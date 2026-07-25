import ast
import importlib.util
import io
import json
import os
import plistlib
import re
import stat
import subprocess
import sys
import tempfile
import time
import tokenize
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


DIRECTORY = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("shift_tracker_watcher", DIRECTORY / "watcher.py")
watcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(watcher)
INDIA = timezone(timedelta(hours=5, minutes=30))


class ShiftWindowTests(unittest.TestCase):
    def test_required_boundaries(self):
        cases = [
            (datetime(2026, 7, 6, 17, 59, tzinfo=INDIA), False),
            (datetime(2026, 7, 6, 18, 0, tzinfo=INDIA), True),
            (datetime(2026, 7, 11, 4, 44, tzinfo=INDIA), True),
            (datetime(2026, 7, 11, 4, 46, tzinfo=INDIA), False),
            (datetime(2026, 7, 12, 22, 0, tzinfo=INDIA), False),
            (datetime(2026, 7, 6, 0, 30, tzinfo=INDIA), False),
        ]
        for timestamp, expected in cases:
            with self.subTest(timestamp=timestamp):
                self.assertEqual(watcher.is_in_shift_window(timestamp), expected)

    def test_exact_end_is_out(self):
        self.assertFalse(watcher.is_in_shift_window(datetime(2026, 7, 11, 4, 45, tzinfo=INDIA)))

    def test_additional_days(self):
        self.assertTrue(watcher.is_in_shift_window(datetime(2026, 7, 10, 23, 59, tzinfo=INDIA)))
        self.assertFalse(watcher.is_in_shift_window(datetime(2026, 7, 11, 18, 0, tzinfo=INDIA)))
        self.assertFalse(watcher.is_in_shift_window(datetime(2026, 7, 7, 12, 0, tzinfo=INDIA)))

    def test_aware_timestamp_is_converted_to_local_time(self):
        utc = timezone.utc
        self.assertTrue(watcher.is_in_shift_window(datetime(2026, 7, 6, 12, 30, tzinfo=utc)))
        self.assertFalse(watcher.is_in_shift_window(datetime(2026, 7, 6, 12, 29, tzinfo=utc)))

    def test_naive_timestamp_is_treated_as_local_time(self):
        self.assertTrue(watcher.is_in_shift_window(datetime(2026, 7, 6, 18, 0)))

    def test_next_shift_start(self):
        monday = datetime(2026, 7, 6, 17, 59, tzinfo=INDIA)
        sunday = datetime(2026, 7, 12, 22, 0, tzinfo=INDIA)
        self.assertEqual(watcher.seconds_until_next_shift(monday), 60)
        self.assertEqual(watcher.seconds_until_next_shift(sunday), 20 * 60 * 60)


