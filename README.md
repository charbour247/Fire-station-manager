# StationDesk

A Windows desktop application for a fire department. The interface uses Times New Roman, vertical navigation, navy panels, and red actions. PStrax and Vector Solutions are design references only; there is no connection to either service.

![StationDesk fire-service emblem](assets/StationDesk.png)

StationDesk uses a red-and-gold fire-service cross with a central flame on the login screen, in navigation, and as its Windows application icon. The multi-size Windows icon and transparent PNG are in `assets`. Keep this folder beside the source files. Compiled Windows builds include the assets inside the EXE. Run `Create-Desktop-Shortcuts.ps1` from the extracted source folder or compiled release folder to apply the emblem to both desktop shortcuts; existing shortcuts with these names are updated.

## Run on Windows

1. Install Python 3.11 or newer from python.org with the Python launcher and Tcl/Tk support (the normal installer includes these).
2. Extract this entire folder to a permanent location.
3. Double-click `Start-StationDesk.bat`.
4. On first launch, create your administrator account. There are no default passwords or invented personnel records.
5. In Personnel, create member accounts. In Schedule, assign Duty, Fundraiser, or Meeting shifts.

Run `Start-Timeclock.bat` for an independent timeclock window. It requires member login and records hours in the same database as the full application. Right-click either launcher and choose **Send to > Desktop (create shortcut)**. Alternatively run `Create-Desktop-Shortcuts.ps1` in PowerShell if your policy permits local scripts. Keep the extracted folder in place after creating shortcuts.

## Features

- Member dashboard: all-time duty, training, and special-event hours, active status, and next five assignments.
- Training: completion dates, 0–24 hours per record, categories, copied document attachments, search, and open attachments. Use zero hours for reference materials.
- Timeclock: Duty, Fundraiser, and Meeting clock-ins, clock-out, and the last 25 entries. Active sessions survive application restarts. Only one activity may run per member.
- Schedule: administrators assign members and remove assignments; overlapping assignments are rejected. Overnight shifts are supported by entering the following date as the end.
- Personnel: visible only to administrators. Create accounts, select an existing member and click **Edit selected member** (or double-click their row), and export all-time department hour totals to CSV. Editing supports full name, username, Member/Administrator role, and an optional password reset. Leave the password field blank to keep the existing password; new passwords require at least 10 characters. Hours, training documents, and assignments stay linked to the member. The last administrator cannot be demoted. Changes to account details and roles appear when an open app window next navigates; personnel actions recheck current administrator permissions before proceeding.
- Passwords are salted and hashed with PBKDF2-SHA256, 300,000 iterations.

## Data and operating scope

This version is a **single-computer local application**, suitable for a shared station computer. All app windows launched under the same Windows account share `%LOCALAPPDATA%\StationDesk\stationdesk.db` and its `documents` folder. Different Windows accounts or computers have separate data. Scheduling uses the computer's local time; punches are stored in UTC and displayed in local time. Keep the station computer clock correct.

Close all app windows before copying the entire `%LOCALAPPDATA%\StationDesk` folder for backup. Back up the database and documents together. Restore by closing the app and replacing that folder. Document files are stored with unique internal names; their original names appear in the UI.

This initial version does not include central server synchronization, integration with PStrax/Vector, password recovery, training approvals, payroll rules, or an immutable audit log. Authentication controls access within the application; anyone with direct access to the local database can change it. Use a protected Windows account for the station computer. Administrators cannot view members' passwords.

## Optional standalone executable

On Windows, run `Build-Windows-EXE.bat`. It downloads PyInstaller and builds `dist\StationDesk.exe`, which no longer requires Python on the destination computer. Create a shortcut to the EXE with `--timeclock` in its arguments for timeclock-only mode. A compiled Windows EXE is not included: this delivery was built in Linux.

## Verification

Run `py -3 -m unittest discover -s tests -v`. Automated checks cover authentication, persisted data, timeclock transitions and duplicate prevention, activity totals, training validation and attachment copying, and schedule overlap checks. Python compilation and data-layer tests were run in Linux; Windows launchers, desktop shortcuts, and visual rendering require verification on Windows.

## Download a Windows EXE from GitHub

Open this repository's **Actions** tab, select a successful **Test and build Windows application** run, and download **StationDesk-Windows** from its Artifacts section (GitHub sign-in is required). Extract the ZIP and run `StationDesk.exe`. The workflow builds on pushes to main and can be run manually. For independent timeclock mode, create a Windows shortcut to the EXE and add ` --timeclock` after the quoted executable path in the shortcut Target. The source-code batch launchers require Python; the built EXE does not.
