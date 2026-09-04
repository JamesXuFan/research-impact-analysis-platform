# Deploying to Azure App Service

Live at: **https://data-platform.azurewebsites.net**

Resource group `comp3888_group`, Linux App Service Plan `data-platform-plan`
(**Premium v4 P2v4**, 4 vCPU / 16 GB — history below), web app `data-platform`, Python 3.12,
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
az appservice plan create --name data-platform-plan --resource-group comp3888_group --sku P2v4 --is-linux
az webapp create --name data-platform --resource-group comp3888_group --plan data-platform-plan --runtime "PYTHON:3.12"

# Streamlit needs WebSockets (off by default). Startup command is the
# literal streamlit invocation, NOT a script filename — see "Why not
# startup.sh" below.
az webapp config set --resource-group comp3888_group --name data-platform --web-sockets-enabled true
az webapp config set --resource-group comp3888_group --name data-platform --startup-file `
    "python -m streamlit run app/Home.py --server.address 0.0.0.0 --server.port 8000 --server.headless true"

# Prevents the ~20-minute idle timeout from forcing a full cold start (re-read
# both parquet files from persistent storage) on whoever visits next — see
# "Why Always On matters" below. Free on Basic tier and above.
az webapp config set --resource-group comp3888_group --name data-platform --always-on true

# Let Oryx install requirements.txt on deploy; tell Streamlit which port to bind;
# point dataset.py at the persistent data location
az webapp config appsettings set --resource-group comp3888_group --name data-platform `
    --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true WEBSITES_PORT=8000 P36_DATA_DIR="/home/data/processed"

# SCM/FTP basic-auth publishing credentials are off by default on new App
# Services — needed for both the publish-profile (GitHub Actions) and the
# Kudu VFS upload below.
az resource update --resource-group comp3888_group --name scm --namespace Microsoft.Web `
    --resource-type basicPublishingCredentialsPolicies --parent sites/data-platform --set properties.allow=true
az resource update --resource-group comp3888_group --name ftp --namespace Microsoft.Web `
    --resource-type basicPublishingCredentialsPolicies --parent sites/data-platform --set properties.allow=true

# Publish profile -> GitHub Actions secret (used by azure/webapps-deploy)
az webapp deployment list-publishing-profiles --resource-group comp3888_group --name data-platform --xml `
    | gh secret set AZURE_WEBAPP_PUBLISH_PROFILE --repo JamesXuFan/COMP3888-Project36
```

### Uploading (or re-uploading) the processed data

Kudu's VFS API accepts arbitrary file sizes over plain HTTP PUT with the
publishing username/password as Basic auth — no size cap the way GitHub has.

```powershell
$creds = az webapp deployment list-publishing-credentials --resource-group comp3888_group --name data-platform `
    --query "{user:publishingUserName, pass:publishingPassword}" -o json | ConvertFrom-Json
$b64 = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes("$($creds.user):$($creds.pass)"))
```

```bash
AUTH="<the base64 string from above>"
curl -X PUT -H "Authorization: Basic $AUTH" \
  "https://data-platform.scm.azurewebsites.net/api/vfs/data/processed/"   # create the dir once

curl -X PUT -H "Authorization: Basic $AUTH" \
  --data-binary @data/processed/publications_deduplicated.parquet \
  "https://data-platform.scm.azurewebsites.net/api/vfs/data/processed/publications_deduplicated.parquet"

curl -X PUT -H "Authorization: Basic $AUTH" \
  --data-binary @data/processed/publications_raw.parquet \
  "https://data-platform.scm.azurewebsites.net/api/vfs/data/processed/publications_raw.parquet"
```

Verify with `curl -H "Authorization: Basic $AUTH" https://data-platform.scm.azurewebsites.net/api/vfs/data/processed/`.

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

**Why not B1.** B1 (1.75 GB RAM) OOM-crashed on startup —
`az monitor metrics list --metric MemoryWorkingSet` showed working set
climbing 131 MB → 785 MB → 1.19 GB and then dropping straight to 0 (the
container being killed and restarted), consistent with loading the ~245 MB
raw and ~208 MB deduplicated parquet files into pandas DataFrames — parquet
files expand substantially in memory, and `st.cache_data` keeps both cached
in the same process. Diagnose the same way if an OOM-style crash recurs:
check `MemoryWorkingSet` for a climb-then-drop-to-zero pattern before
assuming any other cause.

