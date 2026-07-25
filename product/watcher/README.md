# Shift Tracker

Shift Tracker quietly records foreground activity during the defined evening and early morning shift hours. It takes one sample every thirty seconds while the shift is active. It records nothing outside those hours.

Each sample contains the local time, the foreground application name, idle seconds when the sensor is available, and whether idle time is over three minutes. A null idle reading means the sensor was unavailable, so activity is unknown. It does not mean the user was active.

Window titles are rarely available because macOS usually exposes them only for applications in the visible desktop space. Nothing should depend on a window title being present. For Safari, Chrome, Arc, Brave, and Edge each sample also records only the host of the active tab. It does not keep the rest of the web address.

## Privacy

Everything collected stays on this Mac. Shift Tracker has no network feature and never sends the records anywhere.

Records live in `~/.shift-tracker/log`. Each shift has one file named for the evening when that shift began. A sample after midnight is kept in the file for the previous evening. The folder is private to your macOS account. Log files remain until you choose to remove them.

Window titles and browser hosts can be sensitive. The status command never displays them.

## Install

Open Terminal in `product/watcher` and run this command.

```sh
./install.sh
```

The installer starts a small background process. It sleeps between checks and uses no processor time while sleeping.

macOS may ask for Accessibility access so Shift Tracker can read the front window title. Open System Settings, then Privacy and Security, then Accessibility. Allow the Python program or osascript if macOS lists either one.

macOS may also ask for Automation access so Shift Tracker can ask System Events and supported browsers for activity details. Open System Settings, then Privacy and Security, then Automation. Allow System Events and the browsers you want recorded for the Python program or osascript shown there. These prompts might appear only when the first sample is collected during shift hours. If access is not granted, sampling continues and the protected values stay empty.

## Status

Open Terminal in `product/watcher` and run this command.

```sh
./watcher.py status
```

The result says whether the background agent is loaded, whether the shift window is active now, where the current log belongs, when the latest sample was recorded, and the current idle seconds. It says plainly when the idle sensor is unavailable.

## Uninstall

Open Terminal in `product/watcher` and run this command.

```sh
./uninstall.sh
```

Uninstalling stops the watcher and removes its LaunchAgent file. It keeps `~/.shift-tracker` and every collected record.

## Tests

From the repository root run this single command.

```sh
python3 -m unittest discover -s product/watcher -p 'test_*.py'
```

The tests use only Python 3 and install no packages.
