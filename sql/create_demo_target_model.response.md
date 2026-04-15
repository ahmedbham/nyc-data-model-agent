## EDA Summary
This exploration identifies the synthetic source tables, joins, and data quality considerations needed to support a dimensional model for 30-day readmission and average length-of-stay reporting. It matters for the demo because the target outputs require a reliable path from source discovery to metric-ready modeling and starter SQL.

## Recommended Source Tables
- `encounters` — grain: one row per inpatient encounter; required as the core event table for admissions, discharges, facility/department attribution, length of stay, and readmission logic.
- `patients` — grain: one row per patient; required for patient-level linkage across encounters and for deriving age group as of admit date.
- `diagnoses` — grain: one row per diagnosis per encounter; required to identify the primary diagnosis using `is_primary = 1` and support diagnosis-level slicing.
- `departments` — grain: one row per department; required for department reporting attributes and department-level metric aggregation.
- `facilities` — grain: one row per facility; required for facility-level reporting and regional grouping.

## Join Path
1. `encounters.patient_id = patients.patient_id`
2. `encounters.encounter_id = diagnoses.encounter_id`
3. `encounters.department_id = departments.department_id`
4. `encounters.facility_id = facilities.facility_id`

Recommended modeling join usage:
- Start from `encounters`
- Left join primary diagnosis from `diagnoses` filtered to `is_primary = 1`
- Join `patients` for age derivation
- Join `departments` for department attributes
- Join `facilities` for facility attributes

## Data Quality Checks
- Null checks:
  - `patients.patient_id`, `patients.birth_date` should be non-null for age-group derivation.
  - `encounters.encounter_id`, `encounters.patient_id`, `encounters.admit_date` should be non-null.
  - `encounters.discharge_date` should be reviewed because LOS and discharge-based metrics require completed encounters.
  - `diagnoses.is_primary` and `diagnoses.icd10_code` should be reviewed for primary diagnosis support.
- Uniqueness checks:
  - `patients.patient_id` should be unique; profile indicates primary key.
  - `encounters.encounter_id` should be unique; profile indicates primary key.
  - `diagnoses (encounter_id, diagnosis_sequence)` should be unique; profile indicates composite primary key.
- Referential integrity checks:
  - `encounters.patient_id` must match `patients.patient_id`.
  - `encounters.department_id` must match `departments.department_id`.
  - `encounters.facility_id` must match `facilities.facility_id`.
  - `diagnoses.encounter_id` must match `encounters.encounter_id`.
- Business-rule checks:
  - Confirm only inpatient encounters are present or define filter logic using `admission_type` if non-inpatient values exist.
  - Confirm each encounter has at most one row with `is_primary = 1`; otherwise primary diagnosis assignment is ambiguous.
  - Validate `discharge_date >= admit_date` for LOS.
  - Validate readmission logic by sequencing encounters per `patient_id` and identifying next `admit_date` within 30 days after `discharge_date`.

## Metric Alignment
- `readmission_rate_30d`
  - Supported by `encounters.patient_id`, `encounters.admit_date`, `encounters.discharge_date`, `encounters.facility_id`, `encounters.department_id`, primary diagnosis from `diagnoses.is_primary = 1`, and age group from `patients.birth_date` as of admit date.
- `average_length_of_stay`
  - Supported by `encounters.admit_date` and `encounters.discharge_date` with grouping by facility, department, primary diagnosis, and age group.
- `encounter_count`
  - Supported by `encounters.encounter_id`, grouped by admit or reporting date plus facility and department.
- `discharge_count`
  - Supported by `encounters.encounter_id` where `discharge_date` is populated, grouped by discharge date plus facility and department.
- `readmission_count_30d`
  - Supported by encounter sequencing on `encounters.patient_id` plus date logic, with grouping by facility, department, and primary diagnosis.

