CREATE TABLE dim_patient (
    patient_key INT IDENTITY(1,1) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    age_group VARCHAR(20) NOT NULL,
    gender CHAR(1) NOT NULL,
    insurance_type VARCHAR(50) NOT NULL,
    zip_code VARCHAR(10) NOT NULL,
    is_current BIT NOT NULL DEFAULT 1
);

CREATE TABLE dim_facility (
    facility_key INT IDENTITY(1,1) PRIMARY KEY,
    facility_id INT NOT NULL,
    facility_name VARCHAR(100) NOT NULL,
    region VARCHAR(50) NOT NULL
);

CREATE TABLE dim_department (
    department_key INT IDENTITY(1,1) PRIMARY KEY,
    department_id INT NOT NULL,
    facility_id INT NOT NULL,
    department_name VARCHAR(100) NOT NULL,
    department_type VARCHAR(50) NOT NULL,
    bed_count INT NOT NULL
);

CREATE TABLE dim_diagnosis (
    diagnosis_key INT IDENTITY(1,1) PRIMARY KEY,
    icd10_code VARCHAR(10) NOT NULL,
    diagnosis_description VARCHAR(200) NOT NULL
);

CREATE TABLE fact_encounter_outcomes (
    encounter_id VARCHAR(20) PRIMARY KEY,
    patient_key INT NOT NULL,
    facility_key INT NOT NULL,
    department_key INT NOT NULL,
    diagnosis_key INT NOT NULL,
    admit_date DATE NOT NULL,
    discharge_date DATE NOT NULL,
    length_of_stay_days INT NOT NULL,
    encounter_count INT NOT NULL DEFAULT 1,
    discharge_count INT NOT NULL DEFAULT 1,
    readmission_30d_flag BIT NOT NULL,
    CONSTRAINT fk_fact_patient FOREIGN KEY (patient_key) REFERENCES dim_patient (patient_key),
    CONSTRAINT fk_fact_facility FOREIGN KEY (facility_key) REFERENCES dim_facility (facility_key),
    CONSTRAINT fk_fact_department FOREIGN KEY (department_key) REFERENCES dim_department (department_key),
    CONSTRAINT fk_fact_diagnosis FOREIGN KEY (diagnosis_key) REFERENCES dim_diagnosis (diagnosis_key)
);

WITH patient_age_groups AS (
    SELECT DISTINCT
        p.patient_id,
        CASE
            WHEN DATEDIFF(YEAR, p.birth_date, e.admit_date)
                - CASE
                    WHEN DATEFROMPARTS(YEAR(e.admit_date), MONTH(p.birth_date), DAY(p.birth_date)) > e.admit_date THEN 1
                    ELSE 0
                END < 18 THEN '0-17'
            WHEN DATEDIFF(YEAR, p.birth_date, e.admit_date)
                - CASE
                    WHEN DATEFROMPARTS(YEAR(e.admit_date), MONTH(p.birth_date), DAY(p.birth_date)) > e.admit_date THEN 1
                    ELSE 0
                END BETWEEN 18 AND 34 THEN '18-34'
            WHEN DATEDIFF(YEAR, p.birth_date, e.admit_date)
                - CASE
                    WHEN DATEFROMPARTS(YEAR(e.admit_date), MONTH(p.birth_date), DAY(p.birth_date)) > e.admit_date THEN 1
                    ELSE 0
                END BETWEEN 35 AND 49 THEN '35-49'
            WHEN DATEDIFF(YEAR, p.birth_date, e.admit_date)
                - CASE
                    WHEN DATEFROMPARTS(YEAR(e.admit_date), MONTH(p.birth_date), DAY(p.birth_date)) > e.admit_date THEN 1
                    ELSE 0
                END BETWEEN 50 AND 64 THEN '50-64'
            ELSE '65+'
        END AS age_group,
        p.gender,
        p.insurance_type,
        p.zip_code
    FROM patients AS p
    INNER JOIN encounters AS e
        ON e.patient_id = p.patient_id
)
MERGE dim_patient AS target
USING patient_age_groups AS source
ON target.patient_id = source.patient_id
AND target.age_group = source.age_group
WHEN MATCHED THEN
    UPDATE SET
        target.gender = source.gender,
        target.insurance_type = source.insurance_type,
        target.zip_code = source.zip_code,
        target.is_current = 1
