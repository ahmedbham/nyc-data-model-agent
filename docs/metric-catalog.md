# Demo Metric Catalog

## Metrics

### readmission_rate_30d
- Definition: percentage of discharged inpatient encounters followed by another inpatient encounter for the same patient within 30 days.
- Numerator: count of encounters where a qualifying readmission occurs within 30 days of discharge.
- Denominator: count of index discharges.
- Grain: month, facility, department, primary diagnosis, age group.

### average_length_of_stay
- Definition: average number of days between admit and discharge for completed inpatient encounters.
- Numerator: sum of encounter length of stay in days.
- Denominator: count of completed encounters.
- Grain: month, facility, department, primary diagnosis, age group.

### encounter_count
- Definition: count of inpatient encounters in the reporting period.
- Grain: day, month, facility, department.

### discharge_count
- Definition: count of inpatient encounters with a discharge date in the reporting period.
- Grain: day, month, facility, department.

### readmission_count_30d
- Definition: count of inpatient encounters that qualify as 30-day readmissions.
- Grain: month, facility, department, primary diagnosis.

## Shared Business Rules

1. Only inpatient encounters are in scope for the demo.
2. Readmission matching uses patient identity and admission date within 30 days of discharge.
3. Primary diagnosis is taken from the diagnosis row where `is_primary = 1`.
4. Age group is derived from patient birth date as of admit date.