## Key Findings
- The source catalog cleanly supports the demo target model using the five listed source tables only.
- Profiling shows small synthetic volumes: 8 patients, 10 encounters, 11 diagnoses, 6 departments, and 3 facilities.
- `encounters` is the natural driving table for the fact model and already aligns to candidate measures: `length_of_stay_days`, `index_discharge_flag`, and `readmission_30d_flag`.
- Profiling notes confirm at least one known 30-day readmission scenario for patient `P001`, which is useful for validation.
- Diagnosis handling is the main modeling risk because encounter-level analytics require a single primary diagnosis row.

## Open Gaps
- The source profile does not confirm whether `admission_type` explicitly identifies inpatient rows; filtering may be required if mixed encounter types exist.
- No explicit null profile is provided for `encounters.discharge_date`; incomplete encounters may need exclusion from LOS and discharge-based metrics.
- The age-group bucket definitions are not specified in the provided artifacts; they must be assumed in modeling unless business provides standard bands.
- The source profile does not confirm whether every encounter has exactly one `is_primary = 1` diagnosis row.
- Before production hardening, business confirmation is needed on whether readmission attribution belongs to the index discharge encounter, the subsequent encounter, or both; for this demo, index encounter flagging is the safest assumption.

## Model Objective
The target model supports dashboarding and self-service analysis for 30-day readmission and length-of-stay reporting by organizing inpatient encounter outcomes into a dimensional structure that can answer questions by facility, department, primary diagnosis, date, and patient age group.

## Proposed Grain
- `fact_encounter_outcomes` grain: one row per inpatient encounter.

## Fact Tables
- `fact_encounter_outcomes`
  - Business process: inpatient admission and discharge outcome tracking.
  - Core measures:
    - `encounter_count`
    - `discharge_count`
    - `length_of_stay_days`
    - `index_discharge_flag`
    - `readmission_30d_flag`
    - `readmission_count_30d`
  - Grain: one row per inpatient encounter, with encounter-level keys to patient, admit date, discharge date, facility, department, and primary diagnosis.

## Dimensions
- `dim_patient`
  - Business purpose: patient demographic and cohort context for self-service slicing.
  - Natural key: `patient_id`
  - Surrogate key recommendation: `patient_key` as integer identity
  - Notable attributes: `mrn`, `birth_date`, `gender`, `insurance_type`, `zip_code`

- `dim_date`
  - Business purpose: reusable calendar dimension for admit and discharge reporting periods.
  - Natural key: `date_value`
  - Surrogate key recommendation: `date_key` as integer in `YYYYMMDD` format
  - Notable attributes: `date_value`, `calendar_year`, `calendar_month`, `month_name`, `day_of_month`

- `dim_department`
  - Business purpose: department-level reporting and operational slicing.
  - Natural key: `department_id`
  - Surrogate key recommendation: `department_key` as integer identity
  - Notable attributes: `facility_id`, `department_name`, `department_type`, `bed_count`

- `dim_facility`
  - Business purpose: facility and region-level grouping.
  - Natural key: `facility_id`
  - Surrogate key recommendation: `facility_key` as integer identity
  - Notable attributes: `facility_name`, `region`

- `dim_diagnosis`
  - Business purpose: primary diagnosis slicing for readmission and LOS analysis.
  - Natural key: `icd10_code`
  - Surrogate key recommendation: `diagnosis_key` as integer identity
  - Notable attributes: `icd10_code`, `diagnosis_description`

## Metric Mapping
- `readmission_rate_30d`
  - Supported by `fact_encounter_outcomes.index_discharge_flag` as denominator and `fact_encounter_outcomes.readmission_30d_flag` as numerator.
  - Dimensions used: `dim_date` (typically discharge month), `dim_facility`, `dim_department`, `dim_diagnosis`, derived age group stored on fact.
- `average_length_of_stay`
  - Supported by `fact_encounter_outcomes.length_of_stay_days` divided by completed encounter count.
  - Dimensions used: `dim_date` (admit or discharge period based on report), `dim_facility`, `dim_department`, `dim_diagnosis`, derived age group stored on fact.
