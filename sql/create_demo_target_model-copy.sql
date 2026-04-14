IF OBJECT_ID('dbo.dim_patient', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.dim_patient (
        patient_key INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        patient_id VARCHAR(50) NOT NULL,
        mrn VARCHAR(50) NOT NULL,
        birth_date DATE NOT NULL,
        gender VARCHAR(20) NOT NULL,
        insurance_type VARCHAR(50) NOT NULL,
        zip_code VARCHAR(20) NOT NULL,
        CONSTRAINT UQ_dim_patient_patient_id UNIQUE (patient_id)
    );
END;

IF OBJECT_ID('dbo.dim_facility', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.dim_facility (
        facility_key INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        facility_id VARCHAR(50) NOT NULL,
        facility_name VARCHAR(200) NOT NULL,
        region VARCHAR(100) NULL,
        CONSTRAINT UQ_dim_facility_facility_id UNIQUE (facility_id)
    );
END;

IF OBJECT_ID('dbo.dim_department', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.dim_department (
        department_key INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        department_id VARCHAR(50) NOT NULL,
        facility_id VARCHAR(50) NOT NULL,
        department_name VARCHAR(200) NOT NULL,
        department_type VARCHAR(100) NULL,
        bed_count INT NULL,
        CONSTRAINT UQ_dim_department_department_id UNIQUE (department_id)
    );
END;

IF OBJECT_ID('dbo.dim_diagnosis', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.dim_diagnosis (
        diagnosis_key INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        icd10_code VARCHAR(20) NOT NULL,
        diagnosis_description VARCHAR(255) NULL,
        CONSTRAINT UQ_dim_diagnosis_icd10_code UNIQUE (icd10_code)
    );
END;

IF OBJECT_ID('dbo.dim_age_group', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.dim_age_group (
        age_group_key INT NOT NULL PRIMARY KEY,
        age_group_code VARCHAR(20) NOT NULL,
        age_group_label VARCHAR(50) NOT NULL,
        age_min INT NOT NULL,
        age_max INT NULL,
        CONSTRAINT UQ_dim_age_group_code UNIQUE (age_group_code)
    );
END;

IF OBJECT_ID('dbo.dim_date', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.dim_date (
        date_key INT NOT NULL PRIMARY KEY,
        date_value DATE NOT NULL,
        calendar_year INT NOT NULL,
        calendar_quarter INT NOT NULL,
        month_number INT NOT NULL,
        month_name VARCHAR(20) NOT NULL,
        day_of_month INT NOT NULL,
        CONSTRAINT UQ_dim_date_date_value UNIQUE (date_value)
    );
END;

IF OBJECT_ID('dbo.fact_encounter_outcomes', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.fact_encounter_outcomes (
        encounter_id VARCHAR(50) NOT NULL PRIMARY KEY,
        patient_key INT NOT NULL,
        facility_key INT NOT NULL,
        department_key INT NOT NULL,
        diagnosis_key INT NULL,
        age_group_key INT NOT NULL,
        admit_date_key INT NOT NULL,
        discharge_date_key INT NULL,
        admission_type VARCHAR(50) NULL,
        discharge_disposition VARCHAR(100) NULL,
        encounter_count INT NOT NULL,
        discharge_count INT NOT NULL,
        length_of_stay_days INT NULL,
        index_discharge_flag INT NOT NULL,
        readmission_30d_flag INT NOT NULL,
        readmission_count_30d INT NOT NULL,
        CONSTRAINT FK_fact_encounter_outcomes_patient FOREIGN KEY (patient_key) REFERENCES dbo.dim_patient(patient_key),
        CONSTRAINT FK_fact_encounter_outcomes_facility FOREIGN KEY (facility_key) REFERENCES dbo.dim_facility(facility_key),
        CONSTRAINT FK_fact_encounter_outcomes_department FOREIGN KEY (department_key) REFERENCES dbo.dim_department(department_key),
        CONSTRAINT FK_fact_encounter_outcomes_diagnosis FOREIGN KEY (diagnosis_key) REFERENCES dbo.dim_diagnosis(diagnosis_key),
        CONSTRAINT FK_fact_encounter_outcomes_age_group FOREIGN KEY (age_group_key) REFERENCES dbo.dim_age_group(age_group_key),
        CONSTRAINT FK_fact_encounter_outcomes_admit_date FOREIGN KEY (admit_date_key) REFERENCES dbo.dim_date(date_key),
        CONSTRAINT FK_fact_encounter_outcomes_discharge_date FOREIGN KEY (discharge_date_key) REFERENCES dbo.dim_date(date_key)
    );
END;

INSERT INTO dbo.dim_age_group (age_group_key, age_group_code, age_group_label, age_min, age_max)
SELECT v.age_group_key, v.age_group_code, v.age_group_label, v.age_min, v.age_max
FROM (VALUES
    (1, '0_17', '0-17', 0, 17),
    (2, '18_34', '18-34', 18, 34),
    (3, '35_49', '35-49', 35, 49),
    (4, '50_64', '50-64', 50, 64),
    (5, '65_PLUS', '65+', 65, NULL)
) v(age_group_key, age_group_code, age_group_label, age_min, age_max)
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.dim_age_group d
    WHERE d.age_group_key = v.age_group_key
);

INSERT INTO dbo.dim_patient (patient_id, mrn, birth_date, gender, insurance_type, zip_code)
SELECT p.patient_id, p.mrn, p.birth_date, p.gender, p.insurance_type, p.zip_code
FROM patients p
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.dim_patient d
    WHERE d.patient_id = p.patient_id
);

INSERT INTO dbo.dim_facility (facility_id, facility_name, region)
SELECT f.facility_id, f.facility_name, f.region
FROM facilities f
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.dim_facility d
    WHERE d.facility_id = f.facility_id
);

INSERT INTO dbo.dim_department (department_id, facility_id, department_name, department_type, bed_count)
SELECT d.department_id, d.facility_id, d.department_name, d.department_type, d.bed_count
FROM departments d
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.dim_department x
    WHERE x.department_id = d.department_id
);

INSERT INTO dbo.dim_diagnosis (icd10_code, diagnosis_description)
SELECT dx.icd10_code, MAX(dx.diagnosis_description) AS diagnosis_description
FROM diagnoses dx
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.dim_diagnosis d
    WHERE d.icd10_code = dx.icd10_code
)
GROUP BY dx.icd10_code;

WITH date_seed AS (
    SELECT admit_date AS dt
    FROM encounters
    WHERE admit_date IS NOT NULL
    UNION
    SELECT discharge_date AS dt
    FROM encounters
    WHERE discharge_date IS NOT NULL
)
INSERT INTO dbo.dim_date (
    date_key,
    date_value,
    calendar_year,
    calendar_quarter,
    month_number,
    month_name,
    day_of_month
)
SELECT
    (YEAR(ds.dt) * 10000) + (MONTH(ds.dt) * 100) + DAY(ds.dt) AS date_key,
    ds.dt AS date_value,
    YEAR(ds.dt) AS calendar_year,
    DATEPART(QUARTER, ds.dt) AS calendar_quarter,
    MONTH(ds.dt) AS month_number,
    DATENAME(MONTH, ds.dt) AS month_name,
    DAY(ds.dt) AS day_of_month
FROM date_seed ds
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.dim_date d
    WHERE d.date_value = ds.dt
);

WITH primary_diagnosis AS (
    SELECT
        dx.encounter_id,
        dx.icd10_code,
        dx.diagnosis_description
    FROM diagnoses dx
    WHERE dx.is_primary = 1
),
encounter_enriched AS (
    SELECT
        e.encounter_id,
        e.patient_id,
        e.facility_id,
        e.department_id,
        e.admit_date,
        e.discharge_date,
        e.admission_type,
        e.discharge_disposition,
        p.birth_date,
        pd.icd10_code,
        CASE
            WHEN DATEDIFF(YEAR, p.birth_date, e.admit_date)
                 - CASE
                     WHEN DATEFROMPARTS(YEAR(e.admit_date), MONTH(p.birth_date), DAY(p.birth_date)) > e.admit_date THEN 1
                     ELSE 0
                   END BETWEEN 0 AND 17 THEN 1
            WHEN DATEDIFF(YEAR, p.birth_date, e.admit_date)
                 - CASE
                     WHEN DATEFROMPARTS(YEAR(e.admit_date), MONTH(p.birth_date), DAY(p.birth_date)) > e.admit_date THEN 1
                     ELSE 0
                   END BETWEEN 18 AND 34 THEN 2
            WHEN DATEDIFF(YEAR, p.birth_date, e.admit_date)
                 - CASE
                     WHEN DATEFROMPARTS(YEAR(e.admit_date), MONTH(p.birth_date), DAY(p.birth_date)) > e.admit_date THEN 1
                     ELSE 0
                   END BETWEEN 35 AND 49 THEN 3
            WHEN DATEDIFF(YEAR, p.birth_date, e.admit_date)
                 - CASE
                     WHEN DATEFROMPARTS(YEAR(e.admit_date), MONTH(p.birth_date), DAY(p.birth_date)) > e.admit_date THEN 1
                     ELSE 0
                   END BETWEEN 50 AND 64 THEN 4
            ELSE 5
        END AS age_group_key,
        CASE
            WHEN e.discharge_date IS NOT NULL THEN DATEDIFF(DAY, e.admit_date, e.discharge_date)
            ELSE NULL
        END AS length_of_stay_days,
        CASE
            WHEN e.discharge_date IS NOT NULL THEN 1
            ELSE 0
        END AS discharge_count,
        CASE
            WHEN e.discharge_date IS NOT NULL THEN 1
            ELSE 0
        END AS index_discharge_flag,
        CASE
            WHEN e.discharge_date IS NOT NULL
                 AND EXISTS (
                    SELECT 1
                    FROM encounters e2
                    WHERE e2.patient_id = e.patient_id
                      AND e2.admit_date > e.discharge_date
                      AND e2.admit_date <= DATEADD(DAY, 30, e.discharge_date)
                 )
            THEN 1
            ELSE 0
        END AS readmission_30d_flag
    FROM encounters e
    INNER JOIN patients p
        ON p.patient_id = e.patient_id
    LEFT JOIN primary_diagnosis pd
        ON pd.encounter_id = e.encounter_id
)
INSERT INTO dbo.fact_encounter_outcomes (
    encounter_id,
    patient_key,
    facility_key,
    department_key,
    diagnosis_key,
    age_group_key,
    admit_date_key,
    discharge_date_key,
    admission_type,
    discharge_disposition,
    encounter_count,
    discharge_count,
    length_of_stay_days,
    index_discharge_flag,
    readmission_30d_flag,
    readmission_count_30d
)
SELECT
    ee.encounter_id,
    dp.patient_key,
    df.facility_key,
    dd.department_key,
    dx.diagnosis_key,
    ee.age_group_key,
    (YEAR(ee.admit_date) * 10000) + (MONTH(ee.admit_date) * 100) + DAY(ee.admit_date) AS admit_date_key,
    CASE
        WHEN ee.discharge_date IS NOT NULL THEN (YEAR(ee.discharge_date) * 10000) + (MONTH(ee.discharge_date) * 100) + DAY(ee.discharge_date)
        ELSE NULL
    END AS discharge_date_key,
    ee.admission_type,
    ee.discharge_disposition,
    1 AS encounter_count,
    ee.discharge_count,
    ee.length_of_stay_days,
    ee.index_discharge_flag,
    ee.readmission_30d_flag,
    ee.readmission_30d_flag AS readmission_count_30d
FROM encounter_enriched ee
INNER JOIN dbo.dim_patient dp
    ON dp.patient_id = ee.patient_id
INNER JOIN dbo.dim_facility df
    ON df.facility_id = ee.facility_id
INNER JOIN dbo.dim_department dd
    ON dd.department_id = ee.department_id
LEFT JOIN dbo.dim_diagnosis dx
    ON dx.icd10_code = ee.icd10_code
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.fact_encounter_outcomes f
    WHERE f.encounter_id = ee.encounter_id
);

