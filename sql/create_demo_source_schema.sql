CREATE TABLE facilities (
    facility_id INT PRIMARY KEY,
    facility_name VARCHAR(100) NOT NULL,
    region VARCHAR(50) NOT NULL
);

CREATE TABLE departments (
    department_id INT PRIMARY KEY,
    facility_id INT NOT NULL,
    department_name VARCHAR(100) NOT NULL,
    department_type VARCHAR(50) NOT NULL,
    bed_count INT NOT NULL,
    CONSTRAINT fk_departments_facility FOREIGN KEY (facility_id) REFERENCES facilities (facility_id)
);

CREATE TABLE patients (
    patient_id VARCHAR(20) PRIMARY KEY,
    mrn VARCHAR(20) NOT NULL,
    birth_date DATE NOT NULL,
    gender CHAR(1) NOT NULL,
    insurance_type VARCHAR(50) NOT NULL,
    zip_code VARCHAR(10) NOT NULL
);

CREATE TABLE encounters (
    encounter_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    facility_id INT NOT NULL,
    department_id INT NOT NULL,
    admit_date DATE NOT NULL,
    discharge_date DATE NOT NULL,
    admission_type VARCHAR(20) NOT NULL,
    discharge_disposition VARCHAR(50) NOT NULL,
    CONSTRAINT fk_encounters_patient FOREIGN KEY (patient_id) REFERENCES patients (patient_id),
    CONSTRAINT fk_encounters_facility FOREIGN KEY (facility_id) REFERENCES facilities (facility_id),
    CONSTRAINT fk_encounters_department FOREIGN KEY (department_id) REFERENCES departments (department_id)
);

CREATE TABLE diagnoses (
    encounter_id VARCHAR(20) NOT NULL,
    diagnosis_sequence INT NOT NULL,
    icd10_code VARCHAR(10) NOT NULL,
    diagnosis_description VARCHAR(200) NOT NULL,
    is_primary BIT NOT NULL,
    CONSTRAINT pk_diagnoses PRIMARY KEY (encounter_id, diagnosis_sequence),
    CONSTRAINT fk_diagnoses_encounter FOREIGN KEY (encounter_id) REFERENCES encounters (encounter_id)
);