- `encounter_count`
  - Supported by `fact_encounter_outcomes.encounter_count`.
  - Dimensions used: `dim_date`, `dim_facility`, `dim_department`.
- `discharge_count`
  - Supported by `fact_encounter_outcomes.discharge_count`.
  - Dimensions used: `dim_date` using discharge date, `dim_facility`, `dim_department`.
- `readmission_count_30d`
  - Supported by `fact_encounter_outcomes.readmission_30d_flag` or derived sum thereof.
  - Dimensions used: `dim_date`, `dim_facility`, `dim_department`, `dim_diagnosis`.

## Source-to-Target Flow
1. Extract `patients`, `encounters`, `diagnoses`, `departments`, and `facilities`.
2. Filter `encounters` to inpatient rows only if needed based on `admission_type`.
3. Derive primary diagnosis set from `diagnoses` where `is_primary = 1`.
4. Load `dim_patient` from `patients`.
5. Load `dim_facility` from `facilities`.
6. Load `dim_department` from `departments`.
7. Load `dim_diagnosis` from distinct primary diagnosis codes and descriptions.
8. Load `dim_date` from distinct admit and discharge dates in `encounters`.
9. Build an encounter staging set by joining `encounters` to `patients`, primary diagnosis, `departments`, and `facilities`.
10. Derive `length_of_stay_days` from `discharge_date - admit_date` for completed encounters.
11. Derive age at admit and assign age group from `patients.birth_date` relative to `encounters.admit_date`.
12. Sequence encounters by `patient_id` and `admit_date` to derive whether a subsequent encounter occurs within 30 days after discharge.
13. Populate `fact_encounter_outcomes` with surrogate keys, encounter identifiers, derived flags, and base measures.

## Design Decisions
- The fact table stays at encounter grain to support both dashboard metrics and ad hoc drill-down without requiring multiple summary facts.
- Primary diagnosis is modeled as a single encounter-level foreign key using `diagnoses.is_primary = 1`; secondary diagnoses are out of scope for this starter design.
- Age group is stored as a derived attribute on the fact because it depends on admit date and can vary by encounter even for the same patient.
- Readmission logic is assigned to the index discharge encounter using same-patient next admission within 30 days after discharge; this directly supports the metric catalog numerator/denominator.
- A single `dim_date` is reused for both admit and discharge date keys to keep the design simple and Azure SQL compatible.
- Age-group bands are assumed for demo purposes because the artifacts specify derivation logic but not bucket definitions.

## Approval Gate
Human approval is required before SQL generation or execution. The model design, especially readmission attribution, primary diagnosis handling, and age-group definitions, should be reviewed and approved before proceeding.

## SQL Objective
This SQL creates a dev-only dimensional model for inpatient encounter outcomes and populates dimensions and the encounter-level fact needed to support 30-day readmission and length-of-stay analytics.

## Approval Gate
This SQL is for a dev-only environment and requires human approval before execution. Model approval is required before running any generated SQL. Validate the SQL with `python app/validate_generated_sql.py --sql-file <path-to-sql> --target-environment dev --approved-by <name>` before any execution step.

## Target Objects
- `dbo.dim_patient`
- `dbo.dim_date`
- `dbo.dim_facility`
- `dbo.dim_department`
- `dbo.dim_diagnosis`
- `dbo.fact_encounter_outcomes`

