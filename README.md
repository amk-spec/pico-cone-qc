# pico-cone-qc# PICOGRID LANDER — WELDING QUALITY CONTROL APPLICATION
## Initial Codex Project Instructions

### 1. Project Objective

Develop a standalone, secure, web-based Welding Quality Control (QC) application for the Picogrid Lander program.

The application will replace the existing complex Excel QC workbook with a streamlined, relational database-driven system that manages welding operations, qualifications, inspections, testing, Engineering Holds, nonconformances, approvals, and hardware release.

The primary users will be Picogrid and Cone Engineering. AM Kreations will serve as the system owner and administrator.

**This application is independent of ShopForge.**

The primary objectives are to:

- Eliminate redundant data entry through relational records.
- Simplify shop-floor quality documentation.
- Automatically associate relevant records, qualifications, and test results.
- Enforce the established welding QC workflow and approval authorities.
- Provide visibility into production status and outstanding actions.
- Maintain complete traceability and auditable quality records.
- Support collaboration between Picogrid, Cone Engineering, and AM Kreations.
- Minimize unnecessary administrative work without compromising required quality controls.

### 2. Governing Documents and Authority

The project has three primary source documents:

1. **Picogrid Lander Welding Quality Control Flowchart Rev C** — locked governing workflow and decision logic.
2. **Picogrid Lander Welding Procedure Rev A** — latest working master containing technical requirements and implementation details. Currently a discussion draft, not approved for production.
3. **Picogrid Welding QC Master Workbook** — existing record formats, fields, and operational data structures.

Before proceeding, confirm that all three documents are accessible and readable. Do not assume access to files from another ChatGPT conversation or Project.

The Rev C flowchart governs workflow routing and decision paths. The procedure provides the corresponding technical and operational requirements. The workbook is a reference for existing data and forms, not an independent authority to change governing requirements.

If documents conflict, identify the conflict and request clarification. Do not silently reconcile it.

Relevant AWS and ASTM standards may be used as references where identified in the governing documents. Do not introduce additional requirements without authorization.

### 3. Strict Engineering and Document-Control Rules

The following rules are mandatory:

1. Do not modify, reinterpret, simplify, bypass, or expand governing QC requirements.
2. Do not invent acceptance criteria, inspection frequencies, qualification requirements, approval authorities, or mandatory records.
3. Preserve all TBD items as unresolved engineering decisions.
4. Do not make autonomous engineering or hardware-disposition decisions.
5. Do not modify governing source documents without explicit authorization.
6. Do not treat an Engineering Hold as automatically requiring an NCR.
7. Do not treat successful development testing as production qualification.
8. Do not eliminate required verification or introduce unnecessary routine logging.
9. Do not assume completing an activity constitutes acceptance or authorization for release.
10. Do not allow software administrative privileges to override engineering approval authority.
11.
