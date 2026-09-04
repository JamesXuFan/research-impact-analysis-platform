# Deploying to Azure App Service

Target: this Streamlit app on Azure App Service (Linux, Python runtime), reachable
at `https://<your-app-name>.azurewebsites.net` (or a custom domain pointed at it).

## Before you run anything — three decisions that are yours to make, not mine

1. **Public access.** This app reads Scopus/QS bibliometric data
   (`data/processed/*.parquet`) at the individual-publication level. Deploying it
   to a public URL means anyone with the link can see that data. If it should stay
   restricted to your team/client, turn on **App Service Authentication** (Settings
   → Authentication in the Portal, or `az webapp auth microsoft update`) *before*
   you announce the URL to anyone — it's much easier to lock down at deploy time
   than to retrofit after the link has already circulated.
2. **Pricing tier.** The app + its dependencies (pandas, statsmodels, pyarrow,
   scipy) + `data/processed/` (444 MB) add up to a footprint the **Free (F1)**
   tier's 1 GB quota and CPU-minute caps will not comfortably hold, and F1 apps
   idle out between requests. Use at least **Basic B1** (~US$13/month at time of
   writing — check current pricing) below; this is a real recurring cost, not a
   one-off.
3. **Python version.** Local development here runs Python 3.14; Azure App
   Service's Linux Python runtime may not yet offer 3.14 as a stack. The commands
   below target `PYTHON:3.12` (broadly available and compatible with everything
   in `requirements.txt`) — confirm current availability with
   `az webapp list-runtimes --os linux` and adjust if needed.

## What you need first

- An Azure subscription, and the **Azure CLI** installed locally
  (`winget install Microsoft.AzureCLI` on Windows, or see
  [learn.microsoft.com/cli/azure/install-azure-cli](https://learn.microsoft.com/cli/azure/install-azure-cli)).
- `az login` — run this yourself in an interactive terminal; it opens a browser
  for you to authenticate. This step can't be scripted or done on your behalf.

## 1. Log in and pick names

```powershell
az login

$RG       = "p36-platform-rg"          # resource group — pick any name
$LOCATION = "australiaeast"            # closest Azure region to Sydney
$PLAN     = "p36-platform-plan"
$APPNAME  = "p36-platform"             # must be globally unique across Azure — you will likely need to change this
```

## 2. Create the resource group, plan, and web app

```powershell
az group create --name $RG --location $LOCATION

az appservice plan create `
    --name $PLAN --resource-group $RG `
    --sku B1 --is-linux

az webapp create `
    --name $APPNAME --resource-group $RG --plan $PLAN `
    --runtime "PYTHON:3.12"
```

## 3. Required App Service settings

```powershell
# Streamlit needs WebSockets — off by default on App Service.
az webapp config set --resource-group $RG --name $APPNAME --web-sockets-enabled true

# Use the startup.sh already in this repo.
az webapp config set --resource-group $RG --name $APPNAME --startup-file "startup.sh"

# Let Oryx install requirements.txt during deploy.
az webapp config appsettings set --resource-group $RG --name $APPNAME `
    --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true WEBSITES_PORT=8000
```

## 4. Build a deploy package that excludes the raw source exports

The app only reads `data/processed/*.parquet` at runtime (see
`src/p36/dataset.py`) — it never touches the 8 raw QS/Scopus export `.xlsx`
files directly under `data/`. Those are the most sensitive files in this repo
(individually named per university, clearly identifiable as licensed exports)
and add ~326 MB for no runtime benefit, so they're deliberately left out of the
deploy package below rather than shipped and hoped-nobody-notices.

```powershell
# Run from the repo root.
$zip = "deploy.zip"
if (Test-Path $zip) { Remove-Item $zip }

Compress-Archive -Path app, src, requirements.txt, startup.sh, .streamlit, `
    data\processed, data\dictionary `
    -DestinationPath $zip
```

## 5. Deploy the zip

```powershell
az webapp deployment source config-zip `
    --resource-group $RG --name $APPNAME --src $zip
```

This triggers an Oryx build (installing `requirements.txt` — pandas, statsmodels,
pyarrow, etc. have compiled wheels, so first build can take several minutes) and
then starts `startup.sh`.

## 6. Verify

```powershell
az webapp browse --resource-group $RG --name $APPNAME
```

If it doesn't come up, check the log stream first — most first-deploy failures
are either a missing WebSockets setting (step 3) or an Oryx build failure
visible right there:

```powershell
az webapp log tail --resource-group $RG --name $APPNAME
```

## Updating after a code change

Re-run steps 4 and 5 (rebuild the zip, redeploy) — steps 1-3 only need doing once.

## Custom domain ("我的网站" instead of `*.azurewebsites.net`)

Once the app is live on its default hostname, add your domain via
`az webapp config hostname add` and provision a managed TLS certificate with
`az webapp config ssl create --hostname <your-domain> --resource-group $RG`.
This needs a DNS record (CNAME or A, per Azure's instructions) added at your
domain registrar — that step is on whichever registrar/DNS provider your
domain is with, not something the App Service CLI can do for you.
