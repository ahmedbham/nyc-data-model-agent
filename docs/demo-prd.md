# Demo PRD: Inpatient Readmission Analytics

## Objective

Enable hospital analytics teams to accelerate development of a reusable data product for 30-day readmission and length-of-stay reporting.

## Business Problem

The hospital system wants a faster path from business requirements to analytics-ready data products. Teams currently spend too much time translating PRDs into source discovery, metric definitions, logical models, and starter SQL.

## In-Scope Questions

1. Which departments and diagnoses have the highest 30-day readmission rate?
2. How does average length of stay vary by facility, department, diagnosis, and age group?
3. Which patient cohorts should be prioritized for care transition interventions?
4. What source data is required to support a readmission dashboard and self-service analysis?

## Users

- Data product manager.
- Analytics engineer.
- Data architect.
- Clinical operations analyst.

## Success Criteria

1. The agent identifies the relevant source tables and key joins.
2. The agent proposes a target dimensional model that supports dashboard and ad hoc analytics needs.
3. The agent generates valid starter DDL and DML for a dev-only target schema.
4. The resulting target model supports readmission rate and average length of stay metrics.

## Constraints

- Use synthetic, non-PHI sample data only.
- Assume dev-only execution for generated SQL.
- Keep the design compatible with Azure SQL Database.
- Require human approval between modeling and SQL execution.

## Target Outputs

- EDA report.
- Logical data model.
- Source-to-target data flow.
- Starter DDL for dimensions and fact tables.
- Starter transformation SQL for target fact population.
