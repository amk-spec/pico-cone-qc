# Workbook simplification and source-preserving migration

Goal: enter a fact once, reuse it through links/views, preserve independent record identities and approval acts. This changes data handling, not QC requirements. Equivalent Cone variations remain possible through approved mappings (P3.6.1), as the user requested. The proposed primary system is the application and traveler, subject to final review; it must not impose a second traveler on Cone where an approved equivalent already exists.

## Repetition and proposed source of truth

| Existing repetition / concrete source | Proposed authoritative fact and reuse | Required distinction preserved |
| --- | --- | --- |
| Machine ID, model/serial in PQR 13, Universal Coupon 10, Coupon Register D/E, Production QC 14, Equipment Log C, Qualification Register C/L | Select unique Machine once; link event/operation/coupon/award; snapshots keep historical identity | Identical model is not identical machine; qualification tied to unique ID |
| Operator in PQR C10, Universal Coupon 9, Coupon Register D, Production QC 13, Qualification Register C | Person plus actual performer links; separate account and entered-by | Helper is not worker; qualification not approval authority |
| Job/drawing/material/filler/WPS header repeated across WPS/PQR/Universal Coupon/Production QC | Select versioned WPS, drawing and actual operation/setup; choose lots rather than type names repeatedly | WPS nominal/ranges versus actual coupon/production facts; actual lot/setup must be verified, not auto-attested |
| Actual root/cover parameters in PQR 25–60, Universal Coupon 21–37, Coupon Register H–M | PassActual rows on the specific assembly weld/side; PQR references evidence and register derives summary | No automatic production range from actual point; raw machine settings/units retained |
| Macro/pull/VT results in PQR 73–94, Universal Coupon 38–41/75–107, Coupon Register S/T/Z–AB, Production QC 40–43 | Specimen/TestAttempt/Inspection with source report; linked acceptance reused in views | Test validity, valid failure and acceptance/signoff remain separate; retests retain failed/invalid attempts |
| Coupon identity and acceptance in Universal Coupon, Coupon Register, PQR, traveler | One set/physical assembly/weld-feature/specimen identity chain; registers and evidence references generated | A/B are confirmed separate welds on one assembly; preserve both weld identities without counting them as two physical coupons. Set-level mapping remains open |
| Outside-corner pre/post-finish detail in PQR 106–116, Universal Coupon 75–87, Production QC 54–64 | Stage-specific inspection records on actual target; views use references | A coupon's inspection cannot substitute for required inspection of production hardware |
| Qualification status in WPS/PQR, Production QC 13–19 and Qualification Register | Scope-specific QualificationAward plus evidence and effective restrictions | Procedure, operator and machine approvals stay distinct; do not derive “qualified” from test PASS alone |
| Serial/coupon references in Coupon Register W–Y, Universal Coupon 61–68/105, Production QC 38/74–81 | Explicit population/coverage memberships and checkpoint record | Serial presence is not a frequency trigger; preserve exact affected population and sequence |
| Hold/NCR description and closure fields repeated within Hold NCR 6–32 and 35–44, with traveler exception links | Common Issue context; separate Hold/NCR/Disposition records, linked from traveler | Hold not automatically NCR; process closure not hardware acceptance or shipping authority |
| Gate 2 decisions in Production QC 45–52 and 72–82 | One revisioned ReleaseAssessment/Decision shown in both summary and detail; shipment/CoC linked | Normal Cone release, Picogrid pending-coupon authorization and physical shipment differ |
| Proof-test reference in Production QC 48/74 and Assembly Proof Test A–R | Per-serial ProofTestRecord/test occurrence plus its approved setup/evidence, referenced by release | Each serial's actual static/drop evidence retained; proposed applicability/setup not silently approved |
| Common procedure/control text scattered in WPS, START HERE, Production QC and Lists | Versioned source/requirement references with contextual guidance | Workbook captions/list choices do not become engineering authority or route overrides |

Master lookup selection can prefill identifiers and planned requirements. The performer/reviewer must still confirm actual setup and evidence where required. “Reuse” never means copying a PASS onto another unit, deleting an approval, collapsing development into qualification or creating routine passing A records.

## Full worksheet mapping

