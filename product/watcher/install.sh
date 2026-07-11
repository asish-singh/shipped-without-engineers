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
DOMAIN="gui/$(id -u)"
SERVICE="$DOMAIN/$LABEL"

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
TEMPORARY_PLIST="$DESTINATION_PLIST.tmp.$$"
TEMPORARY_WATCHER="$PROGRAM_DIRECTORY/watcher.py.tmp.$$"
trap 'rm -f "$TEMPORARY_PLIST" "$TEMPORARY_WATCHER"' EXIT HUP INT TERM

cp "$SOURCE_PLIST" "$TEMPORARY_PLIST"
cp "$SOURCE_WATCHER" "$TEMPORARY_WATCHER"
chmod 700 "$TEMPORARY_WATCHER"
/usr/bin/plutil -replace ProgramArguments.0 -string "$PYTHON_PATH" "$TEMPORARY_PLIST"
/usr/bin/plutil -replace ProgramArguments.1 -string "$WATCHER_PATH" "$TEMPORARY_PLIST"
/usr/bin/plutil -lint "$TEMPORARY_PLIST" >/dev/null
chmod 644 "$TEMPORARY_PLIST"

if /bin/launchctl bootout "$SERVICE" >/dev/null 2>&1; then
    true
elif /bin/launchctl bootout "$DOMAIN" "$DESTINATION_PLIST" >/dev/null 2>&1; then
    true
else
    /bin/launchctl unload "$DESTINATION_PLIST" >/dev/null 2>&1 || true
    /bin/launchctl remove "$LABEL" >/dev/null 2>&1 || true
fi

if /bin/launchctl print "$SERVICE" >/dev/null 2>&1 || /bin/launchctl list "$LABEL" >/dev/null 2>&1; then
    printf '%s\n' "An older Shift Tracker process could not be stopped. Run the uninstaller and try again."
    exit 1
fi

mv "$TEMPORARY_WATCHER" "$WATCHER_PATH"
mv "$TEMPORARY_PLIST" "$DESTINATION_PLIST"
trap - EXIT HUP INT TERM
/bin/launchctl enable "$SERVICE" >/dev/null 2>&1 || true
if /bin/launchctl bootstrap "$DOMAIN" "$DESTINATION_PLIST" >/dev/null 2>&1; then
    true
else
    /bin/launchctl load "$DESTINATION_PLIST"
fi

if ! /bin/launchctl print "$SERVICE" >/dev/null 2>&1 && ! /bin/launchctl list "$LABEL" >/dev/null 2>&1; then
    printf '%s\n' "Shift Tracker could not be loaded. Run the installer again after checking the messages above."
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
