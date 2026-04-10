# EDA Output Template

Use this template when the user asks for autonomous data exploration, source discovery, profiling, metric support analysis, joins, or data quality review.

Output contract:
- Use the exact markdown H2 section headings below.
- Keep the sections in the exact order shown below.
- Do not rename the headings.
- Do not replace the structure with custom headings or a single summary.

## EDA Summary
- One short paragraph on what business question is being explored and why it matters for the demo.

## Recommended Source Tables
- Table name, grain, and why it is needed.

## Join Path
- Explicit join keys in the order they should be used.

## Data Quality Checks
- Null, uniqueness, referential integrity, and business-rule checks relevant to the request.

## Metric Alignment
- Which metrics from the metric catalog are supported and what source fields drive them.

## Key Findings
- The most relevant observations, risks, or notable data patterns.

## Open Gaps
- Missing context, assumptions, or follow-up questions required before modeling or SQL execution.

Formatting rules:
- Stay grounded in the PRD, source catalog, metric catalog, and profiling metadata.
- Reference concrete tables, keys, and fields rather than generic statements.
- Keep the response concise and implementation-oriented.