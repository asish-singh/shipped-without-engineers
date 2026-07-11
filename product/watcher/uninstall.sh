#!/bin/sh

set -eu
umask 077

LABEL="com.shifttracker.watcher"
DESTINATION_PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
PROGRAM_DIRECTORY="$HOME/Library/Application Support/ShiftTracker"
WATCHER_PATH="$PROGRAM_DIRECTORY/watcher.py"
DOMAIN="gui/$(id -u)"
SERVICE="$DOMAIN/$LABEL"

if /bin/launchctl bootout "$SERVICE" >/dev/null 2>&1; then
    true
elif [ -f "$DESTINATION_PLIST" ] && /bin/launchctl bootout "$DOMAIN" "$DESTINATION_PLIST" >/dev/null 2>&1; then
    true
elif [ -f "$DESTINATION_PLIST" ] && /bin/launchctl unload "$DESTINATION_PLIST" >/dev/null 2>&1; then
    true
else
    /bin/launchctl remove "$LABEL" >/dev/null 2>&1 || true
fi

if /bin/launchctl print "$SERVICE" >/dev/null 2>&1 || /bin/launchctl list "$LABEL" >/dev/null 2>&1; then
    printf '%s\n' "Shift Tracker could not be stopped. Its files were kept so you can try again."
    exit 1
fi

rm -f "$DESTINATION_PLIST"
if [ -L "$PROGRAM_DIRECTORY" ]; then
    rm -f "$PROGRAM_DIRECTORY"
else
    rm -f "$WATCHER_PATH"
    rm -f "$PROGRAM_DIRECTORY"/watcher.py.tmp.*
    rmdir "$PROGRAM_DIRECTORY" >/dev/null 2>&1 || true
fi

printf '%s\n' "Shift Tracker is stopped and its LaunchAgent file is removed."
printf '%s\n' "Your records remain in ~/.shift-tracker/log."
printf '%s\n' "macOS privacy choices also remain. You can remove them in Privacy and Security in System Settings."
