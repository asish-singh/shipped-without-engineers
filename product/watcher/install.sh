#!/bin/sh

set -eu
umask 077

SCRIPT_DIRECTORY=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SOURCE_PLIST="$SCRIPT_DIRECTORY/com.shifttracker.watcher.plist"
SOURCE_WATCHER="$SCRIPT_DIRECTORY/watcher.py"
LABEL="com.shifttracker.watcher"
DESTINATION_DIRECTORY="$HOME/Library/LaunchAgents"
DESTINATION_PLIST="$DESTINATION_DIRECTORY/$LABEL.plist"
PROGRAM_DIRECTORY="$HOME/Library/Application Support/ShiftTracker"
WATCHER_PATH="$PROGRAM_DIRECTORY/watcher.py"
DATA_DIRECTORY="$HOME/.shift-tracker"
ERROR_LOG_PATH="$DATA_DIRECTORY/watcher.err.log"
DOMAIN="gui/$(id -u)"
SERVICE="$DOMAIN/$LABEL"
LAUNCHCTL_COMMAND=${SHIFT_TRACKER_LAUNCHCTL_COMMAND:-/bin/launchctl}

service_value() {
    VALUE_NAME=$1
    /usr/bin/awk -v name="$VALUE_NAME" '
        {
            line = $0
            sub(/^[ \t]+/, "", line)
            prefix = name " = "
            if (index(line, prefix) == 1) {
                print substr(line, length(prefix) + 1)
                exit
            }
        }
    '
}

list_value() {
    VALUE_NAME=$1
    /usr/bin/awk -v name="\""${VALUE_NAME}"\"" '
        $1 == name && $2 == "=" {
            gsub(/[;"]/, "", $3)
            print $3
            exit
        }
    '
}

service_is_healthy() {
    if SERVICE_DETAILS=$("$LAUNCHCTL_COMMAND" print "$SERVICE" 2>/dev/null); then
        LAST_EXIT_CODE=$(printf '%s\n' "$SERVICE_DETAILS" | service_value "last exit code")
        case "$LAST_EXIT_CODE" in
            ""|"0"|"(never exited)") ;;
            *) return 1 ;;
        esac
        SERVICE_STATE=$(printf '%s\n' "$SERVICE_DETAILS" | service_value "state")
        SERVICE_PID=$(printf '%s\n' "$SERVICE_DETAILS" | service_value "pid")
        case "$SERVICE_PID" in
            ""|*[!0-9]*) ;;
            *)
                if [ "$SERVICE_STATE" = "running" ] && [ "$SERVICE_PID" -gt 0 ]; then
                    return 0
                fi
                ;;
        esac
        if [ "$SERVICE_STATE" = "waiting" ] && [ "$LAST_EXIT_CODE" = "0" ]; then
            return 0
        fi
        return 1
    fi

    if LIST_DETAILS=$("$LAUNCHCTL_COMMAND" list "$LABEL" 2>/dev/null); then
        LAST_EXIT_CODE=$(printf '%s\n' "$LIST_DETAILS" | list_value "LastExitStatus")
        if [ -n "$LAST_EXIT_CODE" ] && [ "$LAST_EXIT_CODE" != "0" ]; then
            return 1
        fi
        SERVICE_PID=$(printf '%s\n' "$LIST_DETAILS" | list_value "PID")
        case "$SERVICE_PID" in
            ""|*[!0-9]*) ;;
            *)
                if [ "$SERVICE_PID" -gt 0 ]; then
                    return 0
                fi
                ;;
        esac
        if [ "$LAST_EXIT_CODE" = "0" ]; then
            return 0
        fi
    fi
    return 1
}

PYTHON_COMMAND=$(command -v python3 || true)
if [ -z "$PYTHON_COMMAND" ]; then
    printf '%s\n' "Python 3 was not found. Install Python 3 and run this installer again."
    exit 1
fi

if ! "$PYTHON_COMMAND" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)'; then
    printf '%s\n' "Shift Tracker needs Python 3.8 or newer."
    exit 1
