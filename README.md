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
- Schedule: an apparatus-based roster board with Day, Week, and Month views, color-coded shift groups, named personnel cards, staffing targets, filters, drag-and-drop changes, and recurring assignments. Administrators see and manage the station schedule; members see their own assignments in a read-only view. Existing databases and assignments are upgraded automatically.
- Personnel: visible only to administrators. Create accounts, select an existing member and click **Edit selected member** (or double-click their row), and export all-time department hour totals to CSV. Editing supports full name, username, Member/Administrator role, and an optional password reset. Leave the password field blank to keep the existing password; new passwords require at least 10 characters. Hours, training documents, and assignments stay linked to the member. The last administrator cannot be demoted. Changes to account details and roles appear when an open app window next navigates; personnel actions recheck current administrator permissions before proceeding.
- Passwords are salted and hashed with PBKDF2-SHA256, 300,000 iterations.

## Using the scheduling board

The board uses roster and staffing workflows inspired by [Vector Scheduling](https://www.vectorsolutions.com/solutions/vector-scheduling/fire-ems/), with StationDesk branding and Times New Roman typography. This is an independent local application with no connection to Vector's service.

1. Open **Schedule**, then **Apparatus / staffing**. Type a new apparatus name or select an existing vehicle. Set its minimum on-duty crew, or enter 0 for no staffing target.
2. Choose **Day**, **Week**, or **Month**. Use Previous/Next, Today, or a YYYY-MM-DD date to navigate. The Day and Week boards show apparatus as rows, dates as columns, and personnel as assignment cards. The Month view places cards in calendar days. Both axes scroll when the roster is larger than the window.
3. Double-click an empty cell to create an assignment for that date and apparatus, or click **+ Assignment**. Choose the member, activity, apparatus, optional A/B/C/D shift group, crew position, start/end, and location. Enter the following date for overnight shifts.
4. For a rotation, set **Repeat every N days** and **Total occurrences** (maximum 52). For example, a 24-hour shift every 3 days is entered as next-day start/end dates, interval 3, and the desired count. No department rotation is assumed. If any occurrence conflicts with the member's existing assignments, none of the new occurrences are saved.
5. Drag a card to another apparatus row or date to move that occurrence while retaining its member, start time, duration, group, and position. In Month view, dragging changes its date and keeps its apparatus. Dropping an overnight carryover card shifts the whole assignment by the number of days dragged. Conflicts are rejected. Select a card for full details; double-click it or choose **Edit selected** to edit. Edits and removal affect only that occurrence.
6. Filter by apparatus, shift group, or activity, or search member names, titles, positions, apparatus, and locations. Group colors A/B/C/D are red/blue/green/purple; ungrouped cards use their activity color.

Coverage figures on the administrator roster count distinct members with active **Duty** assignments at the displayed **Coverage at** time on each day. Enter a 24-hour HH:MM time and click Apply. Red counts are below the configured minimum. Counts use all duty groups and ignore display filters, so filtering the board does not change the staffing calculation. This is a point-in-time staffing indicator; it does not certify full-shift coverage or validate firefighter qualifications. Member views show only their own active duty assignments and do not report department-wide coverage.

## Data and operating scope

This version is a **single-computer local application**, suitable for a shared station computer. All app windows launched under the same Windows account share `%LOCALAPPDATA%\StationDesk\stationdesk.db` and its `documents` folder. Different Windows accounts or computers have separate data. Scheduling uses the computer's local time; punches are stored in UTC and displayed in local time. Keep the station computer clock correct.

Close all app windows before copying the entire `%LOCALAPPDATA%\StationDesk` folder for backup. Back up the database and documents together. Restore by closing the app and replacing that folder. Document files are stored with unique internal names; their original names appear in the UI.

This initial version does not include central server synchronization, integration with PStrax/Vector, password recovery, training approvals, payroll rules, or an immutable audit log. Authentication controls access within the application; anyone with direct access to the local database can change it. Use a protected Windows account for the station computer. Administrators cannot view members' passwords.

## Optional standalone executable

On Windows, run `Build-Windows-EXE.bat`. It downloads PyInstaller and builds `dist\StationDesk.exe`, which no longer requires Python on the destination computer. Create a shortcut to the EXE with `--timeclock` in its arguments for timeclock-only mode. A compiled Windows EXE is not included: this delivery was built in Linux.

## Verification

Run `py -3 -m unittest discover -s tests -v`. Automated checks cover authentication, persisted data, timeclock transitions and duplicate prevention, activity totals, training validation and attachment copying, and schedule overlap checks. Python compilation, data-layer tests, and a rendered GUI smoke test were run in Linux. The Windows workflow also runs `python tests/gui_smoke.py` before packaging. Windows launchers, desktop shortcuts, and final Windows rendering still require verification on Windows.

## Download a Windows EXE from GitHub

Open this repository's **Actions** tab, select a successful **Test and build Windows application** run, and download **StationDesk-Windows** from its Artifacts section (GitHub sign-in is required). Extract the ZIP and run `StationDesk.exe`. The workflow builds on pushes to main and can be run manually. For independent timeclock mode, create a Windows shortcut to the EXE and add ` --timeclock` after the quoted executable path in the shortcut Target. The source-code batch launchers require Python; the built EXE does not.
