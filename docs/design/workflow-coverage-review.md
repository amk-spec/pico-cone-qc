# Rev C workflow completeness and branch review

This is a documentary inventory against the complete visual Rev C chart and Rev A Part 2, not an executed test result. Every named step, decision outcome and caller return is represented below. Grouped outcomes each require separate later test execution. Unresolved interpretations are linked to gaps; inventory presence does not mean the behavior is approved or implemented. Existing RTM references retain R01–R53.

## Master M

| Verification ID | Source step / trigger | All branches, prerequisites or effects to verify | RTM / gap |
| --- | --- | --- | --- |
| WF-M01 | F M START; P M.2.1 | Enter with job/work-order/contract context; identify scope and applicable WPS | R02; A01/A04/B30 |
| WF-M02 | Approved WPS, no changes? P M.2.2 | YES→readiness; NO→D. Draft/missing/changed WPS not treated as approved unchanged WPS | R02/R38; B01/B20 |
| WF-M03 | Readiness P M.2.3 | WPS revision, qualified operator and unique machine, materials/filler, fixtures and verification requirements all examined | R03; B01/B03/B21/B25 |
| WF-M04 | Gate 1 P M.2.4 | YES→identify all triggers; NO→engineering review, not welding | R03; B02/B03 |
| WF-M05 | Engineering review F M/P M.2.4 | Resolved→readiness; unresolved→H; interim authorization only within defined authority/scope | R03/R04; B02 |
| WF-M06 | Identify ALL triggers P M.2.5 | A, B, C triggers can coexist; preserve every applicable obligation and approved combined-event coverage | R05; B04/B08/B09 |
| WF-M07 | Verification still required? P M.2.6 | YES→each applicable A/B/C with caller context; NO→controlled welding only with no incompatible restrictions | R05/R06; B04/B18 |
| WF-M08 | Controlled production P M.2.7 | Approved/authorized controls; missing qualification/open applicable hold prevents ordinary production | R06; B02/B21/A02 |
| WF-M09 | Checkpoint/trigger/issue? P M.2.8 | NO→continue to final inspection; YES→quality-issue decision | R06 |
| WF-M10 | Quality issue? P M.2.8 | YES→H; NO→trigger identification; no direct completed-subprocess→welding return | R06/R32 |
| WF-M11 | Final inspection P M.2.9/1.8 | Outside-corner pre-finish VT/correction before finishing; post-finish VT/dimensions/radius; other joints per approved plan | R07/R08; B12/B29 |
| WF-M12 | Gate 2 P M.2.10 | YES→authorized release; NO→H; pending-coupon-only→Picogrid at-risk decision. Known failures/other unmet requirements not pending route | R08–R10; B01/B17/B24/B29 |
| WF-M13 | Picogrid ship at risk? F M/P M.2.10 | YES with explicit scoped evidence/conditions→authorized pending-coupon route; NO/absent→hold shipment | R10; B37/A02 |
| WF-M14 | Wait for pending results F M | On results available repeat Gate 2; late failure H/NCR and affected population; approved waiting does not lose follow-up task | R10/R11; B34/B37 |
| WF-M15 | END release P M.2.11 | Cone normal authority, explicit Picogrid pending route; release not shipment. Approved hardware via disposition requires B29 definition | R09–R11; A02/B29/B37 |

## Strike plate A

| Verification ID | Source step / trigger | All branches, prerequisites or effects to verify | RTM / gap |
| --- | --- | --- | --- |
| WF-A01 | F A triggers; P A.1 | Shift/session, idle above approved threshold, gas cylinder, filler reload, nozzle and lens changes each trigger A; no default 20 minutes | R12; B05/B06 |
| WF-A02 | P A.2.1 | Accept M/B/D/H entry, preserve exact caller; no fabricated C-direct entry replacing C→B→A | R16 |
| WF-A03 | P A.2.2 | Clean representative plate, reuse only suitable surface, never production hardware; filler within approved WPS before reload check | R13; B06/B25 |
| WF-A04 | P A.2.3/1.8 | Visual screen and machine/error indications, especially after nozzle/lens work; no added destructive/dimensional test | R13; B12 |
| WF-A05 | Acceptable? P A.2.4 | YES→acknowledge/return; NO→operator self-check | R14/R15 |
| WF-A06 | Self-check P A.2.5 | Gas fittings/flow meter/flow, nozzle/lens/filler/settings/cleanliness; minor authorized correction | R14; B07 |
| WF-A07 | Found/fixed? P A.2.6 | YES→reweld A; NO→H; repeated failed A from active H needs root-hold handling | R14; B27 |
| WF-A08 | P A.2.4/3 | Routine PASS has no individual log/traveler entry; failures requiring H/potential hardware impact documented; H PASS includes actor/machine/time/action reference | R15; B05/B07 |
| WF-A09 | F A exits | M→Gate 1; B→B; D→D; H→H with hold open. Test each return separately | R16 |
| WF-A10 | P A.5 | Purge recommended unless approved mandatory instruction; strike plate gas flow not proof of complete purge | R12/R13; B06 |

