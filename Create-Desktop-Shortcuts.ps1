$ErrorActionPreference = 'Stop'
$folder = $PSScriptRoot
$desktop = [Environment]::GetFolderPath('Desktop')
$shell = New-Object -ComObject WScript.Shell
foreach ($item in @(@('StationDesk', 'Start-StationDesk.bat'), @('StationDesk Timeclock', 'Start-Timeclock.bat'))) {
    $shortcut = $shell.CreateShortcut((Join-Path $desktop ($item[0] + '.lnk')))
    if (Test-Path (Join-Path $folder 'StationDesk.exe')) {
        $shortcut.TargetPath = Join-Path $folder 'StationDesk.exe'
        if ($item[0] -eq 'StationDesk Timeclock') {
            $shortcut.Arguments = '--timeclock'
        } else {
            $shortcut.Arguments = ''
        }
    } else {
        $shortcut.TargetPath = Join-Path $folder $item[1]
        $shortcut.Arguments = ''
    }
    $shortcut.WorkingDirectory = $folder
    $shortcut.Description = $item[0]
    $shortcut.IconLocation = (Join-Path $folder 'assets\StationDesk.ico') + ',0'
    $shortcut.Save()
}
Write-Host 'Created StationDesk and StationDesk Timeclock shortcuts on your desktop.'