## DDL
```sql
-- Dimension tables
CREATE TABLE dbo.dim_patient (
    patient_key INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL,
    mrn VARCHAR(50) NOT NULL,
    birth_date DATE NOT NULL,
    gender VARCHAR(50) NOT NULL,
    insurance_type VARCHAR(50) NOT NULL,
    zip_code VARCHAR(20) NOT NULL,
    CONSTRAINT uq_dim_patient_patient_id UNIQUE (patient_id)
);

CREATE TABLE dbo.dim_date (
    date_key INT NOT NULL PRIMARY KEY,
    date_value DATE NOT NULL,
    calendar_year INT NOT NULL,
    calendar_month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day_of_month INT NOT NULL,
    CONSTRAINT uq_dim_date_date_value UNIQUE (date_value)
);

CREATE TABLE dbo.dim_facility (
    facility_key INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    facility_id VARCHAR(50) NOT NULL,
    facility_name VARCHAR(200) NOT NULL,
    region VARCHAR(100) NOT NULL,
    CONSTRAINT uq_dim_facility_facility_id UNIQUE (facility_id)
);

CREATE TABLE dbo.dim_department (
    department_key INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    department_id VARCHAR(50) NOT NULL,
    facility_id VARCHAR(50) NOT NULL,
    department_name VARCHAR(200) NOT NULL,
    department_type VARCHAR(100) NOT NULL,
    bed_count INT NULL,
    CONSTRAINT uq_dim_department_department_id UNIQUE (department_id)
);

CREATE TABLE dbo.dim_diagnosis (
    diagnosis_key INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    icd10_code VARCHAR(20) NOT NULL,
    diagnosis_description VARCHAR(255) NOT NULL,
    CONSTRAINT uq_dim_diagnosis_icd10_code UNIQUE (icd10_code)
);

-- Fact table
CREATE TABLE dbo.fact_encounter_outcomes (
    encounter_id VARCHAR(50) NOT NULL PRIMARY KEY,
    patient_key INT NOT NULL,
    admit_date_key INT NOT NULL,
    discharge_date_key INT NULL,
    facility_key INT NOT NULL,
    department_key INT NOT NULL,
    diagnosis_key INT NULL,
    age_group VARCHAR(50) NOT NULL,
    admit_date DATE NOT NULL,
    discharge_date DATE NULL,
    length_of_stay_days INT NULL,
    encounter_count INT NOT NULL,
    discharge_count INT NOT NULL,
    index_discharge_flag INT NOT NULL,
    readmission_30d_flag INT NOT NULL,
    readmission_count_30d INT NOT NULL,
    CONSTRAINT fk_fact_patient FOREIGN KEY (patient_key) REFERENCES dbo.dim_patient(patient_key),
    CONSTRAINT fk_fact_admit_date FOREIGN KEY (admit_date_key) REFERENCES dbo.dim_date(date_key),
    CONSTRAINT fk_fact_discharge_date FOREIGN KEY (discharge_date_key) REFERENCES dbo.dim_date(date_key),
    CONSTRAINT fk_fact_facility FOREIGN KEY (facility_key) REFERENCES dbo.dim_facility(facility_key),
    CONSTRAINT fk_fact_department FOREIGN KEY (department_key) REFERENCES dbo.dim_department(department_key),
    CONSTRAINT fk_fact_diagnosis FOREIGN KEY (diagnosis_key) REFERENCES dbo.dim_diagnosis(diagnosis_key)
);
```

