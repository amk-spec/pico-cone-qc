# Password-protected Render preview

Status: prepared for the user's Render account; **not yet deployed or provider-validated**. This remains a development prototype with synthetic data. It is not an approved production QC system or engineering authority.

## Open it without installing anything

1. Sign in or create an account at <https://dashboard.render.com/> and connect GitHub access to `amk-spec/pico-cone-qc`.
2. Choose **New → Blueprint**, select that repository and select branch **`codex/lander-hosted-preview`**. Use the repository's `render.yaml`.
3. When prompted for **`LANDER_PREVIEW_OWNER_PASSWORD`**, choose a unique password of at least 16 characters. Enter it only in Render's secure environment-variable field, not in chat or Git. Render generates `DJANGO_SECRET_KEY` automatically; the database connection is linked automatically.
4. Review Render's displayed resource charges before creating anything. The proposed blueprint uses a Starter web service, Basic 256 MB PostgreSQL and a 1 GB persistent disk. These are paid-resource selections; no free hosting or price guarantee is claimed. No paid resources were created by the agent. Do not switch to an ephemeral filesystem while expecting uploaded evidence to persist.
5. After deployment is **Live**, use **View site** on the web service. Render supplies the actual HTTPS address. Sign in as **`owner`** using the password you entered. Start with **Work orders → DEMO-WO-104 → a Lander serial**.

You do not need to install Python, PostgreSQL or the ZIP. No public URL can be supplied until the hosting account creates the service. Render's GitHub/organization authorization and billing confirmation must be completed by the account owner; the current cloud task has no connected hosting identity/API credential.

If the hosting UI labels/options change, select the Blueprint flow for this branch and inspect the detected resources/environment inputs. The YAML's syntax/references are checked locally; only Render can validate/provision the current provider resource plans, runtime availability, region, quota and account access.

## What becomes accessible

- HTTPS login and public static styles; all QC pages, uploads/downloads, decisions and authority views require a valid named program account.
- Synthetic work orders, serials, coupons, draft records and holds. Actual engineering source PDFs/XLSX, previous local uploads/databases/passwords and historical trial data are **not** deployed.
- Source metadata/status remains visible, but the original files are deliberately not imported by hosted seeding. No missing criteria become approved values.
- The preview username `owner` is a fictional demonstration account with explicit owner capacity, not an actual company appointment. Delegation examples remain explicitly synthetic, not actual customer authority.

The hostname is taken from Render's runtime `RENDER_EXTERNAL_HOSTNAME`; no wildcard host acceptance is used. For a later custom hostname, explicitly configure `DJANGO_ALLOWED_HOSTS` and appropriate `DJANGO_CSRF_ORIGINS` after setting up its HTTPS routing.

## Optional role-based review accounts

Only the `owner` password is required initially. The other synthetic accounts receive unknown random passwords unless you set their specific secret variables in Render:

| Username | Optional secure environment variable |
| --- | --- |
| `cone` | `LANDER_PREVIEW_CONE_PASSWORD` |
| `picogrid` | `LANDER_PREVIEW_PICOGRID_PASSWORD` |
| `operator` | `LANDER_PREVIEW_OPERATOR_PASSWORD` |
| `delegate` | `LANDER_PREVIEW_DELEGATE_PASSWORD` |
| `viewer` | `LANDER_PREVIEW_VIEWER_PASSWORD` |

Each configured password must be unique and at least 16 characters. Restart/deploy the service after changing these settings; startup synchronizes configured account passwords without resetting work records. No credential listing is written into the hosted filesystem or application logs. Keep passwords in the hosting service's secure settings or a password manager. Do not publish them as repository files or screenshots.

## Runtime controls and persistence

- `LANDER_HOSTED_PREVIEW=1` fails closed without a strong external Django key, an explicit hostname and PostgreSQL `DATABASE_URL`. Hosted mode refuses SQLite and forces debug off.
- Gunicorn serves the application; WhiteNoise serves build-generated hashed static assets. Django's development server is not used on Render.
- Render terminates HTTPS at its ingress. The application uses the trusted ingress `X-Forwarded-Proto` signal, redirects HTTP, and sets secure session/CSRF cookies. The app port should remain behind that managed ingress.
- Login protection is enabled through Django Axes: five unsuccessful attempts lock the relevant username or immediate client IP for 15 minutes. This is preview-level protection, not a full SSO/MFA/abuse-management deployment. Render ingress may share a peer IP; an administrator can reset lockouts in the service console using `python manage.py axes_reset`.
- HSTS is limited to one hour for the preview hostname, with no include-subdomains/preload commitment. The deployment check reports these two optional advisories; we deliberately do not assert a permanent policy over subdomains we do not control.
- PostgreSQL keeps relational records. `/var/data/lander/evidence` keeps uploaded private files on the attached disk. Static assets live in the built application image. Persistence is not a tested backup/restore policy; do not use real production evidence here.
- The public `/health/` endpoint checks database connectivity and returns only health/prototype status. It exposes no QC records, passwords or database identity.
- Automatic redeployment is disabled in the blueprint. Review later code/environment changes and deploy explicitly. Seeding is idempotent and does not reset existing review records.

This deployment preparation improves Internet-preview safeguards; it does not complete engineering TBDs, formal qualification, original-source migration, offline paper reconciliation, customer UAT or production recovery/retention/access controls. See [prototype scope](../prototype/README.md) and [gap register](../design/gap-analysis.md).

## Checks performed before handoff

- Existing PostgreSQL prototype suite: 57 tests passed after hosted additions.
- Hosted security suite: 11 tests passed, covering HTTPS redirects, named login/secure cookies, lockout, CSRF, rejected hosts, private pages/downloads, health, required password, secret-free/source-free seeding and password rotation without data reset.
- `scripts/render-build`: dependency installation and compressed hashed static manifest passed.
- `scripts/render-start`: exercised locally against an isolated temporary PostgreSQL database with fresh synthetic data. Gunicorn startup, migrations/seeding, health, HTTPS redirect, password login, private workspace and CSS asset serving passed; no original attachments seeded and no password logged. The temporary service/database were removed afterward.
- Blueprint YAML syntax, service/database references, secure-input declarations and persistent disk checked. Current Render provider schema, billing, account permission, deployed HTTPS and live URL remain unverified until actual creation.

A hosted-mode test harness is provided at `scripts/test_hosted.py`; it needs PostgreSQL test-database permissions and builds the required static assets before testing. Never run the hosted startup against an existing real QC database: this preview is for synthetic development review only.
