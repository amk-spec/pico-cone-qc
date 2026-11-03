# Revised application architecture — for explicit review

Status: **approved by the user for bounded development-prototype implementation (D23); not approved for operational/production use**. All eight architecture-critical questions have been answered in [D13–D22](decision-log.md). This summary consolidates those answers; it is not approval of draft engineering documents or a claim of operational readiness.

## Recommended architecture

A standalone, responsive Django web application with PostgreSQL and private, versioned evidence-file storage. Use one modular application with explicit Rev C domain transitions and transactional authorization checks. Keep the web UI suitable for shop-floor, office, customer and assisted entry. The local prototype now uses Django and PostgreSQL. No public/production hosting account or deployment has been created; see the prototype guide for actual validation and limits.

| Area | Confirmed architecture decision / recommended realization |
| --- | --- |
| Official records | Application owns QC, approval and release history. Cone may use approved equivalent traveler/forms with a field mapping and one authoritative source per fact; no duplicate mandatory traveler. |
| Work scope | One work order may contain several Landers with independent serial/joint-operation state, operators/machines, holds and release/shipment outcomes. Group entry without granting group-wide acceptance from one unit's evidence. |
| Shared visibility | Picogrid, Cone and AM Kreations share Lander program records. Read access does not grant edit/approval authority. Labs initially submit reports without accounts. Private credentials and unrelated programs are not shared. |
| Organizational authority | Senior approvers manage backup grants/revocation and self-approval restrictions within their organization's procedural authority. Technical qualification, organizational designation and software permission remain separate. |
| Self-approval | Initially allowed only for a person already authorized for the approval type/scope, with all required qualifications/evidence satisfied. Later policy restrictions apply to subsequent decisions; history retained. |
| Owner/delegate capacities | User personally has requested unrestricted owner application power. Decisions name the actual signer and authority used; Picogrid approval requires recorded applicable Picogrid delegation, while owner-only action remains separately identified. Original facts/results remain unchanged. |
| Paper and outages | Signed paper supports assisted entry and authorized approval without mandatory worker digital reconfirmation. Controlled paper fallback during outages is accepted; current authority/hold checks, timing and reconciliation details still need B45 definition. No offline digital client is assumed. |
| Workflow and evidence | Rev C remains the locked software routing baseline and a discussion draft. Separate caller-aware workflow, validity, technical acceptance, qualification, process holds, hardware NCR/disposition, release and actual shipment. Preserve the accepted C→M START and C→H verification/problem-resolution returns. |
| Coupon structure | Test set → physical coupon assembly → separate A/B welds → actual passes; extracted specimens link to source weld(s). Two welds on one assembly are not automatically two physical coupons. Plan counts/aggregate acceptance remain engineering decisions. |
| Record integrity | Freeze identified approved revisions and evidence manifests; corrections/amendments preserve originals. Track dependencies from test/report/WPS/qualification evidence through affected units/decisions/releases/shipments. |
| Adverse evidence | Incorrect supporting evidence automatically flags dependent records and pauses further affected approvals/releases/shipments pending authorized scoped review. Preserve original history. Cone handles process matters; Picogrid retains affected-hardware disposition, including shipped hardware. No automatic recall/disposition is invented. Detailed scope/clearance/reapproval B33–B35 remains required. |
| Hosting constraints | No compulsory provider/location/login/signature/storage constraints currently known. Use this explicit bounded assumption for architecture; check later customer constraints before operational deployment. It does not waive security, retention, recovery or identity requirements. |

## Domain boundaries and stored relationships

Keep modules for identity/authority, controlled requirements/documents, jobs/hardware, development/qualification, coupons/welds/specimens/tests, inspections, holds/NCR/disposition, release/shipping and reports/imports. PostgreSQL holds canonical relationships, scopes, revision references, actor/capacity/grant records and decision/dependency state. Private object storage holds original signed paper, reports, photos and versioned evidence objects; database manifests identify the exact bytes used by approvals.

Derived registers/travelers/dossiers reuse facts without collapsing WPS instructions into PQR actual evidence, qualification into approval authority, process-hold closure into hardware disposition, or release authorization into shipment. Routine passing strike-plate checks remain unlogged; required H checks and reportable exceptions remain documented.

## Remaining gates

- **Architecture review:** explicit approval and bounded prototype authorization received D23. This supersedes the prior waiting status; it does not authorize production use or silently resolve B requirements.
- **Affected feature implementation:** the [46 B questions](gap-analysis.md) still include required technical/customer definitions: acceptance criteria, verification intervals, qualification/continuity details, proof-test applicability/setup, early/partial failures, hold/retest interactions, rework/disposition, source mappings, signed/paper fallback details, delegation evidence, revision-impact/clearance and operational controls. Resolve them in manageable groups before implementing the affected behavior. Do not turn TBD values into passing rules.
- **Operational use:** controlled engineering approvals/source alignment, data/source/equivalent-record validation, role-based verification/UAT, security, backup/restore and maintenance responsibilities must be evidenced. Test success never substitutes for welding qualification or hardware release.

The [71-entry workflow inventory](workflow-coverage-review.md), [record lifecycle review](record-lifecycle-review.md), [53-requirement matrix](requirements-traceability.md) and [38-group verification plan](verification-plan.md) are the review evidence. All proposed application tests remain unrun. Source PDFs/workbook and application source remain unchanged.
