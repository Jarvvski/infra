# infra

Terraform for Adam's personal infrastructure. This repository currently manages Cloudflare DNS for **jarvis.gg** and is meant to grow zone by zone (`cloudflare/<zone>/`, and later a `modules/` directory when a pattern is shared).

Mail (the Google Workspace MX records) stays as imported. The website points at GitHub Pages for `jarvvski.github.io`: apex `A`/`AAAA` records, `www` as a CNAME, and the Pages domain-verification TXT record. Those addresses were checked against the [GitHub Pages custom-domain docs](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site) on 2026-10-23. Every Pages record is DNS-only (`proxied = false`) with automatic TTL (`1`).

| | |
| --- | --- |
| Zone | `jarvis.gg` |
| Zone id | `25a69e647ecf731fb8268a02b55e8afa` |
| Plan / status | Free, active (not managed here) |
| Provider | `cloudflare/cloudflare` **5.28.1** |
| Terraform | `>= 1.6.3` (CI uses 1.17.0). 1.6.3 is the first release with `skip_s3_checksum`, which R2 requires. The configuration is OpenTofu-compatible HCL (`import` blocks and the S3 backend). |
| State | Cloudflare R2 bucket `jarvvski-tfstate`, key `cloudflare/jarvis-gg/terraform.tfstate` |

Zone id and DNS record ids are public identifiers and are committed in `cloudflare/jarvis-gg/imports.tf`. The Cloudflare account id is not committed.

## Layout

```text
cloudflare/jarvis-gg/    root module for jarvis.gg DNS
scripts/                 live-record listing and plan checks
.github/workflows/       plan on pull requests, manual apply on main
```

NS records at the zone apex are Cloudflare nameservers. They are intentionally unmanaged.

## One-time bootstrap

Do these once, before the first `terraform init` against the remote backend. This repo does not create the bucket or the tokens.

1. **Create the R2 bucket.** In the Cloudflare dashboard open R2 and create a bucket named `jarvvski-tfstate`. Leave it private: no custom domain and no `r2.dev` public access. Default jurisdiction is correct unless you specifically choose EU or FedRAMP. R2 has no object versioning; do not delete the state object.

2. **Create an R2 API token.** R2 → Manage R2 API Tokens → Create API token. Permission: Object Read & Write. Scope it to `jarvvski-tfstate` only. Store the Access Key ID and Secret Access Key (shown once).

3. **Create a Cloudflare API token scoped to this zone.** My Profile → API Tokens → Create Custom Token.
   - Permission: Zone → DNS → Edit (Edit includes read).
   - Zone resources: Include → Specific zone → `jarvis.gg`.
   - No account-level permissions and no other zones.

4. **Find the account id** on the dashboard overview (the right-hand sidebar). You will put it only in the R2 endpoint below. Keep it out of git.

5. **Local backend config.** From `cloudflare/jarvis-gg`:

   ```bash
   cp backend.hcl.example backend.hcl
   ```

   Edit `backend.hcl` so `endpoints.s3` is the real endpoint. `backend.hcl` is gitignored.

   ```hcl
   endpoints = {
     s3 = "https://<ACCOUNT_ID>.r2.cloudflarestorage.com"
   }
   ```

   EU jurisdiction uses `https://<ACCOUNT_ID>.eu.r2.cloudflarestorage.com`. FedRAMP uses `https://<ACCOUNT_ID>.fedramp.r2.cloudflarestorage.com`.

6. **GitHub Actions secrets.** Repo → Settings → Secrets and variables → Actions → Repository secrets. Create these four names exactly:

   | Secret | Value |
   | --- | --- |
   | `CLOUDFLARE_API_TOKEN` | Token from step 3 |
   | `R2_ACCESS_KEY_ID` | R2 access key id from step 2 |
   | `R2_SECRET_ACCESS_KEY` | R2 secret access key from step 2 |
   | `R2_ENDPOINT` | `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` (same host as `backend.hcl`) |

   Pull-request plans skip themselves when any of these are missing. Apply fails until all four exist.

7. **GitHub environment gate.** Settings → Environments → New environment. Name it `production` (the apply workflow references that name). Enable required reviewers and add yourself. Do this before the first apply run. This repository's workflows do not change repo settings, so the environment stays unprotected until you add the reviewer.

## Plan and apply locally

```bash
export CLOUDFLARE_API_TOKEN="<zone DNS token>"
export AWS_ACCESS_KEY_ID="<R2 access key id>"
export AWS_SECRET_ACCESS_KEY="<R2 secret access key>"

cd cloudflare/jarvis-gg
terraform init -input=false -backend-config=backend.hcl
terraform plan -input=false
```

`CLOUDFLARE_API_TOKEN` is the provider credential. The `AWS_*` variables are the R2 S3 credentials. Terraform reads both from the environment; they are not written into `.tf` files.

Check the live zone any time (this prints ids, priorities, TTLs, and proxied flags, and compares them to the committed config):

```bash
export CLOUDFLARE_API_TOKEN="<zone DNS token>"
./scripts/list-dns-import-blocks.sh
```

Equivalent raw request:

```bash
curl -sS \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  "https://api.cloudflare.com/client/v4/zones/25a69e647ecf731fb8268a02b55e8afa/dns_records?per_page=100" \
  | jq '.result[] | {id,type,name,content,priority,ttl,proxied,comment}'
```

