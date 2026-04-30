param(
    [string]$VmName = "haos-jmri-test",
    [string]$VmRoot = "C:\haos-jmri-test",
    [switch]$KeepDisk
)

$ErrorActionPreference = "Stop"

$vm = Get-VM -Name $VmName -ErrorAction SilentlyContinue
if ($vm) {
    if ($vm.State -ne "Off") {
        Stop-VM -Name $VmName -TurnOff -Force
    }
    Remove-VM -Name $VmName -Force
}

if ((Test-Path $VmRoot) -and -not $KeepDisk) {
    Remove-Item -Path $VmRoot -Recurse -Force
}

Write-Host "Removed $VmName"