## Coupon B

| Verification ID | Source step / trigger | All branches, prerequisites or effects to verify | RTM / gap |
| --- | --- | --- | --- |
| WF-B01 | F B/P B.1 | Preproduction, approved in-process checkpoint, C qualification and H-directed testing; serial existence alone not trigger | R17; B08 |
| WF-B02 | Combining events P B.1 | Match joint families/materials/machine/operator/WPS/timing/tests/traceability/authorization; incomplete coverage cannot close another trigger | R18; B09 |
| WF-B03 | Entry P B.2.1 | M/C/H caller and scope retained | R26 |
| WF-B04 | Preparation P B.2.2 | Current A; two physical coupons/family per approved plan; representative batch/fit-up/clamping/suspended support/no table backing/finishing | R19; B05/B09/B11 |
| WF-B05 | Inspection/extraction P B.2.2–3 | Required NDE before any cutting; outside-corner before/after finishing; layout reserves required specimens; integrity/geometry check | R20/R21; B10/B15 |
| WF-B06 | Tests P B.2.4 | Finished outside-corner macroetch as specified; no Lander enclosure corner pull; other joint tests per plan; lab or approved in-house evidence | R21/R22; B12/B13/B19 |
| WF-B07 | In-process pending? P B.2.5 | NO continuation→stop production until results; YES authorized→M Gate 1 with shipment hold and live pending B; not general preproduction/C/H bypass | R23; B17/B18 |
| WF-B08 | Results arrive P B.2.5 | Resume B validity and eventual caller return; preserve follow-up while production context changes | R23/R26/R11; B34 |
| WF-B09 | Complete/valid? P B.2.6 | YES→acceptance, even bad valid result; NO→invalidity/correctability, not automatic weld rejection | R24 |
| WF-B10 | Obvious correctable cause? | YES→fix/repeat B preparation with prior attempt retained; NO→H | R24; B16/B27 |
| WF-B11 | All approved criteria met? P B.2.7 | YES→record acceptance; NO→weld nonconformance, containment, NCR, Picogrid disposition and H; partial failure/early NDE questions B15 | R25/R26; B12/B15 |
| WF-B12 | Documentation P B.2.8 | Cone designated acceptance, traveler references same coupon record; no implied C qualification from B acceptance alone | R26/R30 |
| WF-B13 | Return from M | B completion→M Gate 1 | R26 |
| WF-B14 | Return from C | B completion→C evidence-validity decision; C approval remains separate | R26/R29 |
| WF-B15 | Return from H | B completion→H verification acceptability; does not close H | R26/R34 |

## Qualification C

| Verification ID | Source step / trigger | All branches, prerequisites or effects to verify | RTM / gap |
| --- | --- | --- | --- |
| WF-C01 | F C/P C.1 procedure | New/revised WPS, essential-variable change; reconcile nonessential-revision rule rather than assume every edit needs new PQR | R27/R38; B20 |
| WF-C02 | F C/P C.1 operator | New, inactivity >6 months, lost qualification, training need from H; exact continuity evidence/calculation approved | R27; B21/B22 |
| WF-C03 | F C/P C.1 equipment | Every new/replacement unique machine, even identical; major maintenance affecting performance→C→B, not routine A-only | R27/R45; B23 |
| WF-C04 | Scope P C.2.1–2 | M/D/H origins; determine types/subjects/scope, combined plan with separate awards/approvers | R28; B09/B21 |
| WF-C05 | Coupon P C.2.3 | Always B; nested B→A if needed; no award from routine A or development result alone | R29 |
| WF-C06 | Complete/valid? P C.2.4 | NO→qualification evidence hold/retest B; YES→acceptance; B failures also propagated to C case | R29; B15/B27 |
| WF-C07 | Meets criteria? P C.2.5 | NO→not qualified under change/no welding under change→H; YES→required approval; prior unaffected scopes not silently revoked | R29/R30; B21 |
| WF-C08 | Approval P C.2.6 | Picogrid procedure; Cone operator/equipment; each subject/scope approved separately; self-approval only if authorized | R30/R50; A06 |
| WF-C09 | Record P C.2.7 | Freeze scope/limits/evidence/signatures; no automatic production parameter ranges inferred | R30/R41 |
| WF-C10 | Return M/D P C.2.8 | M START/work-order-WPS review then readiness; user accepted interpretation, source graphic discrepancy retained | R31; D11/X03 |
| WF-C11 | Return H | Verification acceptable then problem resolved/closure; user accepted; P C.2.8 wording discrepancy retained | R31/R34; D11/X04 |

