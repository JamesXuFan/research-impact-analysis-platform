# Deploying to Azure App Service

Live at: **https://comp3888.azurewebsites.net**

Resource group `comp3888_group`, Linux App Service Plan `comp3888-linux-plan`
(**Basic B3** — see "Why B3, not B1" below), web app `comp3888`, Python 3.12,
Australia East. Deploys automatically via GitHub Actions on every push to
`main` (`.github/workflows/azure-deploy.yml`).

## Architecture: code and data deploy separately

The processed dataset (`data/processed/*.parquet`, ~444 MB) is **not** in this
git repo — it's licensed Scopus/QS data, excluded via `.gitignore`, and both
files individually exceed GitHub's 100 MB per-file push limit anyway. Neither
is it rebuilt during CI (that needs the raw `.xlsx` exports, also excluded and
also not something CI has access to).

Instead:
- **Code** (`app/`, `src/`, `requirements.txt`, `.streamlit/`) deploys via
  GitHub Actions on every push — see the workflow file.
- **Data** was uploaded *once*, directly, to the App Service's persistent
  storage at `/home/data/processed/` (outside the deployed code package, so a
  code-only redeploy never touches it). `src/p36/dataset.py` reads from
  `$P36_DATA_DIR` (an App Service setting, `/home/data/processed`) instead of
  the local `data/processed/` it defaults to for local dev.

If the underlying data changes, re-run the upload step below — pushing new
code does not.

## One-time setup (already done for this deployment — kept here for reference)

```powershell
# Resource group, Linux plan, web app
az group create --name comp3888_group --location australiaeast
az appservice plan create --name comp3888-linux-plan --resource-group comp3888_group --sku B3 --is-linux
az webapp create --name comp3888 --resource-group comp3888_group --plan comp3888-linux-plan --runtime "PYTHON:3.12"

# Streamlit needs WebSockets (off by default). Startup command is the
# literal streamlit invocation, NOT a script filename — see "Why not
# startup.sh" below.
az webapp config set --resource-group comp3888_group --name comp3888 --web-sockets-enabled true
az webapp config set --resource-group comp3888_group --name comp3888 --startup-file `
    "python -m streamlit run app/Home.py --server.address 0.0.0.0 --server.port 8000 --server.headless true"

# Let Oryx install requirements.txt on deploy; tell Streamlit which port to bind;
# point dataset.py at the persistent data location
az webapp config appsettings set --resource-group comp3888_group --name comp3888 `
    --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true WEBSITES_PORT=8000 P36_DATA_DIR="/home/data/processed"

# SCM/FTP basic-auth publishing credentials are off by default on new App
# Services — needed for both the publish-profile (GitHub Actions) and the
# Kudu VFS upload below.
az resource update --resource-group comp3888_group --name scm --namespace Microsoft.Web `
    --resource-type basicPublishingCredentialsPolicies --parent sites/comp3888 --set properties.allow=true
az resource update --resource-group comp3888_group --name ftp --namespace Microsoft.Web `
    --resource-type basicPublishingCredentialsPolicies --parent sites/comp3888 --set properties.allow=true

# Publish profile -> GitHub Actions secret (used by azure/webapps-deploy)
az webapp deployment list-publishing-profiles --resource-group comp3888_group --name comp3888 --xml `
    | gh secret set AZURE_WEBAPP_PUBLISH_PROFILE --repo JamesXuFan/COMP3888-Project36
```

### Uploading (or re-uploading) the processed data

Kudu's VFS API accepts arbitrary file sizes over plain HTTP PUT with the
publishing username/password as Basic auth — no size cap the way GitHub has.

```powershell
$creds = az webapp deployment list-publishing-credentials --resource-group comp3888_group --name comp3888 `
    --query "{user:publishingUserName, pass:publishingPassword}" -o json | ConvertFrom-Json
$b64 = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes("$($creds.user):$($creds.pass)"))
```

