---
title: 3. Scores by cuisine
---

# How much do scores differ by cuisine?

The median and spread of first-inspection scores for the 20 most common cuisines. A first inspection is the routine unannounced visit that starts each inspection cycle, so every restaurant is checked the same way.

## Data Transformation

**Goal:** For each of the 20 most common cuisines, get the numbers needed for a box plot of first-inspection scores: the number of inspections, the quartiles and the whiskers.

1. Get the `inspections` table and keep only first inspections ("Cycle Inspection / Initial Inspection") that have a score, same as Q1.
2. Join with the `restaurants` table on `camis` to get each restaurant's `cuisine_description`. Keep only `restaurants` with a non-null `cuisine_description`
3. Keep the 20 cuisines with the most first inspections
4. Group by `cuisine_description` and calculate `count` (number of inspections), `percentile_25`, `median` and `percentile_75`
5. Calculate the whiskers with the 1.5 × interquartile range rule, where the interquartile range is `percentile_75 - percentile_25`. `whisker_high` is the highest score that is still at most `percentile_75 + 1.5 × interquartile range`, and `whisker_low` is the lowest score that is at least `percentile_25 - 1.5 × interquartile range` (always 0 here). Scores outside the whiskers are not stored, since some go above 100 and would squash the boxes
6. Sort by median

```js
const cuisines = FileAttachment("/data/q3-cuisines.csv").csv({typed: true});
```

## Scores by Cuisine

```js
display(Inputs.table(cuisines))
```

## Chart Sketch