## Transformation SQL
```sql
-- Load dim_patient
INSERT INTO dbo.dim_patient (
    patient_id,
    mrn,
    birth_date,
    gender,
    insurance_type,
    zip_code
)
SELECT
    p.patient_id,
    p.mrn,
    p.birth_date,
    p.gender,
    p.insurance_type,
    p.zip_code
FROM patients p;

-- Load dim_facility
INSERT INTO dbo.dim_facility (
    facility_id,
    facility_name,
    region
)
SELECT
    f.facility_id,
    f.facility_name,
    f.region
FROM facilities f;

-- Load dim_department
INSERT INTO dbo.dim_department (
    department_id,
    facility_id,
    department_name,
    department_type,
    bed_count
)
SELECT
    d.department_id,
    d.facility_id,
    d.department_name,
    d.department_type,
    d.bed_count
FROM departments d;

-- Load dim_diagnosis from primary diagnoses only
INSERT INTO dbo.dim_diagnosis (
    icd10_code,
    diagnosis_description
)
SELECT DISTINCT
    dx.icd10_code,
    dx.diagnosis_description
FROM diagnoses dx
WHERE dx.is_primary = 1;

-- Load dim_date from admit and discharge dates
WITH distinct_dates AS (
    SELECT e.admit_date AS date_value
    FROM encounters e
    WHERE e.admit_date IS NOT NULL
    UNION
    SELECT e.discharge_date AS date_value
    FROM encounters e
    WHERE e.discharge_date IS NOT NULL
)
INSERT INTO dbo.dim_date (
    date_key,
    date_value,
    calendar_year,
    calendar_month,
    month_name,
    day_of_month
)
SELECT
    CAST(CONVERT(VARCHAR(8), dd.date_value, 112) AS INT) AS date_key,
    dd.date_value,
    YEAR(dd.date_value) AS calendar_year,
    MONTH(dd.date_value) AS calendar_month,
    DATENAME(MONTH, dd.date_value) AS month_name,
    DAY(dd.date_value) AS day_of_month
FROM distinct_dates dd;

-- Load fact_encounter_outcomes
WITH primary_diagnosis AS (
    SELECT
        dx.encounter_id,
        dx.icd10_code,
        dx.diagnosis_description
    FROM diagnoses dx
    WHERE dx.is_primary = 1
),
sequenced_encounters AS (
    SELECT
        e.encounter_id,
        e.patient_id,
        e.facility_id,
        e.department_id,
        e.admit_date,
        e.discharge_date,
        LEAD(e.admit_date) OVER (
            PARTITION BY e.patient_id
            ORDER BY e.admit_date, e.encounter_id
        ) AS next_admit_date
    FROM encounters e
),
fact_stage AS (
    SELECT
        e.encounter_id,
        e.patient_id,
        e.facility_id,
        e.department_id,
        e.admit_date,
        e.discharge_date,
        pd.icd10_code,
        DATEDIFF(YEAR, p.birth_date, e.admit_date)
            - CASE
                WHEN DATEFROMPARTS(YEAR(e.admit_date), MONTH(p.birth_date), DAY(p.birth_date)) > e.admit_date THEN 1
                ELSE 0
              END AS age_at_admit,
        CASE
            WHEN e.discharge_date IS NOT NULL THEN DATEDIFF(DAY, e.admit_date, e.discharge_date)
            ELSE NULL
        END AS length_of_stay_days,
        CASE
            WHEN e.discharge_date IS NOT NULL THEN 1 ELSE 0
        END AS discharge_count,
        CASE
            WHEN e.discharge_date IS NOT NULL THEN 1 ELSE 0
        END AS index_discharge_flag,
        CASE
            WHEN e.discharge_date IS NOT NULL
             AND se.next_admit_date IS NOT NULL
             AND se.next_admit_date > e.discharge_date
             AND se.next_admit_date <= DATEADD(DAY, 30, e.discharge_date)
            THEN 1 ELSE 0
        END AS readmission_30d_flag
    FROM encounters e
    INNER JOIN patients p
        ON e.patient_id = p.patient_id
    LEFT JOIN primary_diagnosis pd
        ON e.encounter_id = pd.encounter_id
    LEFT JOIN sequenced_encounters se
        ON e.encounter_id = se.encounter_id
)
INSERT INTO dbo.fact_encounter_outcomes (
    encounter_id,
    patient_key,
    admit_date_key,
    discharge_date_key,
    facility_key,
    department_key,
    diagnosis_key,
    age_group,
    admit_date,
    discharge_date,
    length_of_stay_days,
    encounter_count,
    discharge_count,
    index_discharge_flag,
    readmission_30d_flag,
    readmission_count_30d
)
SELECT
    fs.encounter_id,
    dp.patient_key,
    CAST(CONVERT(VARCHAR(8), fs.admit_date, 112) AS INT) AS admit_date_key,
    CASE
        WHEN fs.discharge_date IS NOT NULL
        THEN CAST(CONVERT(VARCHAR(8), fs.discharge_date, 112) AS INT)
        ELSE NULL
    END AS discharge_date_key,
    df.facility_key,
    dd.department_key,
    dx.diagnosis_key,
    CASE
        WHEN fs.age_at_admit < 18 THEN '0-17'
        WHEN fs.age_at_admit BETWEEN 18 AND 34 THEN '18-34'
        WHEN fs.age_at_admit BETWEEN 35 AND 49 THEN '35-49'
        WHEN fs.age_at_admit BETWEEN 50 AND 64 THEN '50-64'
        ELSE '65+'
    END AS age_group,
    fs.admit_date,
    fs.discharge_date,
    fs.length_of_stay_days,
    1 AS encounter_count,
    fs.discharge_count,
    fs.index_discharge_flag,
    fs.readmission_30d_flag,
    fs.readmission_30d_flag AS readmission_count_30d
FROM fact_stage fs
INNER JOIN dbo.dim_patient dp
    ON fs.patient_id = dp.patient_id
INNER JOIN dbo.dim_facility df
    ON fs.facility_id = df.facility_id
INNER JOIN dbo.dim_department dd
    ON fs.department_id = dd.department_id
LEFT JOIN dbo.dim_diagnosis dx
    ON fs.icd10_code = dx.icd10_code;
```

