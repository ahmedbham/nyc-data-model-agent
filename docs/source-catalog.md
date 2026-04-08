# Demo Source Catalog

## Source Tables

### patients
- Grain: one row per patient.
- Primary key: `patient_id`.
- Purpose: demographic context for cohorts and age grouping.

Columns:
- `patient_id`
- `mrn`
- `birth_date`
- `gender`
- `insurance_type`
- `zip_code`

### encounters
- Grain: one row per inpatient encounter.
- Primary key: `encounter_id`.
- Foreign key: `patient_id` to `patients.patient_id`.
- Purpose: admissions, discharges, department routing, and encounter-level measures.

Columns:
- `encounter_id`
- `patient_id`
- `facility_id`
- `department_id`
- `admit_date`
- `discharge_date`
- `admission_type`
- `discharge_disposition`

### diagnoses
- Grain: one row per diagnosis assigned to an encounter.
- Primary key: composite of `encounter_id`, `diagnosis_sequence`.
- Foreign key: `encounter_id` to `encounters.encounter_id`.
- Purpose: primary diagnosis selection and comorbidity grouping.

Columns:
- `encounter_id`
- `diagnosis_sequence`
- `icd10_code`
- `diagnosis_description`
- `is_primary`

### departments
- Grain: one row per department.
- Primary key: `department_id`.
- Purpose: reporting hierarchy and bed capacity context.

Columns:
- `department_id`
- `facility_id`
- `department_name`
- `department_type`
- `bed_count`

### facilities
- Grain: one row per facility.
- Primary key: `facility_id`.
- Purpose: top-level hospital location grouping.

Columns:
- `facility_id`
- `facility_name`
- `region`

## Recommended Joins

1. `patients.patient_id = encounters.patient_id`
2. `encounters.encounter_id = diagnoses.encounter_id`
3. `departments.department_id = encounters.department_id`
4. `facilities.facility_id = encounters.facility_id`

## Candidate Target Model

- Fact table: `fact_encounter_outcomes`
- Dimensions: `dim_patient`, `dim_date`, `dim_department`, `dim_facility`, `dim_diagnosis`