Apply the import pull request before this GitHub Pages change. That first apply, against the import configuration, must be:

```text
Plan: 6 to import, 0 to add, 0 to change, 0 to destroy.
```

It only writes Terraform state, including the old apex `A` record `46.101.80.89`. Then merge and apply this change. With that record in state, the plan must be:

```text
Plan: 10 to add, 0 to change, 1 to destroy.
```

Destroy is only `cloudflare_dns_record.apex` (`A` `jarvis.gg` `46.101.80.89`). The ten adds are four GitHub Pages `A` records, four `AAAA` records, the `www` CNAME, and the `_github-pages-challenge-jarvvski` TXT record. MX records stay unchanged. After that apply, later plans must say `No changes`.

If the import has not been applied, this configuration cannot see `46.101.80.89` and will leave it in Cloudflare next to the new Pages addresses. Do not apply in that case.

Apply once you have read that plan:

```bash
terraform apply -input=false
```

Prefer the GitHub apply workflow below for the real apply so there is a review gate. State locking is off: the S3 lockfile argument needs Terraform 1.10, and this stack stays on `>= 1.6.3` for R2 (`skip_s3_checksum`). Do not run a local apply while the GitHub apply workflow is running.

MX `import` blocks stay in the configuration. Terraform skips them once those addresses are in state. If the state object is lost, the next plan imports the same MX ids again. The old apex `A` record is not imported anymore; Terraform destroys it only when it is already in state.

## GitHub Actions

**Plan** (`.github/workflows/terraform-plan.yml`) runs on every pull request:

- `terraform fmt -check -recursive`
- `terraform init -backend=false` and `terraform validate`
- `tflint`
- `terraform plan`, then a pull-request comment, only when `CLOUDFLARE_API_TOKEN`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, and `R2_ENDPOINT` are all set. Otherwise the plan step logs a skip and the job stays green. A successful plan, including `10 to add, 0 to change, 1 to destroy`, does not fail the job. The plan comment is still posted. `terraform plan` errors still fail the job. The import-only gate (`scripts/assert-import-only-plan.py`) runs only when the repository variable `TF_PLAN_IMPORT_ONLY` is `true`. Leave that variable unset for this cutover.

The workflow trigger is `pull_request`. It must stay that way. `pull_request_target` would run with this repository's secrets, including on fork pull requests. Fork pull requests do not receive the four Actions secrets, and the plan step is skipped for them.

**Apply** (`.github/workflows/terraform-apply.yml`) runs only from `workflow_dispatch` on `main`. It never runs on push or on a pull request. The `plan` job prints the plan. The `apply` job is bound to the `production` environment, so it waits for the required reviewer. Read the plan job log, then approve only when it is `10 to add, 0 to change, 1 to destroy` or `No changes`. Do not approve a plan that creates the Pages records without destroying `46.101.80.89`.

## DNS records

| Type | Name | Content | Priority | TTL | Proxied |
| --- | --- | --- | --- | --- | --- |
| A | jarvis.gg | 185.199.108.153 | | 1 (automatic) | false |
| A | jarvis.gg | 185.199.109.153 | | 1 (automatic) | false |
| A | jarvis.gg | 185.199.110.153 | | 1 (automatic) | false |
| A | jarvis.gg | 185.199.111.153 | | 1 (automatic) | false |
| AAAA | jarvis.gg | 2606:50c0:8000::153 | | 1 (automatic) | false |
| AAAA | jarvis.gg | 2606:50c0:8001::153 | | 1 (automatic) | false |
| AAAA | jarvis.gg | 2606:50c0:8002::153 | | 1 (automatic) | false |
| AAAA | jarvis.gg | 2606:50c0:8003::153 | | 1 (automatic) | false |
| CNAME | www.jarvis.gg | jarvvski.github.io | | 1 (automatic) | false |
| TXT | _github-pages-challenge-jarvvski.jarvis.gg | 8246776e59edf2bb27a58013c4317d | | 1 (automatic) | false |
| MX | jarvis.gg | aspmx.l.google.com | 1 | 1 | false |
| MX | jarvis.gg | alt1.aspmx.l.google.com | 5 | 1 | false |
| MX | jarvis.gg | alt2.aspmx.l.google.com | 5 | 1 | false |
| MX | jarvis.gg | aspmx2.googlemail.com | 10 | 1 | false |
| MX | jarvis.gg | aspmx3.googlemail.com | 10 | 1 | false |

After the Pages apply, verify the domain at <https://github.com/settings/pages_verified_domains/jarvis.gg>. Then in the `jarvvski.github.io` repository open Settings → Pages, set the custom domain to `jarvis.gg`, and turn on Enforce HTTPS. GitHub can take up to 24 hours before Enforce HTTPS is available.

`comment` is null on every record, so the configuration leaves it unset. MX records use `content` and `priority`, which is the shape the DNS API returns for these rows (no `data` object).

If a plan still wants to change a field this configuration leaves unset, read that field from the curl output above and set the same value. `private_routing`, `settings`, and `tags` were absent or empty in the captured records. Do not apply a plan that would write a different value.

## Optional pre-commit

```bash
pre-commit install
```

The hook runs `terraform fmt -check` and `terraform validate` with `-backend=false`. It does not call Cloudflare.
