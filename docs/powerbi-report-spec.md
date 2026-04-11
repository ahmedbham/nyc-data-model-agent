# Power BI Report Specification

## Purpose

This report is the business-facing layer for the hospital data model demo. It should show that the agent-generated target schema can support readmission and length-of-stay reporting with a simple, credible semantic model.

## Data Source

- Azure SQL Database
- Tables: `dim_patient`, `dim_facility`, `dim_department`, `dim_diagnosis`, `fact_encounter_outcomes`
- Refresh mode: Import for the live demo

## Demo Story

1. Show the agent identifying source tables and target model structure.
2. Show the SQL validation and approval gate.
3. Execute the target model load into Azure SQL.
4. Refresh Power BI.
5. Walk through readmission and length-of-stay insights by facility, department, diagnosis, and age group.

## Report Pages

## Executive Overview
- KPI card: `Readmission Rate 30d`
- KPI card: `Average Length of Stay`
- KPI card: `Encounter Count`
- Clustered bar chart: readmission rate by facility
- Clustered bar chart: average length of stay by department
- Slicers: facility, department, age group, diagnosis description

## Readmission Analysis
- Matrix: facility, department, diagnosis description with readmission count, discharge count, readmission rate
- Bar chart: top diagnoses by readmission count
- Bar chart: readmission rate by age group
- Table: encounter detail drill-through fields for spot checks

## Length of Stay Analysis
- Bar chart: average LOS by department
- Bar chart: average LOS by facility
- Matrix: diagnosis description by age group with average LOS and encounter count
- Table: recent encounters with admit date, discharge date, LOS, readmission flag

## Cohort Detail
- Stacked column chart: encounter count by insurance type and age group
- Matrix: facility and department by insurance type with encounter count
- Table: patient demographic slice using age group, gender, insurance type, zip code

## Required Slicers

- Facility name
- Department name
- Diagnosis description
- Age group
- Gender
- Insurance type

## Visual Design Guidance

- Keep the demo to three report pages plus one detail page.
- Use clean healthcare-friendly styling with neutral colors and one accent color for readmission-related measures.
- Show the same slicers across overview and detail pages for a consistent demo flow.
- Prefer labels and sorted visuals over decorative formatting.

## Acceptance Criteria

- The report refreshes successfully from the Azure SQL target schema.
- The KPI cards match the validation query outputs from the target-model execution script.
- A presenter can answer the PRD questions on readmissions and LOS using the report without leaving Power BI.
- The report exposes the dimensional design clearly enough to support drill-down by facility, department, diagnosis, and age group.