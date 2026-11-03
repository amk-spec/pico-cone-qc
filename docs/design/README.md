# Picogrid Lander QC — requirements and architecture review

Status: **architecture approved for a bounded development prototype (D23).** See the [implemented prototype guide](../prototype/README.md) for demonstrated features and explicit limits. Source drafts and engineering TBDs are not production-approved. Design date: November 2, 2026 (America/Los_Angeles).

## Comprehensive gap review now in progress

The [gap register](gap-analysis.md) uses the requested A critical / B required-before-feature / C optional taxonomy. It supersedes legacy Q priorities. The [decision log](decision-log.md) preserves answers and their exact scope. [Workflow coverage](workflow-coverage-review.md), [record/lifecycle review](record-lifecycle-review.md) and [verification plan](verification-plan.md) are the evidence for the new review. The gap review remains the requirements record. The architecture was subsequently approved for the bounded prototype D23; no operational readiness is claimed.

A01 official record ownership, A02 signer/owner-versus-Picogrid-delegate attribution and A03 controlled paper fallback are confirmed. A04 independent serial outcomes, A05 shared program reads/no initial lab accounts and A06 scoped organizational grant management are confirmed. A07 no-known-compulsory-platform-constraints is accepted as a bounded assumption, and A08 dependency flags/paused further affected decisions pending review is confirmed. All eight critical questions are resolved; the user subsequently approved the revised architecture for the bounded prototype D23. Technical/customer constraints remain unresolved where marked B, even though the architecture can represent their TBD status. Those authorization gates were subsequently satisfied for the bounded development prototype D23, without waiving B engineering/operational controls.

The [revised architecture summary](architecture-review-summary.md) consolidates the eight critical decisions and remaining implementation gates.

## Review recommendation

Use a standalone web application with a relational database and a server-enforced implementation of Rev C. Keep process routing, evidence validity, qualification, hold closure, hardware disposition and shipment authorization as separate concepts. Recommend a Django/PostgreSQL modular monolith, responsive server-rendered screens, private attachment storage and organization-scoped access. User direction favors the application as primary record system/traveler, with an approved Cone variation possible, broad Picogrid/AM Kreations visibility, and online use with manual/assisted entry. Each organization will have a senior approver within procedural limits; Picogrid will not handle routine Cone qualification approvals. The user personally requests unrestricted application owner authority, modeled as attributable exceptions to ordinary roles. Self-approval is allowed initially, with configurable restrictions by the responsible authority. Official QC/approval/release record ownership is now confirmed in the application with approved Cone alternatives. Owner and formally delegated Picogrid acting capacities are distinguished; organizational policy/grant management is confirmed within each senior approver's own scope. Specific delegations/technical requirements remain B-level; A07 is resolved on the no-known-compulsory-constraints assumption and A08 automatic impact flags/paused further affected decisions is confirmed. The architecture is approved for prototype development only.

Rev C is the **locked software development baseline**, as confirmed in this conversation. It remains **Discussion Draft, Not Approved for Production Use**. Rev A supplies implementation details and remains a discussion draft. The workbook supplies record and data references; it cannot change routing or establish acceptance criteria. A completed software record, successful development test or administrative privilege conveys no engineering approval. This package does not authorize production welding or hardware release.

## Deliverables

| Artifact | Contents |
| --- | --- |
| [Source register and review questions](sources-and-decisions.md) | Exact source identities, gaps, potential conflicts, architecture decisions and prioritized engineering questions |
| [Requirements traceability matrix](requirements-traceability.md) | Source → requirement → data/workflow/screen → proposed verification |
| [Organizational authority and qualification matrix](authority-and-qualification.md) | Organizational responsibilities, scoped grants, qualification evidence and unresolved authority |
| [Proposed relational schema](relational-schema.md) | Entities, keys, cardinalities, integrity rules, revisions, audit and attachment design |
| [Workflow-state model](workflow-state-model.md) | M/A/B/C/H/D routes, caller returns, concurrent pending evidence, holds and release |
| [Application screen map](application-screen-map.md) | Navigation, role actions, linked records, conditional forms and status visibility |
| [Technology evaluation](technology-evaluation.md) | Alternatives, recommended architecture, security, operations and validation strategy |
| [Workbook simplification and migration](workbook-simplification.md) | Repeated fields, authoritative records, source-cell mappings and historical data controls |

## Decisions needed before implementation

1. The [revised architecture summary](architecture-review-summary.md) was approved for bounded prototype development (D23). All eight critical decisions are resolved; actual delegation details remain B46. Architecture approval and authorization to implement are separate from answers to clarification questions.
2. Define affected B controls before implementing their functions, including hosting/security/retention, engineering limits, signed-paper attribution and detailed outage fallback B45. Controlled paper fallback policy A03 is confirmed.
3. Resolve remaining test/set mapping questions (Q08/Q09). The user accepted Q06/Q07 return routes for software design; retain source wording discrepancies for controlled alignment. A/B are now confirmed as separate welds on one coupon assembly. Do not turn unresolved technical criteria into configured passing rules.

All current questions and priorities are in the gap register; the source register preserves legacy question history. No answer is assumed from silence. Schema extensions and configurable requirements allow analysis to proceed while technical criteria remain TBD; production behavior that depends on those criteria cannot be finalized until their controlled definitions are supplied.

Cone designated approvers may close process holds after required checks pass and the problem is resolved. Cone may collaborate on hardware disposition; Picogrid retains disposition approval.

## Scope and exclusions

Covers the Lander joint families and Cone welding process identified in Rev A, independent of ShopForge. Includes jobs/serials, development, WPS/PQR, operator and machine qualification, coupons/specimens/tests, inspections, holds/NCRs, approvals, proof-test evidence and release. Excludes autonomous engineering decisions, machine control, physical safety enforcement, inferred acceptance limits, redesign of joints/fixtures and unapproved standards requirements. No presumed regulatory certification, retention duration or compulsory logging is added.

This is an initial source-traced design, not a signed requirements baseline or a complete manufacturing specification. Technical acceptance criteria, drawing release, proof-test setup, qualification details and several authority assignments remain open. Verification scenarios are proposed acceptance tests for a later implementation; none are claimed executed against an application.
