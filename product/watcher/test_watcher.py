import ast
import importlib.util
import io
import json
import plistlib
import re
import shutil
import stat
import subprocess
import tempfile
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
        self.assertEqual(watcher.idle_seconds_from_ioreg("unavailable"), 0)

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
            watcher.print_status(timestamp=timestamp, home=home, loaded=True, output=lines.append)
            output = "\n".join(lines)
            self.assertIn("Agent loaded  yes", output)
            self.assertIn("Inside shift window  yes", output)
            self.assertIn("2026-07-06.jsonl", output)
            self.assertIn("2026-07-07T00:29:30+05:30", output)
            self.assertNotIn("Highly sensitive title", output)
            self.assertNotIn("private.example", output)

    def test_status_handles_no_log(self):
        timestamp = datetime(2026, 7, 12, 22, 0, tzinfo=INDIA)
        with tempfile.TemporaryDirectory() as home:
            lines = []
            watcher.print_status(timestamp=timestamp, home=home, loaded=False, output=lines.append)
            self.assertIn("Agent loaded  no", lines)
            self.assertIn("Inside shift window  no", lines)
            self.assertIn("Last recorded sample  none", lines)

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
            watcher.print_status(timestamp=timestamp, home=home, loaded=False, output=lines.append)
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
        self.assertEqual(plist["StandardErrorPath"], "/dev/null")

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
        self.assertIn('launchctl print "$SERVICE"', install)
        self.assertIn("records remain", uninstall)
        self.assertIn('launchctl print "$SERVICE"', uninstall)
        self.assertIn('rm -f "$WATCHER_PATH"', uninstall)
        self.assertNotIn('rm -rf "$HOME/.shift-tracker"', uninstall)

    @unittest.skipUnless(Path("/usr/bin/plutil").is_file(), "macOS plutil is required")
    def test_plist_path_replacement_commands_work(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "agent.plist"
            shutil.copyfile(DIRECTORY / "com.shifttracker.watcher.plist", path)
            commands = [
                ["/usr/bin/plutil", "-replace", "ProgramArguments.0", "-string", "/usr/bin/python3", str(path)],
                ["/usr/bin/plutil", "-replace", "ProgramArguments.1", "-string", "/tmp/watcher.py", str(path)],
            ]
            for command in commands:
                subprocess.run(command, check=True, capture_output=True)
            with path.open("rb") as plist_file:
                plist = plistlib.load(plist_file)
            self.assertEqual(plist["ProgramArguments"][:2], ["/usr/bin/python3", "/tmp/watcher.py"])

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