SELECT COUNT(*) AS patient_dim_rows FROM dbo.dim_patient;
SELECT COUNT(*) AS facility_dim_rows FROM dbo.dim_facility;
SELECT COUNT(*) AS department_dim_rows FROM dbo.dim_department;
SELECT COUNT(*) AS diagnosis_dim_rows FROM dbo.dim_diagnosis;
SELECT COUNT(*) AS date_dim_rows FROM dbo.dim_date;
SELECT COUNT(*) AS fact_rows FROM dbo.fact_encounter_outcomes;

SELECT
    SUM(encounter_count) AS encounter_count,
    SUM(discharge_count) AS discharge_count,
    SUM(readmission_count_30d) AS readmission_count_30d,
    AVG(CAST(length_of_stay_days AS DECIMAL(10,2))) AS average_length_of_stay
FROM dbo.fact_encounter_outcomes;

SELECT
    fct.facility_key,
    dept.department_name,
    diag.icd10_code,
    ag.age_group_label,
    SUM(fct.index_discharge_flag) AS index_discharges,
    SUM(fct.readmission_30d_flag) AS readmissions_30d,
    CASE
        WHEN SUM(fct.index_discharge_flag) = 0 THEN NULL
        ELSE CAST(SUM(fct.readmission_30d_flag) AS DECIMAL(10,4)) / SUM(fct.index_discharge_flag)
    END AS readmission_rate_30d
FROM dbo.fact_encounter_outcomes fct
LEFT JOIN dbo.dim_department dept
    ON dept.department_key = fct.department_key
LEFT JOIN dbo.dim_diagnosis diag
    ON diag.diagnosis_key = fct.diagnosis_key
LEFT JOIN dbo.dim_age_group ag
    ON ag.age_group_key = fct.age_group_key
GROUP BY
    fct.facility_key,
    dept.department_name,
    diag.icd10_code,
    ag.age_group_label
ORDER BY
    readmission_rate_30d DESC;

SELECT
    encounter_id,
    length_of_stay_days,
    index_discharge_flag,
    readmission_30d_flag
FROM dbo.fact_encounter_outcomes
ORDER BY encounter_id;
