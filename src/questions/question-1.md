---
title: 1. Earning an A
---

# How does a restaurant earn its A, and how are first-inspection scores distributed?

Every violation adds points, and a score of 0 to 13 earns an A. This page shows how scores are spread out at first inspections, the routine unannounced visit that starts each inspection cycle, with the A cutoff marked.

```js
const scores = FileAttachment("/data/q1-scores.csv").csv({typed: true});
```

```js
display(Inputs.table(scores))
```
