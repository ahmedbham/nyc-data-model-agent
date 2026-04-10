# Target Model Output Template

Use this template when the user asks for a target data model, dimensional design, data flow, source-to-target mapping, or analytics model proposal.

Output contract:
- Use the exact markdown H2 section headings below.
- Keep the sections in the exact order shown below.
- Do not rename the headings.
- Do not merge fact, dimension, and metric sections together.

## Model Objective
- One short paragraph tying the model to the business problem and target questions.

## Proposed Grain
- State the fact grain clearly.

## Fact Tables
- Fact table name, business process, core measures, and grain.

## Dimensions
- Dimension name, business purpose, natural key, surrogate key recommendation, and notable attributes.

## Metric Mapping
- Map each requested metric to the fact and dimension structures that support it.

## Source-to-Target Flow
- Ordered transformation steps from source tables to target tables.

## Design Decisions
- Explicit assumptions, tradeoffs, and any design constraints tied to Azure SQL compatibility.

## Approval Gate
- Remind the user that human approval is required before SQL generation or execution.

Formatting rules:
- Prefer dimensional modeling language with explicit grain and conformed dimensions.
- Keep facts and dimensions separate.
- Call out where primary diagnosis, age group, and readmission logic are derived.