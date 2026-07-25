#!/usr/bin/env python3

import json
import os
import re
import stat
import subprocess
import sys
import time
from datetime import datetime, time as clock_time, timedelta, timezone
from pathlib import Path


AGENT_LABEL = "com.shifttracker.watcher"
SHIFT_START = clock_time(18, 0)
SHIFT_END = clock_time(4, 45)
SAMPLE_INTERVAL_SECONDS = 30
IDLE_LIMIT_SECONDS = 180
LOCAL_TIMEZONE = timezone(timedelta(hours=5, minutes=30))
RECORD_FIELDS = {
    "timestamp",
    "application",
    "window_title",
    "idle_seconds",
    "idle",
    "url_host",
}

BROWSER_TARGETS = {
    "Safari": ("Safari", "currentTab"),
    "Chrome": ("Google Chrome", "activeTab"),
    "Google Chrome": ("Google Chrome", "activeTab"),
    "Arc": ("Arc", "activeTab"),
    "Brave": ("Brave Browser", "activeTab"),
    "Brave Browser": ("Brave Browser", "activeTab"),
    "Edge": ("Microsoft Edge", "activeTab"),
    "Microsoft Edge": ("Microsoft Edge", "activeTab"),
}

FRONTMOST_SCRIPT = r'''
tell application "System Events"
    set frontProcess to first application process whose frontmost is true
    set applicationName to name of frontProcess
    set windowName to ""
    try
        set windowName to name of front window of frontProcess
    end try
    return applicationName & (ASCII character 30) & windowName
end tell
'''

HOST_ONLY_JAVASCRIPT = r'''
function hostOnly(value) {
    var text = String(value || "");
    var match = text.match(/^[a-z][a-z0-9+.-]*:\/\/(?:[^@\/?#]*@)?(\[[^\]]+\]|[^:\/?#]+)(?::[0-9]+)?(?:[\/?#]|$)/i);
    if (!match) {
        return "";
    }
    var host = match[1];
    if (host.charAt(0) === "[" && host.charAt(host.length - 1) === "]") {
        host = host.slice(1, -1);
    }
    return host.toLowerCase().replace(/\.$/, "");
}
'''


def local_now():
    return datetime.now(LOCAL_TIMEZONE)


def as_local_timestamp(timestamp):
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        return timestamp.replace(tzinfo=LOCAL_TIMEZONE)
    return timestamp.astimezone(LOCAL_TIMEZONE)


def is_in_shift_window(timestamp):
    timestamp = as_local_timestamp(timestamp)
    weekday = timestamp.weekday()
    local_time = timestamp.time().replace(tzinfo=None)
    evening = weekday <= 4 and local_time >= SHIFT_START
    morning = 1 <= weekday <= 5 and local_time < SHIFT_END
    return evening or morning


def shift_start_date(timestamp):
    timestamp = as_local_timestamp(timestamp)
    local_time = timestamp.time().replace(tzinfo=None)
    if local_time < SHIFT_END:
        return timestamp.date() - timedelta(days=1)
    return timestamp.date()


def tracker_root(home=None):
    return Path(home) / ".shift-tracker" if home is not None else Path.home() / ".shift-tracker"


def log_path_for_timestamp(timestamp, home=None):
    timestamp = as_local_timestamp(timestamp)
    log_date = shift_start_date(timestamp) if is_in_shift_window(timestamp) else timestamp.date()
    filename = log_date.isoformat() + ".jsonl"
    return tracker_root(home) / "log" / filename


def run_command(arguments, timeout=5):
    try:
        result = subprocess.run(
            arguments,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.rstrip("\r\n")


def read_frontmost_activity():
    output = run_command(["/usr/bin/osascript", "-e", FRONTMOST_SCRIPT])
    if not output:
        return "", ""
    application, separator, window_title = output.partition(chr(30))
    if not separator:
        return application, ""
    return application, window_title


def idle_seconds_from_ioreg(output):
    match = re.search(r'(?m)^[ \t]*"HIDIdleTime"[ \t]*=[ \t]*(\d+)[ \t]*$', output)
    if match is None:
        return None
    return int(match.group(1)) / 1_000_000_000


def read_idle_seconds():
    output = run_command(["/usr/sbin/ioreg", "-r", "-c", "IOHIDSystem", "-d", "1"])
    return idle_seconds_from_ioreg(output)


def browser_host_script(application_name, tab_property):
    target = json.dumps(application_name)
    return HOST_ONLY_JAVASCRIPT + r'''
var result = "";
try {
    var browser = Application(''' + target + r''');
    var tab = browser.windows[0].''' + tab_property + r''';
    result = hostOnly(tab.url());
} catch (error) {
    result = "";
}
result;
'''


def normalize_host(value):
    host = value.strip().lower().rstrip(".")
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]
    if host.count(":") == 1:
        name, port = host.rsplit(":", 1)
        if port.isdigit():
            host = name
        else:
            return ""
    forbidden = "/?#@\\\"'"
    if not host or len(host) > 253:
        return ""
    if any(character.isspace() or character in forbidden for character in host):
        return ""
    if ":" in host and re.fullmatch(r"[0-9a-f:.]+", host) is None:
        return ""
    return host


def read_browser_host(application_name):
    target = BROWSER_TARGETS.get(application_name)
    if target is None:
        return ""
    script = browser_host_script(*target)
    output = run_command(["/usr/bin/osascript", "-l", "JavaScript", "-e", script])
    return normalize_host(output)


