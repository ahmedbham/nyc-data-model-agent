Using the inpatient readmission analytics demo context, complete this request in three phases: EDA, target modeling, and starter SQL generation.

Phase requirements:
1. First produce the EDA output using the exact section headings and order from the repo's EDA output template.
2. Then produce the target model output using the exact section headings and order from the repo's model output template.
3. Then produce Azure SQL starter SQL using the exact section headings and order from the repo's SQL output template.

Business objective:
Create an analytics-ready dimensional model for 30-day readmission and length-of-stay reporting that supports both dashboarding and self-service analysis.

Source tables:
- patients
- encounters
- diagnoses
- departments
- facilities

Required joins:
- patients.patient_id = encounters.patient_id
- encounters.encounter_id = diagnoses.encounter_id
- departments.department_id = encounters.department_id
- facilities.facility_id = encounters.facility_id

Metrics to support:
- readmission_rate_30d
- average_length_of_stay
- encounter_count
- discharge_count
- readmission_count_30d

Business rules:
- Only inpatient encounters are in scope.
- Readmission matching uses patient identity and a subsequent inpatient admission within 30 days of discharge.
- Primary diagnosis comes from the diagnosis row where is_primary = 1.
- Age group is derived from patient birth date as of admit date.

Modeling expectations:
- Propose a dimensional model with explicit fact grain.
- Keep fact tables and dimensions separate.
- Include metric-to-model mapping.
- Include a source-to-target transformation flow.
- Call out assumptions and tradeoffs, especially around readmission logic, diagnosis handling, and age grouping.
- Keep the design compatible with Azure SQL Database.

SQL expectations:
- Generate Azure SQL compatible DDL, transformation SQL, and validation queries.
- Keep SQL dev-only.
- Do not include server-level administration statements, EXEC or EXECUTE, or system-database switching.
- Include SELECT-based validation queries.
- State clearly that human approval is required before execution.
- Include the validation command the user must run before execution.

Output expectations:
- Keep each phase clearly separated.
- Do not skip open gaps or design decisions.
- Do not execute anything.