fi
case "$PYTHON_COMMAND" in
    /*) PYTHON_PATH="$PYTHON_COMMAND" ;;
    *) PYTHON_PATH=$("$PYTHON_COMMAND" -c 'import os, sys; print(os.path.abspath(sys.executable))') ;;
esac

mkdir -p "$DESTINATION_DIRECTORY"
if [ -L "$PROGRAM_DIRECTORY" ]; then
    printf '%s\n' "The Shift Tracker program folder is a symbolic link. Remove it and run this installer again."
    exit 1
fi
mkdir -p "$PROGRAM_DIRECTORY"
chmod 700 "$PROGRAM_DIRECTORY"
if [ -L "$DATA_DIRECTORY" ]; then
    printf '%s\n' "The Shift Tracker data folder is a symbolic link. Remove it and run this installer again."
    exit 1
fi
mkdir -p "$DATA_DIRECTORY"
chmod 700 "$DATA_DIRECTORY"
if [ -L "$ERROR_LOG_PATH" ] || { [ -e "$ERROR_LOG_PATH" ] && [ ! -f "$ERROR_LOG_PATH" ]; }; then
    printf '%s\n' "The Shift Tracker error log is not a regular file. Move it and run this installer again."
    exit 1
fi
if [ ! -e "$ERROR_LOG_PATH" ]; then
    : >"$ERROR_LOG_PATH"
fi
chmod 600 "$ERROR_LOG_PATH"
TEMPORARY_PLIST="$DESTINATION_PLIST.tmp.$$"
TEMPORARY_WATCHER="$PROGRAM_DIRECTORY/watcher.py.tmp.$$"
trap 'rm -f "$TEMPORARY_PLIST" "$TEMPORARY_WATCHER"' EXIT HUP INT TERM

cp "$SOURCE_PLIST" "$TEMPORARY_PLIST"
cp "$SOURCE_WATCHER" "$TEMPORARY_WATCHER"
chmod 700 "$TEMPORARY_WATCHER"
"$PYTHON_PATH" - "$TEMPORARY_PLIST" "$PYTHON_PATH" "$WATCHER_PATH" "$ERROR_LOG_PATH" <<'PYTHON'
import plistlib
import sys

path, python_path, watcher_path, error_log_path = sys.argv[1:]
with open(path, "rb") as plist_file:
    plist = plistlib.load(plist_file)
plist["ProgramArguments"] = [python_path, watcher_path, "run"]
plist["StandardErrorPath"] = error_log_path
with open(path, "wb") as plist_file:
    plistlib.dump(plist, plist_file)
PYTHON
/usr/bin/plutil -lint "$TEMPORARY_PLIST" >/dev/null
chmod 644 "$TEMPORARY_PLIST"

if "$LAUNCHCTL_COMMAND" bootout "$SERVICE" >/dev/null 2>&1; then
    true
elif "$LAUNCHCTL_COMMAND" bootout "$DOMAIN" "$DESTINATION_PLIST" >/dev/null 2>&1; then
    true
else
    "$LAUNCHCTL_COMMAND" unload "$DESTINATION_PLIST" >/dev/null 2>&1 || true
    "$LAUNCHCTL_COMMAND" remove "$LABEL" >/dev/null 2>&1 || true
fi

if "$LAUNCHCTL_COMMAND" print "$SERVICE" >/dev/null 2>&1 || "$LAUNCHCTL_COMMAND" list "$LABEL" >/dev/null 2>&1; then
    printf '%s\n' "An older Shift Tracker process could not be stopped. Run the uninstaller and try again."
    exit 1
fi

mv "$TEMPORARY_WATCHER" "$WATCHER_PATH"
mv "$TEMPORARY_PLIST" "$DESTINATION_PLIST"
trap - EXIT HUP INT TERM
"$LAUNCHCTL_COMMAND" enable "$SERVICE" >/dev/null 2>&1 || true
if "$LAUNCHCTL_COMMAND" bootstrap "$DOMAIN" "$DESTINATION_PLIST" >/dev/null 2>&1; then
    true
else
    "$LAUNCHCTL_COMMAND" load "$DESTINATION_PLIST"
fi

if ! "$LAUNCHCTL_COMMAND" print "$SERVICE" >/dev/null 2>&1 && ! "$LAUNCHCTL_COMMAND" list "$LABEL" >/dev/null 2>&1; then
    printf '%s\n' "Shift Tracker could not be loaded. Run the installer again after checking the messages above."
    exit 1
fi

/bin/sleep 5
if ! service_is_healthy; then
    printf '%s\n' "Shift Tracker installation did not work because the background agent did not stay healthy." >&2
    printf 'Look for process errors in %s and inspect the service with launchctl print %s.\n' "$ERROR_LOG_PATH" "$SERVICE" >&2
    "$LAUNCHCTL_COMMAND" bootout "$SERVICE" >/dev/null 2>&1 || true
    exit 1
fi

printf '%s\n' "Shift Tracker is installed and loaded."
printf 'Python program  %s\n' "$PYTHON_PATH"
printf '%s\n' "Permission prompts may wait until a sample is collected during shift hours."
printf '%s\n' "macOS may ask for Accessibility access to read the front window title."
printf '%s\n' "Open System Settings, then Privacy and Security, then Accessibility. Allow the Python program or osascript if macOS shows either one."
printf '%s\n' "macOS may also ask for Automation access to ask System Events and supported browsers for activity details."
printf '%s\n' "Open System Settings, then Privacy and Security, then Automation. Allow System Events and the browsers you want recorded for the Python program or osascript shown there."
printf '%s\n' "If access is not granted, sampling continues with some values empty."
printf '%s\n' "All collected details remain in the local log and are never sent anywhere."
