$ErrorActionPreference = 'Stop'
$folder = $PSScriptRoot
$desktop = [Environment]::GetFolderPath('Desktop')
$shell = New-Object -ComObject WScript.Shell
foreach ($item in @(@('StationDesk', 'Start-StationDesk.bat'), @('StationDesk Timeclock', 'Start-Timeclock.bat'))) {
    $shortcut = $shell.CreateShortcut((Join-Path $desktop ($item[0] + '.lnk')))
    $shortcut.TargetPath = Join-Path $folder $item[1]
    $shortcut.WorkingDirectory = $folder
    $shortcut.Description = $item[0]
    $shortcut.Save()
}
Write-Host 'Created StationDesk and StationDesk Timeclock shortcuts on your desktop.'