**Why Premium v4, not just a bigger Basic tier.** Went B1 (crashed) → B3
(7 GB, stable, but Basic tier is shared/lower-priority compute) →
**P2v4** (4 vCPU / 16 GB, Premium — dedicated compute, requested when "the
platform feels slow" turned out to be partly a genuine compute-tier
question, not only the cold-start issue below). Note: this subscription's
**PremiumV3 family quota is 0** (`az appservice plan update --sku P1v3`
fails with "Operation cannot be completed without additional quota" /
"Current Limit (PremiumV3 VMs): 0") — PremiumV4 (`P1v4`, `P2v4`, ...) has
quota and works; if scaling ever fails the same way, try the adjacent
family (v4 instead of v3, or vice versa) before requesting a quota increase.

**Why Always On matters as much as the tier.** Independently of compute
tier, App Service idles the app out after ~20 minutes of no traffic by
default, and the next visitor pays a full cold start — re-importing
pandas/statsmodels and re-reading both parquet files from the persistent
`/home` mount (measured ~26s for the 208 MB file alone via the Kudu VFS API,
i.e. over HTTP — the app's own direct read is faster than that but still
slower than local disk). `alwaysOn` was off by default and is now on
(`az webapp config set --always-on true`) — this is what turns "slow every
~20 minutes" into "slow once, right after a deploy or restart, never
otherwise." A faster tier alone does not fix repeated cold starts; the two
fixes are complementary, not substitutes for each other.

## Ongoing deploys

Just `git push` to `main` — the workflow handles the rest. Watch it with:

```bash
gh run watch --repo JamesXuFan/COMP3888-Project36
```

First build after any `requirements.txt` change takes a few minutes (Oryx
compiling pandas/statsmodels/pyarrow wheels). If a deploy succeeds but the
site 500s, check the log stream:

```powershell
az webapp log tail --resource-group comp3888_group --name data-platform
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
- **Cost.** Premium v4 P2v4 is a materially bigger recurring charge than the
  Basic tiers this deployment started on (Basic B3 was already ~US$55/month).
  This was requested ("给我提高挡位") after diagnosing that some of the
  perceived slowness was a genuine compute-tier question, not only the
  cold-start issue Always On fixes. Scale down (`az appservice plan update
  --sku B3` or similar) or delete the resource group when the project no
  longer needs this level of performance running continuously.

  **Verified pricing (Australia East, Linux, via the public Retail Prices
  API, 2026-09-06)** — worth re-checking before scaling further, since this
  account runs on a capped student/free-trial credit that auto-stops
  resources (not billed further) once exhausted, not a card-backed
  pay-as-you-go subscription:

  | SKU | vCPU/RAM (approx.) | $/hour | $/month | Days a US$200 credit lasts |
  | --- | --- | --- | --- | --- |
  | P1v4 | 2 / 8 GB | $0.212 | ~$153 | ~39 |
  | **P2v4 (current)** | 4 / 16 GB | $0.424 | ~$305 | **~20** |
  | P3v4 | 8 / 32 GB | $0.847 | ~$610 | ~10 |
  | P4mv4 | 16 / 128 GB | $2.155 | ~$1,552 | ~3.9 |
  | P5mv4 (ceiling this subscription's quota allows) | 32 / 256 GB | $4.311 | ~$3,104 | ~1.9 |

  Confirmed by briefly scaling all the way to P5mv4 and back — quota allows
  every tier above, this is a budget choice, not a technical ceiling. Stayed
  on P2v4: it already covers this app's actual bottleneck (a one-time,
  I/O-bound cold-start data load, not sustained CPU parallelism — Streamlit
  runs each session largely single-threaded, so 16 or 32 cores go mostly
  unused) and gives the best balance of headroom vs. the credit lasting
  close to a full month, rather than days.

## Custom domain

Once satisfied with `data-platform.azurewebsites.net`, add a custom domain via
`az webapp config hostname add` and provision managed TLS with
`az webapp config ssl create --hostname <your-domain> --resource-group comp3888_group`.
Needs a DNS record added at whichever registrar the domain is with — that
step isn't something the App Service CLI can do on its own.
