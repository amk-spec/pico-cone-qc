# Development prototype — running and review guide

The user approved the revised architecture and authorized a development prototype. This Django/PostgreSQL application is a reviewable first implementation, **not an operational QC system, production qualification or release authority**. Rev C remains the locked software baseline, and all three source documents retain their discussion-draft status. Engineering TBDs are preserved; the application does not supply missing limits, coupon frequency, idle threshold or proof-test setup.

## Password-protected hosted preview

Render preparation is available in the [hosted preview guide](../preview/README.md). It adds a production-style application server, hashed static assets, HTTPS/cookie settings and login throttling, and excludes original attachments/local credentials from hosted seeding. The service is not yet created; hosting account authorization/billing and live validation remain outstanding. This is still a prototype, not production qualification.

## Try on your own computer

The portable review copy includes `try_prototype.py` and `TRY-ME.txt`. Extract it, install Python 3.12+ if needed, and run `py -3 try_prototype.py` on Windows or `python3 try_prototype.py` on Mac/Linux from the extracted folder. The launcher installs pinned dependencies, creates separate synthetic SQLite data, shows generated local login details and opens the browser. First run requires Internet access. Keep the terminal open; Ctrl+C stops the app. No PostgreSQL installation is needed for this review mode. Its data, uploads, secret key and credentials stay under `.local/sqlite-review`, separate from any PostgreSQL review instance.

The packaged copy excludes all existing databases, credentials, uploads and original source attachments. Its synthetic records remain prototype-only. This chat's cloud runtime does not supply a shareable browser-preview tool; the local address inside that runtime is not a link to a service on the user's computer.

## Run the prepared workspace

From `/workspace/pico-cone-qc`:

```bash
scripts/setup
scripts/dev
```

The development server binds to loopback port 8000 by default. The server uses Django's development static-file handler; this is not a production deployment. `LANDER_BIND` can explicitly select a different development bind address when the environment provides an appropriate preview mechanism. No public deployment has been created.

Local demonstration usernames/passwords are generated once by `manage.py seed_demo` and stored in ignored `.local/demo-accounts.txt` (mode 0600). Read that file locally to sign in. Credentials are synthetic and must not be reused outside this development instance. Re-running setup preserves existing data, passwords and user edits.

| Username | Demonstration role |
| --- | --- |
| `owner` | Explicit personal owner capacity; broad visibility, separately attributed owner actions |
| `cone` | Cone senior approver with action-scoped grants and own organizational policy management |
| `picogrid` | Picogrid senior approver for procedure/disposition/conditional-shipment examples |
| `operator` | Actual worker/data-entry account, without engineering-approval grants |
| `delegate` | AM Kreations account with **synthetic example** Picogrid delegation grants, selected through Picogrid capacity |
| `viewer` | Shared program read access; no write or approval grant |

These are fictional role examples, not actual appointments of the user, Jake, Cone owners or Picogrid personnel. Creating a role does not create a technical qualification or formal customer delegation.

## Database and reproducibility

The prepared cloud instance uses PostgreSQL 17 through a private Unix socket under `.local/pgsocket`, with a rootless server installed under `/workspace/.tools/postgres`. The local configuration points to this database in ignored `.local/database-url`; `.local/postgres-bin` identifies its binaries. `scripts/local-db` restarts that retained local server when needed. The socket directory has mode 0700 and local authentication relies on this development machine's OS user; this is not an external production database authentication design. No global PostgreSQL installation or system files were changed.

On a new workstation, use Python 3.12+ and provide PostgreSQL through `DATABASE_URL` before running setup:

```bash
export DATABASE_URL='postgresql://user:password@host:5432/lander'
scripts/setup
scripts/dev
```

Enter real connection secrets through the environment, not a tracked file. PostgreSQL test execution requires permission to create/drop the isolated Django test database. PostgreSQL binaries were downloaded using Debian's signed package index and verified package hashes; TLS/package verification was not disabled. Python dependencies are pinned in `requirements.txt`.

For an explicitly lightweight local review without PostgreSQL:

```bash
QC_USE_SQLITE=1 scripts/setup
QC_USE_SQLITE=1 scripts/dev
```

SQLite is a fallback, not the approved operational database design. Its concurrency semantics do not validate PostgreSQL locking. The current primary validation used real PostgreSQL. Existing SQLite and PostgreSQL databases are separate; changing the adapter does not migrate local records between them.

## Review walkthrough