def ensure_private_directory(path):
    try:
        information = path.lstat()
    except FileNotFoundError:
        path.mkdir(mode=0o700)
        information = path.lstat()
    if stat.S_ISLNK(information.st_mode) or not stat.S_ISDIR(information.st_mode):
        raise OSError("Tracker storage path is not a directory")
    os.chmod(path, 0o700)


def ensure_log_directory(home=None):
    root = tracker_root(home)
    log_directory = root / "log"
    ensure_private_directory(root)
    ensure_private_directory(log_directory)
    return log_directory


def append_record(path, record):
    payload = (json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    try:
        information = path.lstat()
    except FileNotFoundError:
        information = None
    if information is not None and stat.S_ISLNK(information.st_mode):
        raise OSError("Tracker log path is a symbolic link")
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NONBLOCK
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        information = os.fstat(descriptor)
        if not stat.S_ISREG(information.st_mode) or information.st_nlink != 1:
            raise OSError("Tracker log path is not a private file")
        os.fchmod(descriptor, 0o600)
        offset = 0
        while offset < len(payload):
            offset += os.write(descriptor, payload[offset:])
    finally:
        os.close(descriptor)


def sample_once(
    timestamp=None,
    home=None,
    activity_reader=None,
    idle_reader=None,
    host_reader=None,
):
    timestamp = local_now() if timestamp is None else as_local_timestamp(timestamp)
    if not is_in_shift_window(timestamp):
        return False

    activity_reader = read_frontmost_activity if activity_reader is None else activity_reader
    idle_reader = read_idle_seconds if idle_reader is None else idle_reader
    host_reader = read_browser_host if host_reader is None else host_reader

    application, window_title = activity_reader()
    application = application if isinstance(application, str) else ""
    window_title = window_title if isinstance(window_title, str) else ""
    idle_reading = idle_reader()
    idle_seconds = None if idle_reading is None else max(0.0, float(idle_reading))
    url_host = host_reader(application) if application in BROWSER_TARGETS else ""
    url_host = normalize_host(url_host) if isinstance(url_host, str) else ""

    record = {
        "timestamp": timestamp.isoformat(),
        "application": application,
        "window_title": window_title,
        "idle_seconds": idle_seconds,
        "idle": idle_seconds is not None and idle_seconds > IDLE_LIMIT_SECONDS,
        "url_host": url_host,
    }
    if set(record) != RECORD_FIELDS:
        raise RuntimeError("Invalid record fields")

    log_directory = ensure_log_directory(home)
    path = log_directory / (shift_start_date(timestamp).isoformat() + ".jsonl")
    append_record(path, record)
    return True


def seconds_until_next_shift(timestamp):
    timestamp = as_local_timestamp(timestamp)
    for day_offset in range(8):
        candidate = (timestamp + timedelta(days=day_offset)).replace(
            hour=18,
            minute=0,
            second=0,
            microsecond=0,
        )
        if candidate.weekday() <= 4 and candidate > timestamp:
            return (candidate - timestamp).total_seconds()
    return 3600.0


def run_loop():
    # This persistent loop avoids repeated process starts and sleeps so CPU use stays effectively idle
    while True:
        timestamp = local_now()
        if is_in_shift_window(timestamp):
            started = time.monotonic()
            sample_once(timestamp)
            elapsed = time.monotonic() - started
            time.sleep(max(0.0, SAMPLE_INTERVAL_SECONDS - elapsed))
        else:
            time.sleep(max(1.0, min(seconds_until_next_shift(timestamp), 30.0)))


def agent_is_loaded():
    commands = [
        ["/bin/launchctl", "print", "gui/{}/{}".format(os.getuid(), AGENT_LABEL)],
        ["/bin/launchctl", "list", AGENT_LABEL],
    ]
    for command in commands:
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if result.returncode == 0:
            return True
    return False


def last_recorded_sample(home=None):
    log_directory = tracker_root(home) / "log"
    if not log_directory.is_dir():
        return None
    for path in sorted(log_directory.glob("????-??-??.jsonl"), reverse=True):
        last_timestamp = None
        try:
            with path.open("r", encoding="utf-8", errors="replace") as log_file:
                for line in log_file:
                    try:
                        record = json.loads(line)
                    except (json.JSONDecodeError, TypeError):
                        continue
                    value = record.get("timestamp") if isinstance(record, dict) else None
                    if isinstance(value, str):
                        last_timestamp = value
        except OSError:
            continue
        if last_timestamp is not None:
            return last_timestamp
    return None


def print_status(timestamp=None, home=None, loaded=None, output=print, idle_reader=None):
    timestamp = local_now() if timestamp is None else as_local_timestamp(timestamp)
    loaded = agent_is_loaded() if loaded is None else loaded
    idle_reader = read_idle_seconds if idle_reader is None else idle_reader
    idle_seconds = idle_reader()
    last_sample = last_recorded_sample(home)
    output("Agent loaded  {}".format("yes" if loaded else "no"))
    output("Inside shift window  {}".format("yes" if is_in_shift_window(timestamp) else "no"))
    output("Today's log  {}".format(log_path_for_timestamp(timestamp, home)))
    output("Last recorded sample  {}".format(last_sample if last_sample is not None else "none"))
    if idle_seconds is None:
        output("Idle sensor is unavailable")
    else:
        output("Current idle seconds  {}".format(idle_seconds))


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    command = arguments[0] if arguments else "once"
    if len(arguments) > 1 or command not in {"once", "run", "status"}:
        print("watcher.py usage  watcher.py once or run or status", file=sys.stderr)
        return 2
    if command == "status":
        print_status()
        return 0
    if command == "run":
        run_loop()
        return 0
    sample_once()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