class SamplingTests(unittest.TestCase):
    def test_inside_window_appends_one_complete_json_line(self):
        timestamp = datetime(2026, 7, 6, 18, 0, tzinfo=INDIA)
        with tempfile.TemporaryDirectory() as home:
            written = watcher.sample_once(
                timestamp=timestamp,
                home=home,
                activity_reader=lambda: ("Google Chrome", "Planning board"),
                idle_reader=lambda: 181,
                host_reader=lambda application: "Example.COM",
            )
            self.assertTrue(written)
            path = Path(home) / ".shift-tracker" / "log" / "2026-07-06.jsonl"
            content = path.read_text(encoding="utf-8")
            self.assertEqual(content.count("\n"), 1)
            record = json.loads(content)
            self.assertEqual(set(record), watcher.RECORD_FIELDS)
            self.assertEqual(record["timestamp"], "2026-07-06T18:00:00+05:30")
            self.assertEqual(record["application"], "Google Chrome")
            self.assertEqual(record["window_title"], "Planning board")
            self.assertEqual(record["idle_seconds"], 181)
            self.assertTrue(record["idle"])
            self.assertEqual(record["url_host"], "example.com")
            self.assertEqual(stat.S_IMODE(path.parent.parent.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_outside_window_has_no_side_effects_and_returns_false(self):
        timestamp = datetime(2026, 7, 12, 22, 0, tzinfo=INDIA)
        calls = []

        def activity_reader():
            calls.append("activity")
            return "Safari", "Secret title"

        with tempfile.TemporaryDirectory() as home:
            written = watcher.sample_once(
                timestamp=timestamp,
                home=home,
                activity_reader=activity_reader,
                idle_reader=lambda: calls.append("idle") or 0,
                host_reader=lambda application: calls.append("host") or "secret.example",
            )
            self.assertFalse(written)
            self.assertEqual(calls, [])
            self.assertFalse((Path(home) / ".shift-tracker").exists())

    def test_after_midnight_uses_previous_evening_date(self):
        cases = [
            (datetime(2026, 7, 7, 0, 30, tzinfo=INDIA), "2026-07-06.jsonl"),
            (datetime(2026, 7, 11, 4, 44, tzinfo=INDIA), "2026-07-10.jsonl"),
        ]
        for timestamp, filename in cases:
            with self.subTest(timestamp=timestamp), tempfile.TemporaryDirectory() as home:
                watcher.sample_once(
                    timestamp=timestamp,
                    home=home,
                    activity_reader=lambda: ("Notes", "Plan"),
                    idle_reader=lambda: 0,
                )
                expected = Path(home) / ".shift-tracker" / "log" / filename
                self.assertTrue(expected.is_file())

    def test_idle_is_strictly_over_180_seconds(self):
        timestamp = datetime(2026, 7, 6, 18, 0, tzinfo=INDIA)
        with tempfile.TemporaryDirectory() as home:
            watcher.sample_once(
                timestamp=timestamp,
                home=home,
                activity_reader=lambda: ("Notes", "Plan"),
                idle_reader=lambda: 180,
            )
            watcher.sample_once(
                timestamp=timestamp,
                home=home,
                activity_reader=lambda: ("Notes", "Plan"),
                idle_reader=lambda: 180.000001,
            )
            path = Path(home) / ".shift-tracker" / "log" / "2026-07-06.jsonl"
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertFalse(records[0]["idle"])
            self.assertTrue(records[1]["idle"])

    def test_unavailable_idle_sensor_writes_null_and_not_idle(self):
        timestamp = datetime(2026, 7, 6, 18, 0, tzinfo=INDIA)
        with tempfile.TemporaryDirectory() as home:
            watcher.sample_once(
                timestamp=timestamp,
                home=home,
                activity_reader=lambda: ("Notes", "Plan"),
                idle_reader=lambda: None,
            )
            path = Path(home) / ".shift-tracker" / "log" / "2026-07-06.jsonl"
            record = json.loads(path.read_text(encoding="utf-8"))
            self.assertIsNone(record["idle_seconds"])
            self.assertFalse(record["idle"])

    def test_zero_and_unavailable_idle_readings_write_different_records(self):
        timestamp = datetime(2026, 7, 6, 18, 0, tzinfo=INDIA)
        with tempfile.TemporaryDirectory() as home:
            common = {
                "timestamp": timestamp,
                "home": home,
                "activity_reader": lambda: ("Notes", "Plan"),
            }
            watcher.sample_once(idle_reader=lambda: 0, **common)
            watcher.sample_once(idle_reader=lambda: None, **common)
            path = Path(home) / ".shift-tracker" / "log" / "2026-07-06.jsonl"
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(records[0]["idle_seconds"], 0.0)
            self.assertIsNone(records[1]["idle_seconds"])
            self.assertNotEqual(records[0], records[1])

    def test_nonbrowser_never_calls_host_reader(self):
        timestamp = datetime(2026, 7, 6, 18, 0, tzinfo=INDIA)
        with tempfile.TemporaryDirectory() as home:
            watcher.sample_once(
                timestamp=timestamp,
                home=home,
                activity_reader=lambda: ("Notes", "Plan"),
                idle_reader=lambda: 0,
                host_reader=lambda application: self.fail("host reader called"),
            )
            path = Path(home) / ".shift-tracker" / "log" / "2026-07-06.jsonl"
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["url_host"], "")

    def test_once_command_returns_zero_when_no_sample_is_written(self):
        original = watcher.sample_once
        try:
            watcher.sample_once = lambda: False
            self.assertEqual(watcher.main(["once"]), 0)
        finally:
            watcher.sample_once = original

    def test_storage_directory_symlink_is_rejected(self):
        timestamp = datetime(2026, 7, 6, 18, 0, tzinfo=INDIA)
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as outside:
            (Path(home) / ".shift-tracker").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(OSError):
                watcher.sample_once(
                    timestamp=timestamp,
                    home=home,
                    activity_reader=lambda: ("Notes", "Plan"),
                    idle_reader=lambda: 0,
                )
            self.assertEqual(list(Path(outside).iterdir()), [])

    def test_log_file_symlink_is_rejected(self):
        timestamp = datetime(2026, 7, 6, 18, 0, tzinfo=INDIA)
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as outside:
            log_directory = Path(home) / ".shift-tracker" / "log"
            log_directory.mkdir(parents=True)
            outside_file = Path(outside) / "outside.jsonl"
            outside_file.write_text("unchanged\n", encoding="utf-8")
            (log_directory / "2026-07-06.jsonl").symlink_to(outside_file)
            with self.assertRaises(OSError):
                watcher.sample_once(
                    timestamp=timestamp,
                    home=home,
                    activity_reader=lambda: ("Notes", "Plan"),
                    idle_reader=lambda: 0,
                )
            self.assertEqual(outside_file.read_text(encoding="utf-8"), "unchanged\n")


class CollectionTests(unittest.TestCase):
    def test_ioreg_nanoseconds_become_seconds(self):
        output = '    "HIDIdleTime" = 180000000001\n'
        self.assertAlmostEqual(watcher.idle_seconds_from_ioreg(output), 180.000000001)
        self.assertIsNone(watcher.idle_seconds_from_ioreg("unavailable"))
        self.assertIsNone(watcher.idle_seconds_from_ioreg('"HIDIdleTime" = 123 invalid'))

    @unittest.skipUnless(sys.platform == "darwin", "macOS is required")
    def test_real_idle_reading_is_greater_than_zero(self):
        idle_seconds = watcher.read_idle_seconds()
        self.assertIsInstance(idle_seconds, (int, float))
        self.assertGreater(idle_seconds, 0)

    @unittest.skipUnless(sys.platform == "darwin", "macOS is required")
    def test_real_idle_reading_increases(self):
        first = watcher.read_idle_seconds()
        self.assertIsInstance(first, (int, float))
        time.sleep(2)
        second = watcher.read_idle_seconds()
        self.assertIsInstance(second, (int, float))
        self.assertGreater(second, first)

    def test_host_validation_keeps_only_a_host(self):
        self.assertEqual(watcher.normalize_host("EXAMPLE.COM.\n"), "example.com")
        self.assertEqual(watcher.normalize_host("example.com:443"), "example.com")
        self.assertEqual(watcher.normalize_host("2001:db8::1"), "2001:db8::1")
        self.assertEqual(watcher.normalize_host("https://example.com/private?q=secret"), "")
        self.assertEqual(watcher.normalize_host("not a host"), "")

    def test_browser_script_returns_only_a_host(self):
        script = watcher.browser_host_script("Safari", "currentTab")
        self.assertIn("hostOnly(tab.url())", script)
        self.assertNotIn("return tab.url()", script)

    @unittest.skipUnless(Path("/usr/bin/osascript").is_file(), "macOS osascript is required")
    def test_javascript_returns_hosts_for_supported_url_schemes(self):
        cases = {
            "https://person:secret@Example.COM:8443/private?q=value": "example.com",
            "ftp://ftp.example.com/file": "ftp.example.com",
            "chrome://settings/privacy": "settings",
            "about:blank": "",
        }
        for url, expected in cases.items():
            with self.subTest(url=url):
                script = watcher.HOST_ONLY_JAVASCRIPT + "\nhostOnly({});".format(json.dumps(url))
                output = watcher.run_command(["/usr/bin/osascript", "-l", "JavaScript", "-e", script])
                self.assertEqual(output, expected)

    def test_browser_permission_failure_is_empty_for_each_browser(self):
        original = watcher.run_command
        try:
            watcher.run_command = lambda arguments: ""
            for application in ("Safari", "Google Chrome", "Arc", "Brave Browser", "Microsoft Edge"):
                with self.subTest(application=application):
                    self.assertEqual(watcher.read_browser_host(application), "")
        finally:
            watcher.run_command = original

    def test_failed_command_is_empty(self):
        self.assertEqual(watcher.run_command(["/path/that/does/not/exist"]), "")


class StatusTests(unittest.TestCase):
    def test_status_has_requested_values_without_sensitive_fields(self):
        timestamp = datetime(2026, 7, 7, 0, 30, tzinfo=INDIA)
        with tempfile.TemporaryDirectory() as home:
            log_directory = Path(home) / ".shift-tracker" / "log"
            log_directory.mkdir(parents=True)
            record = {
                "timestamp": "2026-07-07T00:29:30+05:30",
                "application": "Safari",
                "window_title": "Highly sensitive title",
                "idle_seconds": 0,
                "idle": False,
                "url_host": "private.example",
            }
            (log_directory / "2026-07-06.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
            lines = []
            watcher.print_status(
                timestamp=timestamp,
                home=home,
                loaded=True,
                output=lines.append,
                idle_reader=lambda: 12.5,
            )
            output = "\n".join(lines)
            self.assertIn("Agent loaded  yes", output)
            self.assertIn("Inside shift window  yes", output)
            self.assertIn("2026-07-06.jsonl", output)
            self.assertIn("2026-07-07T00:29:30+05:30", output)
            self.assertIn("Current idle seconds  12.5", output)
            self.assertNotIn("Highly sensitive title", output)
            self.assertNotIn("private.example", output)

    def test_status_handles_no_log(self):
        timestamp = datetime(2026, 7, 12, 22, 0, tzinfo=INDIA)
        with tempfile.TemporaryDirectory() as home:
            lines = []
            watcher.print_status(
                timestamp=timestamp,
                home=home,
                loaded=False,
                output=lines.append,
                idle_reader=lambda: None,
            )
            self.assertIn("Agent loaded  no", lines)
            self.assertIn("Inside shift window  no", lines)
            self.assertIn("Last recorded sample  none", lines)
            self.assertIn("Idle sensor is unavailable", lines)

    def test_last_sample_skips_a_malformed_trailing_line(self):
        with tempfile.TemporaryDirectory() as home:
            log_directory = Path(home) / ".shift-tracker" / "log"
            log_directory.mkdir(parents=True)
            path = log_directory / "2026-07-06.jsonl"
            path.write_text('{"timestamp":"first"}\nnot json\n', encoding="utf-8")
            self.assertEqual(watcher.last_recorded_sample(home), "first")

    def test_monday_morning_status_uses_monday_path(self):
        timestamp = datetime(2026, 7, 6, 0, 30, tzinfo=INDIA)
        with tempfile.TemporaryDirectory() as home:
            lines = []
            watcher.print_status(
                timestamp=timestamp,
                home=home,
                loaded=False,
                output=lines.append,
                idle_reader=lambda: 0,
            )
            self.assertIn("2026-07-06.jsonl", "\n".join(lines))

    def test_agent_loaded_uses_modern_then_legacy_lookup(self):
        missing = subprocess.CompletedProcess([], 1)
        present = subprocess.CompletedProcess([], 0)
        with mock.patch.object(watcher.subprocess, "run", side_effect=[missing, present]) as run:
            self.assertTrue(watcher.agent_is_loaded())
            self.assertEqual(run.call_count, 2)
        with mock.patch.object(watcher.subprocess, "run", side_effect=[missing, missing]):
            self.assertFalse(watcher.agent_is_loaded())


class SchedulingTests(unittest.TestCase):
    def test_outside_loop_checks_again_within_thirty_seconds(self):
        timestamp = datetime(2026, 7, 6, 17, 0, tzinfo=INDIA)
        with mock.patch.object(watcher, "local_now", return_value=timestamp), mock.patch.object(
            watcher.time, "sleep", side_effect=StopIteration
        ) as sleep:
            with self.assertRaises(StopIteration):
                watcher.run_loop()
            sleep.assert_called_once_with(30.0)

    def test_inside_loop_keeps_thirty_second_cadence(self):
        timestamp = datetime(2026, 7, 6, 18, 0, tzinfo=INDIA)
        with mock.patch.object(watcher, "local_now", return_value=timestamp), mock.patch.object(
            watcher, "sample_once"
        ) as sample, mock.patch.object(watcher.time, "monotonic", side_effect=[10.0, 11.5]), mock.patch.object(
            watcher.time, "sleep", side_effect=StopIteration
        ) as sleep:
            with self.assertRaises(StopIteration):
                watcher.run_loop()
            sample.assert_called_once_with(timestamp)
            sleep.assert_called_once_with(28.5)


class PackagingTests(unittest.TestCase):
    def test_no_network_modules_are_imported(self):
        tree = ast.parse((DIRECTORY / "watcher.py").read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertEqual(
            imported,
            {"datetime", "json", "os", "pathlib", "re", "stat", "subprocess", "sys", "time"},
        )

    def test_plist_is_valid_and_runs_the_loop(self):
        with (DIRECTORY / "com.shifttracker.watcher.plist").open("rb") as plist_file:
            plist = plistlib.load(plist_file)
        self.assertEqual(plist["Label"], watcher.AGENT_LABEL)
        self.assertEqual(plist["ProgramArguments"][2], "run")
        self.assertTrue(plist["RunAtLoad"])
        self.assertTrue(plist["KeepAlive"])
        self.assertEqual(plist["StandardOutPath"], "/dev/null")
        self.assertEqual(plist["StandardErrorPath"], "__ERROR_LOG_PATH__")

    def test_shell_scripts_parse_and_are_executable(self):
        for name in ("install.sh", "uninstall.sh"):
            path = DIRECTORY / name
            result = subprocess.run(["sh", "-n", str(path)], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(path.stat().st_mode & stat.S_IXUSR)

    def test_install_guidance_and_uninstall_retention_are_present(self):
        install = (DIRECTORY / "install.sh").read_text(encoding="utf-8")
        uninstall = (DIRECTORY / "uninstall.sh").read_text(encoding="utf-8")
        self.assertIn("Accessibility", install)
        self.assertIn("Automation", install)
        self.assertIn("osascript", install)
        self.assertIn("never sent anywhere", install)
        self.assertIn('cp "$SOURCE_WATCHER" "$TEMPORARY_WATCHER"', install)
        self.assertIn("service_is_healthy", install)
        self.assertIn("/bin/sleep 5", install)
        self.assertIn('"$LAUNCHCTL_COMMAND" print "$SERVICE"', install)
        self.assertIn("records remain", uninstall)
        self.assertIn('launchctl print "$SERVICE"', uninstall)
        self.assertIn('rm -f "$WATCHER_PATH"', uninstall)
        self.assertNotIn('rm -rf "$HOME/.shift-tracker"', uninstall)

    @unittest.skipUnless(Path("/usr/bin/plutil").is_file(), "macOS plutil is required")
    def test_real_installer_writes_exact_valid_arguments_and_error_log(self):
        with tempfile.TemporaryDirectory() as home:
            result = self.run_isolated_installer(home, "healthy")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            path = Path(home) / "Library" / "LaunchAgents" / "com.shifttracker.watcher.plist"
            with path.open("rb") as plist_file:
                plist = plistlib.load(plist_file)
            arguments = plist["ProgramArguments"]
            self.assertEqual(len(arguments), 3)
            self.assertTrue(all("__" not in argument for argument in arguments))
            self.assertTrue(Path(arguments[0]).is_file())
            self.assertTrue(os.access(arguments[0], os.X_OK))
            self.assertTrue(Path(arguments[1]).is_file())
            self.assertEqual(arguments[2], "run")
            lint = subprocess.run(
                ["/usr/bin/plutil", "-lint", str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(lint.returncode, 0, lint.stdout + lint.stderr)
            error_log = Path(home) / ".shift-tracker" / "watcher.err.log"
            self.assertEqual(plist["StandardErrorPath"], str(error_log))
            self.assertTrue(error_log.is_file())
            if os.environ.get("SHIFT_TRACKER_SHOW_PROOF_OUTPUT") == "1":
                print(result.stdout.strip())
                print("ProgramArguments count  {}".format(len(arguments)))
                for index, argument in enumerate(arguments):
                    print("ProgramArguments {}  {}".format(index, argument))
                print("Placeholder substrings absent  yes")
                print("Interpreter executable file  yes")
                print("Watcher file exists  yes")
                print(lint.stdout.strip())
                print("StandardErrorPath  {}".format(plist["StandardErrorPath"]))
                print("Error log exists  yes")

    def test_installer_fails_plainly_when_agent_does_not_survive(self):
        with tempfile.TemporaryDirectory() as home:
            result = self.run_isolated_installer(home, "failing")
            output = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("installation did not work", output)
            self.assertIn("background agent did not stay healthy", output)
            self.assertIn("watcher.err.log", output)
            self.assertIn("launchctl print", output)
            self.assertNotIn("Shift Tracker is installed and loaded.", output)
            watcher_path = Path(home) / "Library" / "Application Support" / "ShiftTracker" / "watcher.py"
            self.assertFalse(watcher_path.exists())
            if os.environ.get("SHIFT_TRACKER_SHOW_PROOF_OUTPUT") == "1":
                print("Installer exit code  {}".format(result.returncode))
                print("Broken watcher exists  no")
                print(output.strip())

    def test_broken_plist_arguments_exit_nonzero_with_named_usage(self):
        result = subprocess.run(
            [
                sys.executable,
                str(DIRECTORY / "watcher.py"),
                "__PYTHON_PATH__",
                "__WATCHER_PATH__",
                "run",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("watcher.py usage", result.stderr)
        if os.environ.get("SHIFT_TRACKER_SHOW_PROOF_OUTPUT") == "1":
            print("Watcher exit code  {}".format(result.returncode))
            print(result.stderr.strip())

    def run_isolated_installer(self, home, result_name):
        home_path = Path(home)
        self.assertNotEqual(home_path.resolve(), Path.home().resolve())
        marker = home_path / ".shift-tracker-test-home"
        marker.touch()
        launcher = home_path / "fake-launchctl"
        launcher.write_text(
            """#!/bin/sh
set -eu

[ -f "$HOME/.shift-tracker-test-home" ] || exit 99
STATE_PATH=${SHIFT_TRACKER_FAKE_STATE:?}
RESULT_NAME=${SHIFT_TRACKER_FAKE_RESULT:?}

case "$1" in
    bootout|unload|remove)
        if [ -f "$STATE_PATH" ]; then
            rm -f "$STATE_PATH"
            exit 0
        fi
        exit 1
        ;;
    enable)
        exit 0
        ;;
    bootstrap|load)
        if [ "$RESULT_NAME" = "failing" ]; then
            rm -f "$HOME/Library/Application Support/ShiftTracker/watcher.py"
        fi
        : >"$STATE_PATH"
        exit 0
        ;;
    print)
        [ -f "$STATE_PATH" ] || exit 1
        if [ "$RESULT_NAME" = "failing" ]; then
            printf 'gui/501/com.shifttracker.watcher = {\n\tstate = waiting\n\truns = 1\n\tlast exit code = 2\n}\n'
        else
            printf 'gui/501/com.shifttracker.watcher = {\n\tstate = running\n\truns = 1\n\tpid = 4242\n\tlast exit code = (never exited)\n}\n'
        fi
        ;;
    list)
        [ -f "$STATE_PATH" ] || exit 1
        if [ "$RESULT_NAME" = "failing" ]; then
            printf '{\n\t"LastExitStatus" = 2;\n}\n'
        else
            printf '{\n\t"LastExitStatus" = 0;\n\t"PID" = 4242;\n}\n'
        fi
        ;;
    *)
        exit 2
        ;;
esac
""",
            encoding="utf-8",
        )
        launcher.chmod(0o700)
        environment = os.environ.copy()
        environment.update(
            {
                "HOME": str(home_path),
                "PYTHONDONTWRITEBYTECODE": "1",
                "SHIFT_TRACKER_LAUNCHCTL_COMMAND": str(launcher),
                "SHIFT_TRACKER_FAKE_STATE": str(home_path / "fake-launchctl.state"),
                "SHIFT_TRACKER_FAKE_RESULT": result_name,
            }
        )
        return subprocess.run(
            [str(DIRECTORY / "install.sh")],
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )

    def test_documented_command_and_small_footprint(self):
        readme = (DIRECTORY / "README.md").read_text(encoding="utf-8")
        command = "python3 -m unittest discover -s product/watcher -p 'test_*.py'"
        self.assertIn(command, readme)
        expected = {
            "README.md",
            "com.shifttracker.watcher.plist",
            "install.sh",
            "test_watcher.py",
            "uninstall.sh",
            "watcher.py",
        }
        shipped = [path for path in DIRECTORY.rglob("*") if path.is_file() and "__pycache__" not in path.parts]
        self.assertEqual({str(path.relative_to(DIRECTORY)) for path in shipped}, expected)
        self.assertLess(sum(path.stat().st_size for path in shipped), 100_000)

    def test_readme_prose_has_no_forbidden_punctuation(self):
        lines = (DIRECTORY / "README.md").read_text(encoding="utf-8").splitlines()
        prose = []
        in_code_block = False
        for line in lines:
            if line.startswith("```"):
                in_code_block = not in_code_block
            elif not in_code_block:
                prose.append(re.sub(r"`[^`]+`", "", line))
        text = "\n".join(prose)
        for punctuation in ("-", ":", "\N{EM DASH}", "\N{EN DASH}"):
            self.assertNotIn(punctuation, text)

    def test_prose_comments_have_no_forbidden_punctuation(self):
        python_source = (DIRECTORY / "watcher.py").read_text(encoding="utf-8")
        comments = [
            token.string
            for token in tokenize.generate_tokens(io.StringIO(python_source).readline)
            if token.type == tokenize.COMMENT and not token.string.startswith("#!")
        ]
        plist_source = (DIRECTORY / "com.shifttracker.watcher.plist").read_text(encoding="utf-8")
        comments.extend(re.findall(r"<!--(.*?)-->", plist_source, flags=re.DOTALL))
        for comment in comments:
            for punctuation in ("-", ":", "\N{EM DASH}", "\N{EN DASH}"):
                self.assertNotIn(punctuation, comment)


if __name__ == "__main__":
    unittest.main()