WHEN NOT MATCHED THEN
    INSERT (patient_id, age_group, gender, insurance_type, zip_code, is_current)
    VALUES (source.patient_id, source.age_group, source.gender, source.insurance_type, source.zip_code, 1);

MERGE dim_facility AS target
USING (
    SELECT facility_id, facility_name, region
    FROM facilities
) AS source
ON target.facility_id = source.facility_id
WHEN MATCHED THEN
    UPDATE SET
        target.facility_name = source.facility_name,
        target.region = source.region
WHEN NOT MATCHED THEN
    INSERT (facility_id, facility_name, region)
    VALUES (source.facility_id, source.facility_name, source.region);

MERGE dim_department AS target
USING (
    SELECT department_id, facility_id, department_name, department_type, bed_count
    FROM departments
) AS source
ON target.department_id = source.department_id
WHEN MATCHED THEN
    UPDATE SET
        target.facility_id = source.facility_id,
        target.department_name = source.department_name,
        target.department_type = source.department_type,
        target.bed_count = source.bed_count
WHEN NOT MATCHED THEN
    INSERT (department_id, facility_id, department_name, department_type, bed_count)
    VALUES (source.department_id, source.facility_id, source.department_name, source.department_type, source.bed_count);

MERGE dim_diagnosis AS target
USING (
    SELECT DISTINCT icd10_code, diagnosis_description
    FROM diagnoses
    WHERE is_primary = 1
) AS source
ON target.icd10_code = source.icd10_code
WHEN MATCHED THEN
    UPDATE SET
        target.diagnosis_description = source.diagnosis_description
WHEN NOT MATCHED THEN
    INSERT (icd10_code, diagnosis_description)
    VALUES (source.icd10_code, source.diagnosis_description);

