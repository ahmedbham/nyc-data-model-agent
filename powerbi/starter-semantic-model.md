# Starter Semantic Model Mapping

## Model Objective

This semantic model maps the Azure SQL target schema into a Power BI star schema for the live demo. It is intentionally small and optimized for import-mode reporting.

## Tables To Import

## Fact Table
- `fact_encounter_outcomes`
  - Keys: `encounter_id`, `patient_key`, `facility_key`, `department_key`, `diagnosis_key`
  - Measures source columns: `length_of_stay_days`, `encounter_count`, `discharge_count`, `readmission_30d_flag`
  - Date columns: `admit_date`, `discharge_date`

## Dimension Tables
- `dim_patient`
  - Business attributes: `age_group`, `gender`, `insurance_type`, `zip_code`
  - Hide in report view: `patient_key`, `patient_id`, `is_current`
- `dim_facility`
  - Business attributes: `facility_name`, `region`
  - Hide in report view: `facility_key`, `facility_id`
- `dim_department`
  - Business attributes: `department_name`, `department_type`, `bed_count`
  - Hide in report view: `department_key`, `department_id`, `facility_id`
- `dim_diagnosis`
  - Business attributes: `icd10_code`, `diagnosis_description`
  - Hide in report view: `diagnosis_key`

## Relationships

- `fact_encounter_outcomes[patient_key]` many-to-one to `dim_patient[patient_key]`
- `fact_encounter_outcomes[facility_key]` many-to-one to `dim_facility[facility_key]`
- `fact_encounter_outcomes[department_key]` many-to-one to `dim_department[department_key]`
- `fact_encounter_outcomes[diagnosis_key]` many-to-one to `dim_diagnosis[diagnosis_key]`

Relationship settings:
- Cross-filter direction: single
- Active relationships: all four
- Assume referential integrity: enabled only if DirectQuery is used later

## Date Modeling

The target schema does not currently include `dim_date`, so create a Power BI date table for reporting.

Suggested calculated table:

```DAX
Date =
ADDCOLUMNS (
    CALENDAR ( MIN ( fact_encounter_outcomes[admit_date] ), MAX ( fact_encounter_outcomes[discharge_date] ) ),
    "Year", YEAR ( [Date] ),
    "Month Number", MONTH ( [Date] ),
    "Month Name", FORMAT ( [Date], "MMM" ),
    "Year Month", FORMAT ( [Date], "YYYY-MM" )
)
```

Recommended active relationship:
- `Date[Date]` one-to-many to `fact_encounter_outcomes[discharge_date]`

Recommended inactive relationship:
- `Date[Date]` one-to-many to `fact_encounter_outcomes[admit_date]`

## Starter Measures

```DAX
Encounter Count = SUM ( fact_encounter_outcomes[encounter_count] )

Discharge Count = SUM ( fact_encounter_outcomes[discharge_count] )

Readmission Count 30d = SUM ( fact_encounter_outcomes[readmission_30d_flag] )

Readmission Rate 30d = DIVIDE ( [Readmission Count 30d], [Discharge Count] )

Average Length of Stay = AVERAGE ( fact_encounter_outcomes[length_of_stay_days] )

Average Length of Stay Weighted =
DIVIDE (
    SUMX (
        fact_encounter_outcomes,
        fact_encounter_outcomes[length_of_stay_days] * fact_encounter_outcomes[encounter_count]
    ),
    [Encounter Count]
)
```

## Field Placement Guidance

Use in slicers:
- `dim_facility[facility_name]`
- `dim_department[department_name]`
- `dim_diagnosis[diagnosis_description]`
- `dim_patient[age_group]`
- `dim_patient[gender]`
- `dim_patient[insurance_type]`

Use in drill-down hierarchies:
- Facility hierarchy: `region` > `facility_name`
- Department hierarchy: `department_type` > `department_name`
- Diagnosis hierarchy: `icd10_code` > `diagnosis_description`

## Model Hygiene

- Hide all surrogate keys from report consumers.
- Format `Readmission Rate 30d` as percentage with one decimal place.
- Format `Average Length of Stay` as decimal with one decimal place.
- Mark the `Date` table as a date table.
- Disable auto date/time for the file.
- Use import mode for the demo unless a later requirement calls for DirectQuery.