## Validation Queries
```sql
-- Row-count checks
SELECT 'patients_to_dim_patient' AS check_name, COUNT(*) AS row_count FROM dbo.dim_patient
UNION ALL
SELECT 'facilities_to_dim_facility', COUNT(*) FROM dbo.dim_facility
UNION ALL
SELECT 'departments_to_dim_department', COUNT(*) FROM dbo.dim_department
UNION ALL
SELECT 'fact_encounter_outcomes', COUNT(*) FROM dbo.fact_encounter_outcomes;

-- Validate one row per encounter in fact
SELECT
    encounter_id,
    COUNT(*) AS row_count
FROM dbo.fact_encounter_outcomes
GROUP BY encounter_id
HAVING COUNT(*) > 1;

-- Validate readmission flag counts
SELECT
    SUM(index_discharge_flag) AS index_discharges,
    SUM(readmission_30d_flag) AS readmission_30d_cases,
    SUM(readmission_count_30d) AS readmission_count_30d
FROM dbo.fact_encounter_outcomes;

-- Validate average LOS by facility and department
SELECT
    f.facility_name,
    d.department_name,
    AVG(CAST(feo.length_of_stay_days AS DECIMAL(10,2))) AS avg_length_of_stay
FROM dbo.fact_encounter_outcomes feo
INNER JOIN dbo.dim_facility f
    ON feo.facility_key = f.facility_key
INNER JOIN dbo.dim_department d
    ON feo.department_key = d.department_key
WHERE feo.length_of_stay_days IS NOT NULL
GROUP BY
    f.facility_name,
    d.department_name;

-- Validate known demo readmission scenario presence
SELECT
    dp.patient_id,
    feo.encounter_id,
    feo.discharge_date,
    feo.readmission_30d_flag
FROM dbo.fact_encounter_outcomes feo
INNER JOIN dbo.dim_patient dp
    ON feo.patient_key = dp.patient_key
WHERE dp.patient_id = 'P001';
```

## Validation Gate
Validation must be completed in a dev-only target with a named approver recorded, and no execution should occur until the validation step passes successfully.

## Execution Notes
- Assumes the source tables `patients`, `encounters`, `diagnoses`, `departments`, and `facilities` already exist in the target database and contain only synthetic demo data.
- Assumes inpatient scope is already satisfied by `encounters`; if not, add an `admission_type` filter once valid inpatient values are confirmed.
- Assumes one primary diagnosis row per encounter where `is_primary = 1`; records with multiple primary diagnoses are not resolved in this starter SQL.
- Uses encounter-level age grouping derived at admit date with assumed bands: `0-17`, `18-34`, `35-49`, `50-64`, `65+`.
- Readmission logic flags the index encounter when the next encounter for the same patient has `admit_date` within 30 days after `discharge_date`.
- This is starter SQL only; incremental loading, late-arriving dimensions, and production-grade error handling are intentionally left for later hardening.