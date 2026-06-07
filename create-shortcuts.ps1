$projectRoot = "C:\Users\kukyo\Documents\GOLDdashboard"
$desktop = [Environment]::GetFolderPath("Desktop")
$powershellExe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

$WshShell = New-Object -ComObject WScript.Shell

function New-PSShortcut {
    param(
        [string]$ShortcutName,
        [string]$Arguments,
        [string]$Description
    )

    $shortcutPath = Join-Path $desktop "$ShortcutName.lnk"
    $shortcut = $WshShell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $powershellExe
    $shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$projectRoot\$Arguments`""
    $shortcut.WorkingDirectory = $projectRoot
    $shortcut.Description = $Description
    $shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
    $shortcut.Save()

    Write-Host "作成: $shortcutPath"
}

New-PSShortcut `
    -ShortcutName "GOLDダッシュボード起動" `
    -Arguments "start-local.ps1" `
    -Description "GOLDダッシュボードを起動します"

New-PSShortcut `
    -ShortcutName "GOLDダッシュボード起動（更新あり）" `
    -Arguments "start-local.ps1 -Refresh" `
    -Description "データ更新後にGOLDダッシュボードを起動します"

New-PSShortcut `
    -ShortcutName "GOLDダッシュボード停止" `
    -Arguments "stop-local.ps1" `
    -Description "GOLDダッシュボードを停止します"

Write-Host ""
Write-Host "デスクトップショートカットの作成が完了しました。"