## Engineering Hold H

| Verification ID | Source step / trigger | All branches, prerequisites or effects to verify | RTM / gap |
| --- | --- | --- | --- |
| WF-H01 | Entry/STOP P H.1/H.2.1 | A/B/C/M including failed Gate 2; stop/tag machine/job, preserve originating gate and affected population | R32; A04/B27 |
| WF-H02 | Hardware could be affected? P H.2.2 | YES→contain to last good check and notify Picogrid; NO→investigate without automatic hardware NCR; unknown impact not accepted | R32/R36; B07/B26 |
| WF-H03 | Troubleshoot P H.2.3 | Responsible party cause/actions/documentation; assignment/notifications open | R33; B26 |
| WF-H04 | Always A P H.2.4 | H remains open; record PASS/FAIL; non-welding issue may need other review, not an invented automatic A exemption | R33; B28 |
| WF-H05 | B/C required or wanted? P H.2.5 | YES→B or C and return; NO→acceptability decision. Failed coupon/qualification requires applicable B/C, cannot select NO to bypass | R34; B21 |
| WF-H06 | Verification acceptable? P H.2.6 | NO→escalate help, return troubleshooting; YES→problem-resolved decision | R34; B27 |
| WF-H07 | Problem resolved? P H.2.7 | NO→escalate/hold open; YES→corrective-action record and authorized closure | R35; D08 |
| WF-H08 | Process closure P H.4; user | Cone designated approver after required checks pass/problem solved; no automatic NCR/disposition/release clearance | R35–R37; D08/B29 |
| WF-H09 | Return origin Gate 2 | Closed process hold→M Gate 2 | R35 |
| WF-H10 | Return other origin | Closed process hold→M Gate 1; not direct welding | R35 |
| WF-H11 | Quality issue/NCR P H.4.1–2 | Process-only hold can exist without NCR; identified/suspected nonconforming hardware requires formal evaluation/disposition; unresolved product impact not accepted | R36/R37; B07 |
| WF-H12 | Hardware disposition P H.4.2 | Containment→NCR→Picogrid approved disposition→only authorized execution→reinspection/retest→authorized closeout; Cone collaboration does not substitute for approval | R37; B29/B34 |

## Development D

| Verification ID | Source step / trigger | All branches, prerequisites or effects to verify | RTM / gap |
| --- | --- | --- | --- |
| WF-D01 | Entry P D.0–2.1 | From M new WPS/essential-variable development; nonessential change not automatically requalification | R38; B20 |
| WF-D02 | Joint requirements P D.2.2 | Define metals/thickness/filler/geometry/required weld size-strength; development basis distinct from production approval | R38; B12/B14 |
| WF-D03 | A prerequisite P D.2.3 | Passing A first unless already current; return to D after A; unresolved A→H with correct context | R39; B05/B27 |
| WF-D04 | Trial P D.2.3/D.3 | Vary/record actual parameters and required tests; separate production-representative finishing development on scrap/coupons, not hardware | R39; B14 |
| WF-D05 | Criteria met? P D.2.4 | NO→adjust/repeat trials; YES→preliminary WPS; no testing away a production nonconformance by relabeling DEV | R39/R40; B14 |
| WF-D06 | Preliminary WPS P D.2.5 | Identify essential variables/ranges, supported evidence; proposed settings not qualified production ranges | R40 |
| WF-D07 | C P D.2.6 | Procedure qualification/approval then M START; development success alone never qualifies | R40/R31 |
| WF-D08 | Separation P D.3–5 | Trial source retained verbatim; development coupons/parts never production; lead identity/approval details B19 | R39/R40/R46 |

## Completeness conclusion and unresolved interaction paths

The inventory has **71 entries**: M15, A10, B15, C11, H12 and D8. Both outcomes are listed for each explicit yes/no decision, plus the Gate 2 pending outcome, named holds/escalations, all A/B/C callers and both H returns. This is a branch inventory; infinite loop/path combinations cannot be exhaustively enumerated. Later validation must execute every applicable outcome, all caller-return contexts, repeated/reentrant failures and the critical composite scenarios in the verification plan.

No additional explicit Rev C box or labeled branch was found missing from this inventory. We cannot yet claim a complete operational interpretation: initial missing qualification before Gate 1 (B03), early/partial B failures (B15), invalid replacement pending routes (B17), C/H-origin continuation (B18), nested H failures (B27), non-welding H A requirement (B28) and approved-disposition Gate 2 semantics (B29) still need definition. X03/X04 have user-approved design interpretations; source wording remains unchanged. D test applicability (B14/X05) and proposed proof test (B24/X06) remain unresolved. Owner exception semantics (A02) are separate from the ordinary chart.
