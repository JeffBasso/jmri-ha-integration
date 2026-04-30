param(
    [string]$VmName = "haos-jmri-test",
    [string]$VmRoot = "C:\haos-jmri-test",
    [string]$SwitchName = "",
    [long]$MemoryStartupBytes = 4GB,
    [int]$ProcessorCount = 2,
    [string]$HaosVersion = "latest",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Run this script from Windows PowerShell as Administrator."
    }
}

function Assert-HyperV {
    if (-not (Get-Command Get-VM -ErrorAction SilentlyContinue)) {
        throw "Hyper-V PowerShell module was not found. Enable Hyper-V, then rerun this script."
    }
}

function Get-DefaultSwitchName {
    $external = Get-VMSwitch | Where-Object { $_.SwitchType -eq "External" } | Select-Object -First 1
    if ($external) {
        return $external.Name
    }

    $default = Get-VMSwitch -Name "Default Switch" -ErrorAction SilentlyContinue
    if ($default) {
        return $default.Name
    }

    throw "No Hyper-V switch found. Create an External switch in Hyper-V Manager or pass -SwitchName."
}

function Get-HaosRelease {
    param([string]$Version)

    if ($Version -eq "latest") {
        $release = Invoke-RestMethod -Uri "https://api.github.com/repos/home-assistant/operating-system/releases/latest"
    }
    else {
        $release = Invoke-RestMethod -Uri "https://api.github.com/repos/home-assistant/operating-system/releases/tags/$Version"
    }

    $asset = $release.assets |
        Where-Object { $_.name -match "^haos_hyperv-.+\.vhdx\.xz$" } |
        Select-Object -First 1

    if (-not $asset) {
        throw "Could not find a Hyper-V .vhdx.xz asset in release $($release.tag_name)."
    }

    [pscustomobject]@{
        Tag = $release.tag_name
        Name = $asset.name
        Url = $asset.browser_download_url
    }
}

function Expand-XzFile {
    param(
        [string]$Source,
        [string]$Destination
    )

    if (Test-Path $Destination) {
        return
    }

    if (Get-Command xz.exe -ErrorAction SilentlyContinue) {
        & xz.exe -dkf $Source
        $expanded = Join-Path (Split-Path $Destination) ([IO.Path]::GetFileNameWithoutExtension((Split-Path $Source -Leaf)))
        if ($expanded -ne $Destination -and (Test-Path $expanded)) {
            Move-Item -Path $expanded -Destination $Destination -Force
        }
        return
    }

    if (Get-Command 7z.exe -ErrorAction SilentlyContinue) {
        & 7z.exe x $Source "-o$(Split-Path $Destination)" -y | Out-Host
        $expanded = Join-Path (Split-Path $Destination) ([IO.Path]::GetFileNameWithoutExtension((Split-Path $Source -Leaf)))
        if ($expanded -ne $Destination -and (Test-Path $expanded)) {
            Move-Item -Path $expanded -Destination $Destination -Force
        }
        return
    }

    throw "Install xz or 7-Zip, then rerun this script. Could not extract $Source."
}

Assert-Administrator
Assert-HyperV

if ([string]::IsNullOrWhiteSpace($SwitchName)) {
    $SwitchName = Get-DefaultSwitchName
}

$existingVm = Get-VM -Name $VmName -ErrorAction SilentlyContinue
if ($existingVm) {
    if (-not $Force) {
        throw "VM '$VmName' already exists. Pass -Force to stop and remove it."
    }

    if ($existingVm.State -ne "Off") {
        Stop-VM -Name $VmName -TurnOff -Force
    }
    Remove-VM -Name $VmName -Force
}

if ((Test-Path $VmRoot) -and $Force) {
    Remove-Item -Path $VmRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $VmRoot -Force | Out-Null

$release = Get-HaosRelease -Version $HaosVersion
$archivePath = Join-Path $VmRoot $release.Name
$diskPath = Join-Path $VmRoot ([IO.Path]::GetFileNameWithoutExtension($release.Name))

if (-not (Test-Path $archivePath)) {
    Write-Host "Downloading $($release.Name) from $($release.Tag)..."
    Invoke-WebRequest -Uri $release.Url -OutFile $archivePath
}
else {
    Write-Host "Using existing archive $archivePath"
}

Write-Host "Extracting HAOS disk..."
Expand-XzFile -Source $archivePath -Destination $diskPath

Write-Host "Creating Hyper-V VM '$VmName' on switch '$SwitchName'..."
New-VM `
    -Name $VmName `
    -Generation 2 `
    -MemoryStartupBytes $MemoryStartupBytes `
    -VHDPath $diskPath `
    -SwitchName $SwitchName | Out-Null

Set-VMProcessor -VMName $VmName -Count $ProcessorCount
Set-VMFirmware -VMName $VmName -EnableSecureBoot Off
Set-VM -Name $VmName -AutomaticCheckpointsEnabled $false

Start-VM -Name $VmName

Write-Host ""
Write-Host "HAOS VM started."
Write-Host "VM name: $VmName"
Write-Host "Switch:  $SwitchName"
Write-Host "Open:    http://homeassistant.local:8123"
Write-Host ""
Write-Host "If mDNS does not resolve, wait a few minutes and run:"
Write-Host "  Get-VMNetworkAdapter -VMName '$VmName' | Select-Object -ExpandProperty IPAddresses"
