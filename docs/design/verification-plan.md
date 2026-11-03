# Verification and operational acceptance plan

**Design only: no application exists; no workflow/security/migration/recovery test below has run.** Source parsing, byte hashes and documentation consistency checks do not validate operational application behavior. Software test success will not qualify welding, approve draft engineering criteria, or authorize production use.

## Evidence and coverage contract

The [71-entry workflow inventory](workflow-coverage-review.md) identifies every explicit Rev C step, decision outcome and caller return. Implement at least one meaningful test for every applicable outcome, not just each grouped row. Track outcome-level cases (for example WF-M12-yes/no/pending), actual execution/run/build/version, expected versus actual result, evidence and reviewer. Do not claim “all paths” from a count of test files; loop combinations are unbounded. Exercise repeated loops, nesting and the composites below in addition to individual branches.

Link tests to RTM requirement IDs, gaps/decisions, source/requirement revisions, schema constraints and screens. Required engineering policies/criteria must be approved or explicitly marked draft development fixtures; unknown criteria cannot be replaced by invented production test limits. Report pass/fail/expected-failure/skipped/disabled/unrun separately; no empty suite or mocked-away gate is acceptance evidence.

## Scenario matrix

Each row includes positive and negative behavior where relevant. Recommended test data are synthetic identified units and explicit draft test fixtures, never real production authorization. Authority-specific behavior awaits resolved A/B questions.

