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
