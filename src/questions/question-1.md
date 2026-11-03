---
title: 1. Earning an A
---

# How does a restaurant earn its A, and how are first-inspection scores distributed?

Every violation adds points, and a score of 0 to 13 earns an A. This page shows how scores are spread out at first inspections, the routine unannounced visit that starts each inspection cycle, with the A cutoff marked.

## Data Transformation

**Goal:** Get an array of scores, each with their number of matching inspections.

1. Get `inspections` table and keep only first inspections by matching the `inspection_type` to "Cycle Inspection / Initial Inspection"
2. Group inspections by attribute `score` to get the count for each score
3. Fill in any score that has no inspection associated, this is important because many scores have no count and cause the charts to skip their bars. (e.g. Score 1 has 0 matches)

```js
const scores = FileAttachment("/data/q1-scores.csv").csv({typed: true});
```

## Inspections by Score

```js
display(Inputs.table(scores))
```

## Chart Sketch
A bar chart with x-axis representing the scores from 0 to 157 (apparently one restaurant has a score of 157) and a y-axis representing the number of inspections matching the scores.