WITH encounter_base AS (
    SELECT
        e.encounter_id,
        e.patient_id,
        e.facility_id,
        e.department_id,
        e.admit_date,
        e.discharge_date,
        DATEDIFF(DAY, e.admit_date, e.discharge_date) AS length_of_stay_days,
        CASE
            WHEN DATEDIFF(YEAR, p.birth_date, e.admit_date)
                - CASE
                    WHEN DATEFROMPARTS(YEAR(e.admit_date), MONTH(p.birth_date), DAY(p.birth_date)) > e.admit_date THEN 1
                    ELSE 0
                END < 18 THEN '0-17'
            WHEN DATEDIFF(YEAR, p.birth_date, e.admit_date)
                - CASE
                    WHEN DATEFROMPARTS(YEAR(e.admit_date), MONTH(p.birth_date), DAY(p.birth_date)) > e.admit_date THEN 1
                    ELSE 0
                END BETWEEN 18 AND 34 THEN '18-34'
            WHEN DATEDIFF(YEAR, p.birth_date, e.admit_date)
                - CASE
                    WHEN DATEFROMPARTS(YEAR(e.admit_date), MONTH(p.birth_date), DAY(p.birth_date)) > e.admit_date THEN 1
                    ELSE 0
                END BETWEEN 35 AND 49 THEN '35-49'
            WHEN DATEDIFF(YEAR, p.birth_date, e.admit_date)
                - CASE
                    WHEN DATEFROMPARTS(YEAR(e.admit_date), MONTH(p.birth_date), DAY(p.birth_date)) > e.admit_date THEN 1
                    ELSE 0
                END BETWEEN 50 AND 64 THEN '50-64'
            ELSE '65+'
        END AS age_group,
        pd.icd10_code,
        CASE
            WHEN EXISTS (
                SELECT 1
                FROM encounters AS e_next
                WHERE e_next.patient_id = e.patient_id
                    AND e_next.admit_date > e.discharge_date
                    AND e_next.admit_date <= DATEADD(DAY, 30, e.discharge_date)
            ) THEN CAST(1 AS BIT)
            ELSE CAST(0 AS BIT)
        END AS readmission_30d_flag
    FROM encounters AS e
    INNER JOIN patients AS p
        ON p.patient_id = e.patient_id
    INNER JOIN diagnoses AS pd
        ON pd.encounter_id = e.encounter_id
        AND pd.is_primary = 1
)
MERGE fact_encounter_outcomes AS target
USING (
    SELECT
        eb.encounter_id,
        dp.patient_key,
        df.facility_key,
        dd.department_key,
        dx.diagnosis_key,
        eb.admit_date,
        eb.discharge_date,
        eb.length_of_stay_days,
        CAST(1 AS INT) AS encounter_count,
        CAST(1 AS INT) AS discharge_count,
        eb.readmission_30d_flag
    FROM encounter_base AS eb
    INNER JOIN dim_patient AS dp
        ON dp.patient_id = eb.patient_id
        AND dp.age_group = eb.age_group
    INNER JOIN dim_facility AS df
        ON df.facility_id = eb.facility_id
    INNER JOIN dim_department AS dd
        ON dd.department_id = eb.department_id
    INNER JOIN dim_diagnosis AS dx
        ON dx.icd10_code = eb.icd10_code
) AS source
ON target.encounter_id = source.encounter_id
WHEN MATCHED THEN
    UPDATE SET
        target.patient_key = source.patient_key,
        target.facility_key = source.facility_key,
        target.department_key = source.department_key,
        target.diagnosis_key = source.diagnosis_key,
        target.admit_date = source.admit_date,
        target.discharge_date = source.discharge_date,
        target.length_of_stay_days = source.length_of_stay_days,
        target.encounter_count = source.encounter_count,
        target.discharge_count = source.discharge_count,
        target.readmission_30d_flag = source.readmission_30d_flag
WHEN NOT MATCHED THEN
    INSERT (
        encounter_id,
        patient_key,
        facility_key,
        department_key,
        diagnosis_key,
        admit_date,
        discharge_date,
        length_of_stay_days,
        encounter_count,
        discharge_count,
        readmission_30d_flag
    )
    VALUES (
        source.encounter_id,
        source.patient_key,
        source.facility_key,
        source.department_key,
        source.diagnosis_key,
        source.admit_date,
        source.discharge_date,
        source.length_of_stay_days,
        source.encounter_count,
        source.discharge_count,
        source.readmission_30d_flag
    );

-- Validation queries for demo verification after the target model is created and populated.
SELECT 'dim_patient' AS table_name, COUNT(*) AS row_count FROM dim_patient
UNION ALL
SELECT 'dim_facility' AS table_name, COUNT(*) AS row_count FROM dim_facility
UNION ALL
SELECT 'dim_department' AS table_name, COUNT(*) AS row_count FROM dim_department
UNION ALL
SELECT 'dim_diagnosis' AS table_name, COUNT(*) AS row_count FROM dim_diagnosis
UNION ALL
SELECT 'fact_encounter_outcomes' AS table_name, COUNT(*) AS row_count FROM fact_encounter_outcomes;

SELECT
    COUNT(*) AS encounter_rows,
    SUM(encounter_count) AS encounter_count_total,
    SUM(discharge_count) AS discharge_count_total,
    SUM(CASE WHEN readmission_30d_flag = 1 THEN 1 ELSE 0 END) AS readmission_30d_total,
    AVG(CAST(length_of_stay_days AS DECIMAL(10, 2))) AS average_length_of_stay_days
FROM fact_encounter_outcomes;

SELECT TOP 10
    encounter_id,
    admit_date,
    discharge_date,
    length_of_stay_days,
    readmission_30d_flag
FROM fact_encounter_outcomes
ORDER BY discharge_date DESC, encounter_id;