| Sheet / source range | Target / treatment |
| --- | --- |
| START HERE A1:H44 | Source/document metadata, reference guidance, controlled-baseline/status links. Missing Source 9-1 explicitly flagged; reference notes retained, not executable policy. |
| WPS - Working A1:F117 | WPSRevision, WPSPassRequirement, joint/material/tooling/inspection requirement links; draft constants retained as proposed/unverified. |
| PQR - Working A1:F122 | PQRRevision links to actual coupon/pass/inspection/test evidence and Picogrid approval. Repeated actuals presented from source evidence once mapping is verified. |
| Universal Coupon A1:F107 | CouponSet/physical coupon/context/actuals, purpose-specific evidence, inspections, specimens/tests, acceptance and caller links. Do not force procedure-only fields on WPQ/machine cases. |
| Coupon Register A5:AE131 | Derived register plus reviewed historical import. Rows 6–11 contain 6 TTS-D entries; rows 112–131 contain 20 M1 entries. Blank formatted rows are not records. |
| Production QC A1:F82 | WorkOrder/Operation/Population/readiness/trigger/inspection/release links; duplicate Gate 2 sections become one view; routine A remains unlogged. |
| Assembly Proof Test A1:R109 | Per-serial ProofTestRecord fields/plan/setup/result; template note/default orientation are not evidence of performed testing. |
| Hold NCR A1:F44 | Issue + Hold + optional separate NCR/disposition/verification; origin/return and H A evidence captured without duplicate facts. |
| Equipment Log A1:P105 | Machine, MaintenanceEvent, impact classification, required route/qualification evidence and return-to-service decision. |
| Qualification Register A1:R105 | QualificationCase/Award/Scope/ActivityEvidence/Approval with separate organizational authority. |
| Lists A1:L7 | UI vocabulary proposals only; validate against domain definitions. “Expired”, “N/A”, “Approved to Resume” are not universal engineering rules. |

## Historical data findings

- Six TTS-D entries dated September 1, 2026 retain raw parameter text and observations/follow-up in Coupon Register rows 6–11. Source coordinates are references, not proof that the absent original snapshot matches. Missing operator/machine/gap values remain unknown.
- Twenty M1 entries in rows 112–131 name Jake and machine NE130218L, carry raw root/cover and macro observations and are explicitly **Development - not qualified**. A person name is not automatically resolved to a confirmed identity. The V-column describes source `=TODAY()` dates as unverified; do not fill historical weld dates with the current date.
- User confirms A/B are separate welds on a shared coupon assembly. Group verified A/B pairs under that assembly, retain side-specific parameters/observations, and separately identify any extracted specimens. Check each historical pairing/source before merging; no inference that a side is an extracted specimen. A note such as “ALLOWED SIDE A TO COOL FOR AT LEAST 120 SEC.” is a historical observation, not a mandatory interpass rule.
- P3.8 and START HERE claim a Source 9-1 preservation sheet, but none is present. M1 Pass Data is also referenced but absent. Current bytes can be preserved; original-source fidelity cannot be fully verified from this workbook alone.
- There are no completed production releases or qualification approvals inferred from populated template text. A prefilled word, suggested number, “None” observation or blank cell is not an accepted result.

## Proposed migration procedure (not executed)

1. Obtain authorized controlled source location and missing originals, record immutable file hashes/version/status; preserve source binaries verbatim.
2. Inventory sheets/cells/formulas, drawing references, IDs and record purpose; create an import preview outside production approval flows. Avoid executing formulas/macros. Preserve both formula text and available cached value as source evidence with provenance.
3. Map common identities to canonical records with human review, retaining original labels. Detect duplicates by source identity + source row/record ID, not fuzzy name alone. Keep set/coupon/specimen mapping unresolved until confirmed.
4. Import development data as unqualified draft/source-backed historical entries, preserving raw parameter strings/notes and source coordinates. Add typed measurements only when meaning/units are verified; keep source and interpreted values separately attributable.
5. Reconcile expected 26 present development entries and populated-source fields; prove repeat import is idempotent. Compare hashes and spot-check each mapping type, unknown date, multi-pass raw text and observation relocation. Report missing snapshots as unresolved.
6. Obtain controlled review of migration and any Cone equivalent-record field map before production reliance. Migration acceptance does not qualify welds or release hardware. Preserve amendments and avoid retroactive overwrite of completed records.

## Manual and Cone variants

Provide identified printable forms, paper attachments and assisted entry into the same entities. Store actual worker/date, entry person/date, signed source and distinct approval evidence. Unknown/illegible values go to review, not guessed values. Signed paper is accepted for assisted entry and appropriately authorized approval; no additional worker digital confirmation is required solely because entry was assisted.

For a Cone variation, map every required check, acceptance decision, serial population, coupon checkpoint/frequency, hold/NCR and release authorization to its controlled field/record. Record which system owns each fact and revision; changes in the Cone form require a mapping revision. Avoid bidirectional automatic edits in the initial architecture. A mere scan or API connection does not demonstrate equivalence.

## Comprehensive reinspection corrections

Reinspection found 11 sheets including hidden Lists; the delivered workbook has no active formula cells or external workbook links. The `=TODAY()` references in Coupon Register V112–V131 are text describing unavailable source history, not active workbook date formulas. Validation for Coupon Register purpose/result only covers rows 6–111 and excludes all 20 M1 rows. This is a workbook validation coverage gap, not evidence the historical values are wrong or approved. Preserve source rows and validate mapping independently; do not copy validation bounds as application behavior. Universal Coupon A12 has a drawing-reference comment; record the actual controlled drawing revision rather than treating that comment as drawing release. A01 official record ownership and A03 controlled paper fallback are confirmed; equivalent Cone field maps and B45 reconciliation details remain required.
