# Prototype validation record

Validation performed November 2, 2026 (America/Los_Angeles). These are software-development results on synthetic data, not welding qualification, engineering approval, an operational acceptance test or hardware release.

## Executed checks

| Check | Observed result | Practical scope / limit |
| --- | --- | --- |
| PostgreSQL migrations and `manage.py check` | Passed on PostgreSQL 17.11 with Python 3.12.14 / Django 5.2.18 | Both application migrations applied; no Django system-check errors |
| `scripts/test --verbosity 1` | **57 tests passed, 0 failed, 0 skipped** on PostgreSQL | Includes real concurrent approvals using separate connections, core state decisions, authority/delegation/self-approval, immutable records, failures/holds/NCRs, pending/owner release, late evidence impact, private access and CSRF |
| `QC_USE_SQLITE=1 scripts/test --verbosity 1` | **56 passed, 1 skipped, 0 failed** | PostgreSQL row-lock concurrency case intentionally skipped because SQLite lacks the required row-lock semantics |
| `scripts/setup`, run after initial installation | Passed, existing data/accounts retained | Pinned installed dependencies checked; no pending migrations; seed idempotence preserves existing records/credentials |
| `manage.py makemigrations --check --dry-run` | Passed — no changes detected | Models and committed migrations agree |
| Chromium desktop browser | Passed | Login, 10 register/navigation routes, actual work-order create POST with CSRF, and denial of TBD approval even in owner capacity |
| Chromium mobile browser at 390 px | Passed | Login, overview and navigation rendered; no document-level horizontal overflow. Data tables intentionally have horizontal scroll containers |
| Browser console/runtime | No script errors observed | This server-rendered prototype has no frontend build or external JavaScript dependencies |
| Screenshots | Captured and visually inspected | [Desktop overview](screenshots/overview.png), [mobile overview](screenshots/overview-mobile.png). Synthetic role/record labels only |
| `git diff --check` | Passed | Whitespace consistency only; custom documentation links/table/ID checks separately used for the design review |
| `manage.py check --deploy` | Four expected unresolved development transport warnings | HSTS, SSL redirect, secure session cookie and secure CSRF cookie settings are not configured for a production TLS endpoint. No public/production deployment is claimed |

The first PostgreSQL test run found a nullable-outer-join row-locking error in revision approval. Locking was narrowed to the decision row and ordered through the prototype decision lock; the full PostgreSQL suite was rerun and passed. Subsequent checks added failed-inspection containment, hardware-impact authority, coupon context matching and a real two-reviewer concurrency scenario.

## Representative tested invariants

- Membership, a superuser flag or read access does not independently confer engineering approval authority. Explicit personal owner capacity is distinct from recorded Picogrid delegation.
- Self-approval is allowed only for authorized action/scope, can be restricted by organizational policy, and compares actual performer rather than the helper entering data. Earlier approvals retain their policy version.
- TBD criteria cannot be approved as accepted evidence, even using owner capacity. Owner release actions retain outstanding requirements and cannot change a test fact into PASS or impersonate a Picogrid signer.
- Separate A/B welds do not count as separate physical coupons. Destructive tests require pre-cut evidence; invalid test versus valid failed weld are distinct. Failed valid coupon evidence creates containment/H/NCR rather than pending-results eligibility.
- Holds have origin-dependent returns. A passing H check alone cannot close unresolved corrective action; failed-coupon holds require B/C evidence. Process closure leaves NCR/hardware disposition separate.
- Unique machine and scoped qualification/continuity evidence are checked. Missing/old activity is not current continuity; another machine of the same model does not inherit qualification.
- Ordinary normal release needs defined accepted evidence; pending coupon release requires explicit scoped customer authorization; known failures cannot use that route. A hold on another serial does not block an unrelated serial unless its machine/scope applies.
- Evidence amendment/impact preserves original records, release and actual shipment history, while blocking further affected ordinary decisions. Hardware-impact clearance cannot rely on only Cone process authority.
- Two concurrent approvals of one revision produce one approval and one stale/frozen rejection, not two conflicting approvals.

## Not established by these results

The 71 workflow inventory entries and 38 verification groups remain the full design targets, **not claimed completed coverage**. See the [run guide's deliberate limits](README.md) for unimplemented or deferred controls. We have not executed real customer UAT, certified inspection methods/qualification plans, a full accessibility/security audit, a full outage reconciliation exercise, a production identity deployment, protected-audit recovery or a backup/restore rehearsal.

No raw historical workbook observation has been converted into qualified settings or an approved acceptance criterion. Original source documents retain their reviewed identity/status. The app is intentionally a development prototype and must not be used as a production gate until the remaining engineering/operational decisions and acceptance work are completed.

## Portable review follow-up

The portable `try_prototype.py` launcher was prepared and exercised on its own SQLite data directory, with real Chromium login and workspace verification on a separate port. PostgreSQL and forced-SQLite data, keys, uploads and credential files are isolated. Both database test modes were rerun after this separation change. The ZIP contains source, the local launcher and instructions; it excludes all current databases, generated credentials, uploaded original engineering documents and virtual environments. Windows/macOS launcher branches have not been executed on those operating systems in this Linux workspace.

## Hosted-preview preparation

Prepared `render.yaml`, Gunicorn/WhiteNoise and hosted-only HTTPS/cookie/host/login-throttling settings. Existing PostgreSQL tests remain 57 passing; 11 separate hosted tests passed after building static assets. The exact build/start commands were exercised on isolated synthetic PostgreSQL data; no original source attachments/plaintext credentials were exported. The [hosting guide](../preview/README.md) records the details and two intentional HSTS subdomain/preload advisories. No Render service or live HTTPS URL has been created or validated; account authorization/billing remains external.