| ID | Significant scenario | Expected invariant / evidence to collect | Trace |
| --- | --- | --- | --- |
| VT01 | Execute every outcome in WF-M01–M15 | Work-order/WPS paths, readiness/engineering review outcomes, all triggers, both checkpoint/issue branches and Gate 2 yes/no/pending represented; correct origin/scope retained | R02–R11; inventory |
| VT02 | Execute WF-A01–A10 for every caller | M→Gate1, B→B, D→D, H→H; corrected failure rewelds, unresolved failure H; no individual routine passing-A record/API/telemetry trail; H PASS recorded | R12–R16; B05/B27 |
| VT03 | Execute WF-B01–B15 with M/C/H origins | Proper prep/current A/NDE-before-cut/test plan, validity versus weld result, correctable repeat/unclear cause H, acceptance authority and return | R17–R26 |
| VT04 | Execute WF-C01–C11 per procedure/operator/machine type | Always B; incomplete/invalid holds/retests; valid failure not qualified under change/H; separate approvals, evidence and returns | R27–R31 |
| VT05 | Execute WF-H01–H12 | Stop/contain/notify, both impact branches, A always, required/optional B/C, escalation and resolved/unresolved, both return gates; hold closure not NCR/release | R32–R37 |
| VT06 | Execute WF-D01–D08 | Defined development basis/A/actual trial values/repeat/preliminary WPS/C/M START; no production hardware or automatic qualification | R38–R40 |
| VT07 | All mandatory triggers together; pairwise and disjoint combinations | Every applicable obligation remains until genuinely covered; no double use with wrong machine/operator/WPS/material/time/tests; no duplicate mandatory record where full coverage approved | R05/R18; B04/B09 |
| VT08 | Initial unqualified machine/operator at readiness | C preparation possible under approved route without authorizing production; Gate 1 cannot deadlock or be falsely passed | B03; R03/R27 |
| VT09 | Same model new/replacement machine; major versus routine maintenance; firmware/gas/filler changes | Unique-machine award required; routine A versus C→B and WPS-change assessment per approved policy; no generic periodic expiry or automatic PQR | R27/R45; B20/B23 |
| VT10 | Operator exactly at, before and after approved >6-month boundary; unknown/backdated activity | Actual welding evidence/date, not login/entry date; defined boundary and lost/scope handling | R27; B21/B22 |
| VT11 | One physical assembly with A/B welds and several root/cover passes/specimens | Separate side actuals/results retained; two sides not two coupons; shared specimen source links valid, no result propagation to unrelated weld | D10; B09/B10 |
| VT12 | Multi-coupon set: partial report/early VT failure/one valid test failure plus pending or invalid results | No overall PASS from partial evidence; no failed-as-pending concealment; authorized early-stop/retest path; failed history retained | B15–17; R24/R25 |
| VT13 | In-process pending continuation allowed/denied and C/H-origin cases | Only applicable scope continues via Gate1; pending obligation not falsely accepted/restarted in an infinite trigger loop; open holds/qualification restrictions persist; live follow-up and shipping restriction | R23; B18 |
| VT14 | Pending coupons arrive pass/fail while job continues or hardware shipped | Resume evidence evaluation, scoped containment/NCR/follow-up, original shipment history retained; approved subsequent-result handling | R11/R23; B34/B37 |
| VT15 | Nested H→A failure, H→B invalid/fail, H→C failure; two simultaneous holds on same machine/job | Root origin preserved; no runaway recursive holds, accidental closure or loss of restriction; allowed verification distinguished from prohibited production | B27; R32–R35 |
| VT16 | Gate 2 non-welding hold / documentation defect | Baseline A and additional review handled as actually approved; no invented exemption or direct resume-welding action | B28; R33 |
| VT17 | Outside-corner coupon and hardware before/after finishing; TTS comparison | Required stages on correct physical target; no corner pull requirement or extension of exemption to TTS; draft radius/throat/fixture not accepted criteria | R07/R20–R22/R48; B11–14 |
| VT18 | Serial-specific static/drop tests, failure, retest and absent setup approval | No other unit's proof result reused; actual load/setup/height/reference/inspection retained; failure H; repeated favorable test does not erase failure | R47; B24 |
| VT19 | Authorized correction/removal/re-weld under disposition; accepted-as-is or other approved disposition | Only authorized actions; Picogrid approval versus Cone collaboration distinct; execution/reinspection/closeout and Gate 2 status per defined policy | R37; B29 |
| VT20 | Normal release, pending coupon release, failed/invalid/noncoupon-missing evidence, denied/expired/withdrawn at-risk authorization | Normal Cone scope honored; only permitted pending-coupon exception; all other requirements apply; exact serial/test/conditions checked at release and shipment | R08–R10; B17/B37 |
| VT21 | Job with mixed serials/joints/operators/machines; partial batch/shipment; split/merge/scrap/replacement | Explicit membership/genealogy, restrictions scope correctly, no lexical range bleed or unrelated evidence acceptance | A04; B30/B31 |
| VT22 | Raced hold opening/test correction/grant revocation versus approval/release/shipment | Transactional checks produce one consistent outcome, stale requests rejected/reviewed; all write/import paths obey same restrictions; retry idempotence | R53; A08/B34 |
| VT23 | WPS/PQR/drawing/criterion/form revisions and changed actual evidence | Historical basis reproducible; current effectivity explicit; no automatic latest-version substitution, old approval reused on modified bundle or qualified range inferred from point | R40–R42; B20/B35 |
| VT24 | Record rejected, corrected, canceled, reopened or withdrawn | Rejection/technical failure distinguished; source/reason/actor/history retained; resubmission and dependent review follow agreed policy | B33; P3.2–3 |
| VT25 | Lab revision/evidence error discovered after approval, release, shipment | Reverse impact identifies every affected unit/award/release, original history preserved; appropriate current restrictions/notice/disposition recorded; no fabricated recall command | A08/B34 |
| VT26 | Signed paper with performer/entrant/approver different or same | Signature/source/time and actual work attribution retained; no worker digital reconfirmation required; authority/type/scope still required; mismatch not silently reconciled | D03/D06/D09; B36 |
| VT27 | Controlled outage paper approval then delayed conflicting digital entry | Current-hold/authority fallback checks, signed source, event/entry time and reconciliation; no silently lost earlier hold or duplicate release | A03/D14; B45 |
| VT28 | Each action: perform, inspect, assess validity, accept/reject, approve, disposition, close, release, ship | Test correct action/scope grant, wrong organization, expired/revoked/missing grant, out-of-scope subject and technical qualification conditions; screen hiding alone insufficient | A06/B19; R50/R51 |
| VT29 | Self-approval allowed, later restricted; helper entered work of approver/other person | Allow initially only authorized signer with required evidence; effective restriction compares actual performer/preparer rather than entrant; past approvals retain original policy | D06; R30/R50/R53 |
| VT30 | User acts as software owner versus recorded Picogrid delegate | Real signer and acting capacity preserved; no automatic conversion of read/admin access into customer approval; delegation scope/effectivity checked as defined; owner exceptions retain underlying facts | A02; D07/D16 |
| VT31 | Program/org isolation across records, searches, downloads, exports, audit and attachments | Picogrid/AM Kreations broad read honored; Cone/lab restrictions per A05; direct object-ID, hidden API, URL guessing and export cannot leak records or grant action | A05; R51 |
| VT32 | Duplicate/unknown human IDs and imports, incomplete references, cross-program joins, invalid units/typed raw data | DB/domain constraints preserve referential integrity; no fuzzy-name merge; raw text retained; null/unknown/N/A not pass | R43/R46; B30/B39 |
| VT33 | Full 11-sheet mapping and repeated import of exact source bytes | Reconcile 26 source rows, not 26 assumed assemblies; all source coordinates/unknown dates preserved; no fabricated Source 9-1/M1 snapshot or =TODAY historical date; idempotence | R44/R46; B39 |
| VT34 | Frozen record/attachment substitution or deletion, privileged maintenance, app rollback | Approved evidence version/checksum reproducible, correction attributable; acknowledge DBA capability rather than claim impossible tampering; protected audit/backup recovery verified | R42/R51; B40/B41 |
| VT35 | Authentication/session/CSRF/XSS/upload/download/rate-limit/recovery/offboarding cases | Named attributable access, unsafe file content isolated, secrets private; MFA/recovery/timeout according to agreed policy; shared device not shared approval | B42; R51 |
| VT36 | Backup and restore complete DB + attachments + approvals/audit across failure | Consistent recoverable dossier and dependency state; measured recovery meets agreed objective; restoration checked functionally, not merely backup exit code | B40/B41 |
| VT37 | Realistic floor/office/customer UAT with assisted entry and representative device | Fields available at right stage, legible units/status/printing/accessibility, no unnecessary repeated entry or routine A logging; signed-source review usable | B32/B44; screens S01–S15 |
| VT38 | End-to-end release dossier/report/export and controlled Cone mapping | Complete trace serial→operation→WPS/qualification→coupon/weld/specimen/report/inspection/hold/disposition/proof→release→shipment; approver identities/basis/revisions consistent across views | R41/R44/R52; B43/B44 |