1. Sign in as `owner` or `cone`. The overview links real database counts, work orders, serials, records and attributable history. All seed records are clearly marked `DEMO` and are synthetic examples.
2. Open `DEMO-WO-104`, then an individual Lander serial. Each serial has its own operations, inspection references, holds/NCRs, impact cases, release assessment and shipment history. Grouping in a work order does not confer shared acceptance.
3. Open the WPS or verification plan. Its unresolved criteria block acceptance even in owner capacity. A record can be returned for correction or amended; a frozen approved revision is not overwritten. Original source documents are downloadable privately from their source records when provided during seeding.
4. Open `DEMO-CV-014`. A physical assembly contains separate A/B welds, actual passes and extracted specimens. Record pre-cut inspection before creating/testing specimens. Test validity, actual result, Cone acceptance and subsequent qualification remain separate.
5. Open `DEMO-H-003`. Record investigation/corrective action and H-required strike-plate results. Closing a hold requires passing checks, confirmed resolution and approved verification; a failed-coupon hold also requires applicable B/C evidence. Gate 2-origin closure returns to Gate 2; other origins return to Gate 1. Linked hardware NCRs remain independent.
6. Review `DEMO-NCR-001` as Cone and Picogrid. Cone can propose/collaborate; recorded customer authority is required for disposition. Authorized execution and accepted verification precede closeout. A process hold is not automatically an NCR.
7. In Authority & access, compare shared read access with action/organization/scope grants. Self-approval starts allowed only for authorized approvers; a senior can restrict its organization's policy, without rewriting historical approvals. Owner and Picogrid-delegate capacities are explicit.
8. Flag a record as incorrect or amend approved evidence. Dependency review identifies affected units, pauses ordinary affected approvals/releases/shipments and preserves historical releases/shipments. Hardware-impact clearance cannot be performed with only Cone process authority. The app does not invent recall or disposition instructions.
9. Inspect a serial's Gate 2 checklist. Normal release requires defined approved context, scoped current qualification, matching coupon evidence, final inspections and plan-defined proof applicability. Pending-coupon authorization is separate from continuation of welding, and does not permit failed evidence. A personal owner action retains all outstanding requirements and the actual signer/capacity rather than claiming conformity or a Picogrid signature.
10. Print the serial dossier using the browser's print function. It is a linked current-state prototype view, not a new approval or a production certificate.

To see a successful ordinary acceptance/release path without manufacturing invented program requirements, use the automated tests' explicitly synthetic fixtures. Seeded application criteria intentionally remain unresolved; no historical workbook trial has been promoted into qualification or approved production settings.

## What is implemented

- Authenticated, responsive shared program workspace and private evidence downloads; CSRF-protected writes and per-command server authorization.
- Typed relational jobs, hardware, operations, people/machines, WPS/PQR/plan revisions, coupon assemblies/welds/passes/specimens/tests, qualification cases, holds, NCRs, approvals, release/shipment records and impact dependencies.
- Create/link forms, named performer versus entrant, source attachments/checksums, acceptance/rejection, immutable approved revisions, amendments and decision/history views.
- Core M checkpoint actions, B evidence and caller returns, C award controls and M START return, H verification and origin-dependent closure; D development records linked to preliminary WPS review.
- Distinct owner actions and recorded Picogrid delegation; scoped ordinary grants, self-approval policy versioning, own-organization senior management and revocation.
- Normal versus pending-coupon versus owner release records; actual prototype shipment separate, with rechecks for restrictions and evidence changes.
- Repeatable setup, migrations, idempotent synthetic data, PostgreSQL validation, browser review and printed traceability view.

## Deliberate prototype limits / not operationally validated

The first implementation does **not** claim all 71 workflow inventory entries are operationally implemented or all 38 verification groups executed. These remain review/test targets. In particular:

- Approved engineering acceptance limits, production quantity/batch trigger scheduling/combining rules, specimen/test/qualification plans, proof-test setup and rework/disposition-release semantics remain unresolved. Generic records can retain their source evidence; the app must not infer their engineering content.
- Automatic in-process continuation while results are pending is not enabled by default. The ordinary production-start control requires matching accepted verification; a later controlled continuation feature needs the outstanding B18 decision. Pending-result shipment is a separately scoped prototype route, not a continuation authorization.
- Nested H/B/C orchestration, early/partial test-set rejection, qualification scope-loss semantics, historical revision effectivity, conditional authorization expiry/withdrawal and detailed impact-clearance/reapproval rules need the corresponding B decisions before operational implementation.
- Prototype proof/inspection/maintenance evidence includes controlled content and stage/result references, not a complete approved structured manufacturing checklist or automatic machine/gauge integration. A working form is not evidence that its content is formally approved.
- Signed-source upload and attribution are available, but the full outage paper fallback/reconciliation operating procedure B45 is not implemented or tested end to end. There is no offline digital client or automatic synchronization.
- Original source files are preserved if available when seeding; the 26 historical workbook rows are **not imported as operational records**, and missing Source 9-1/M1 originals are not reconstructed.
- Device accessibility was checked visually and with basic browser flows, not a full accessibility audit. Hosted-mode login throttling and HTTPS/cookie settings are now prepared and tested locally. External identity/MFA, operational email, malware scanning, retention enforcement, protected external audit archive, disaster recovery rehearsal and live hosting are not configured or validated. These are required operational work, not assumed completed.
- The local private-file upload accepts PDF/PNG/JPEG up to 10 MB with content-signature checks and forced download; this is not malware certification. Original trusted workbook attachment is loaded only by the seeder, not executed or evaluated.
- The audit trail/approved-revision safeguards operate through application services; no claim is made that a database administrator cannot tamper with the database. Production access, protected logging and recovery policies remain required.

## Validation

```bash
scripts/test --verbosity 1
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
```

See [validation record](validation.md) for actual executed checks, environment and limits. The current dev process can be restarted with `scripts/dev`. A setup snapshot retains files and database state, not live server processes. Continue using the existing checkout; do not create a worktree unless requested.

## Visual review

[Desktop overview](screenshots/overview.png) · [Mobile overview](screenshots/overview-mobile.png)

A repeatable browser smoke script is included at `scripts/browser_check.py`. It uses Python Playwright and an installed Chromium at `/usr/bin/chromium` (both available in the current cloud machine), reads only generated local demo credentials, and writes review screenshots under `.local/screenshots`. Run it with `python3 scripts/browser_check.py` after `scripts/dev` is running. Those browser tools are review dependencies, not application runtime requirements.
