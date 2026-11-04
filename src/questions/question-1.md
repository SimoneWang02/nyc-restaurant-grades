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
A bar chart with x-axis representing the scores from 0 to 157 (apparently one restaurant has a score of 157) and a y-axis representing the number of inspections matching the scores. Mark the A cutoff. Hovering a bar shows the count.

![Q1 sketch](../images/q1-sketch.jpeg)

<div class="note">
    <ul>
        <li>Why no restaurant has score equal to 1? Because each violation adds a certain score, and even the "lowest" violation is not worth 1.</li>
        <li>Why do so many restaurants score 13 and so few score 14? 13 is the highest score that still gets an A. With 14 or more, the restaurant does not get an A on that visit and has to be inspected again. Inspectors have some say in how many points each violation is worth, so a restaurant right at the line can end up at 13 instead of 14. That is the likely reason for the drop, but the data can't show it directly.</li>
    </ul>
</div>