## Authority boundary proof

For each role/capability combination in VT28–VT31, test the server command directly as well as browser entry: permitted actor/action, permitted actor wrong scope, technical performer without organizational approval grant, administrator/developer without engineering grant, and helper with paper source but no signing authority. The personal owner capability and any formally delegated Picogrid authority require distinct acting-capacity evidence under the resolved A02 policy; do not test them as a generic normal-user bypass. Different actions can require different qualification evidence; B19/A06 must define it rather than using a blanket “welder qualified” flag.

## Exit criteria proposed for review

1. Architecture A questions resolved and reviewed architecture explicitly approved before application coding.
2. B questions applicable to each delivered feature resolved before implementation; formal engineering/customer requirements and source alignment evidenced where required. Draft software fixtures visibly isolated from operational approval.
3. Every applicable workflow outcome/caller return, significant permission boundary and data relationship has meaningful tests; known defects/skips have explicit disposition and no silent suppression of required checks.
4. Controlled migration/equivalence mappings and representative role-based end-to-end UAT demonstrate actual expected behavior; no generic “tests passed” substitutes for proof of intended cases.
5. Source-revision and authority history, amendment/late-result impact, owner/delegate attribution and paper fallback demonstrated; backup/restore and security/operational requirements tested.
6. Named program authorities accept the operational use and deployment scope. Software acceptance, approved manufacturing requirements, welding qualifications and hardware release remain separate decisions.

Track these as review proposals until B43 assigns the accepting roles and criteria. No production-readiness claim is made by this document.

## Critical-decision closure

A01–A08 are now resolved at architecture level, not proof of operational readiness. A07 uses an explicit no-known-compulsory-constraints assumption; later customer requirements must be checked before deployment. A08 confirms the expected VT25 behavior: automatically flag dependent records and pause further affected approvals/releases/shipments pending authorized scoped review, preserve history and do not invent disposition/recall actions. VT22 must cover races with this restriction. Detailed B33–B35 review/clearance behavior remains required before implementing it. No application test has run.
