# HAOS Testing

Use a real Home Assistant OS VM to test the JMRI app/add-on install flow,
Supervisor lifecycle, ingress, logs, persistence, and exposed ports.

## Create The VM

Run Windows PowerShell as Administrator from the repo root:

```powershell
.\scripts\haos\create-hyperv-vm.ps1
```

The script creates a Hyper-V VM named `haos-jmri-test`, downloads the latest
official HAOS Hyper-V disk, attaches it, disables Secure Boot, and starts the VM.

Open Home Assistant after the VM finishes booting:

```text
http://homeassistant.local:8123
```

If that name does not resolve, find the VM address:

```powershell
Get-VMNetworkAdapter -VMName haos-jmri-test | Select-Object -ExpandProperty IPAddresses
```

Then open `http://<ip-address>:8123`.

## Install This App Repository

In Home Assistant:

1. Go to **Settings -> Add-ons -> Add-on Store**.
2. Open the three-dot menu.
3. Choose **Repositories**.
4. Add:

```text
https://github.com/JeffBasso/jmri-ha-integration
```

Install **JMRI Model Railroad** from the repository.

## Development Loop

When changing the app:

1. Bump `version` in `app/jmri/config.yaml`.
2. Commit and push the repo.
3. In HAOS, reload the add-on/app repository.
4. Rebuild/update the JMRI app.
5. Start it and check logs, ingress, persistence, and ports.

## Remove The VM

Run Windows PowerShell as Administrator:

```powershell
.\scripts\haos\remove-hyperv-vm.ps1
```

To remove the VM but keep the downloaded disk files:

```powershell
.\scripts\haos\remove-hyperv-vm.ps1 -KeepDisk
```
