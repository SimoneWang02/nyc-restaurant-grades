---
title: 2. A grades by neighborhood
---

# How much does the share of A grades vary by borough and neighborhood?

A map of New York showing the share of restaurants with an A in each neighborhood. Zoom in from boroughs to neighborhoods to see where an A is more or less common.

```js
const boroughs = FileAttachment("/data/q2-boro.csv").csv({typed: true});
const nta = FileAttachment("/data/q2-nta.csv").csv({typed: true});
```

```js
display(Inputs.table(boroughs))
```

```js
display(Inputs.table(nta))
```