```bash
AUTH="<the base64 string from above>"
curl -X PUT -H "Authorization: Basic $AUTH" \
  "https://comp3888.scm.azurewebsites.net/api/vfs/data/processed/"   # create the dir once

curl -X PUT -H "Authorization: Basic $AUTH" \
  --data-binary @data/processed/publications_deduplicated.parquet \
  "https://comp3888.scm.azurewebsites.net/api/vfs/data/processed/publications_deduplicated.parquet"

curl -X PUT -H "Authorization: Basic $AUTH" \
  --data-binary @data/processed/publications_raw.parquet \
  "https://comp3888.scm.azurewebsites.net/api/vfs/data/processed/publications_raw.parquet"
```

Verify with `curl -H "Authorization: Basic $AUTH" https://comp3888.scm.azurewebsites.net/api/vfs/data/processed/`.

## Two problems hit during the first deploy — kept here so they don't recur

**Why not `startup.sh`.** The first attempt used a checked-in `startup.sh`
script and `--startup-file "startup.sh"`. The container crash-looped —
`exit code 127` ("command not found") after ~40s, then a 2-minute
Azure-imposed cooldown before each retry (visible in `az webapp log tail` as
repeated `ContainerStartupFailure` / `Site is blocked due to multiple,
consecutive cold start failures`). App Service does not reliably resolve a
bare relative filename against the working directory/PATH for a Python
custom startup command. Fix: set the **literal command** as the startup
command instead of a script filename (see the `az webapp config set
--startup-file "python -m streamlit run ..."` line above) — no file lookup
involved, so nothing to get wrong.

**Why B3, not B1.** B1 (1.75 GB RAM) OOM-crashed on startup —
`az monitor metrics list --metric MemoryWorkingSet` showed working set
climbing 131 MB → 785 MB → 1.19 GB and then dropping straight to 0 (the
container being killed and restarted), consistent with loading the ~245 MB
raw and ~208 MB deduplicated parquet files into pandas DataFrames — parquet
files expand substantially in memory, and `st.cache_data` keeps both cached
in the same process. B3 (7 GB) has comfortable headroom; if cost matters
more than headroom, B2 (3.5 GB) is worth trying first, but B1 is not enough
for this dataset. Diagnose the same way if this recurs: check
`MemoryWorkingSet` for a climb-then-drop-to-zero pattern before assuming any
other cause.

## Ongoing deploys

Just `git push` to `main` — the workflow handles the rest. Watch it with:

```bash
gh run watch --repo JamesXuFan/COMP3888-Project36
```

First build after any `requirements.txt` change takes a few minutes (Oryx
compiling pandas/statsmodels/pyarrow wheels). If a deploy succeeds but the
site 500s, check the log stream:

```powershell
az webapp log tail --resource-group comp3888_group --name comp3888
```

— most first-deploy failures are either the WebSockets setting, the
`P36_DATA_DIR` value, or the persistent upload above not having run yet.

## Public access and cost — decisions that are still yours

- **Public access.** This is a real, reachable URL serving individual-
  publication bibliometric data. If it should be restricted to your
  team/client rather than open to anyone with the link, turn on **App Service
  Authentication** (Settings → Authentication in the Portal, or
  `az webapp auth microsoft update`) — easier to set now than to retrofit
  after the link has circulated.
- **Cost.** Basic B3 is a real recurring charge (~US$55/month at time of
  writing — check current pricing; B2 is roughly half that, B1 about a
  quarter, but see "Why B3, not B1" above for why B1 doesn't actually work
  here), not a one-off. Scale down (`az appservice plan update --sku ...`) or
  delete the resource group when the project no longer needs the app running.

## Custom domain

Once satisfied with `comp3888.azurewebsites.net`, add a custom domain via
`az webapp config hostname add` and provision managed TLS with
`az webapp config ssl create --hostname <your-domain> --resource-group comp3888_group`.
Needs a DNS record added at whichever registrar the domain is with — that
step isn't something the App Service CLI can do on its own.
