---
title: 5. Violations
---

# Which violations are cited most often, and what share are critical?

The proposal asked which violations "drive scores up". The data gives the total score of an inspection, yet not the points from each violation. So we count how often each code shows up and how many are critical.

```js
const info = FileAttachment("/data/q5-summary.json").json();
const codes = FileAttachment("/data/q5-code-summary.csv").csv({typed: true});
const flags = FileAttachment("/data/q5-critical-summary.csv").csv({typed: true});
```

## Data

We use **${d3.format(",")(info.inspections)} routine initial inspections** (Cycle Inspection / Initial Inspection) from ${info.start} to ${info.end}. They have ${d3.format(",")(info.violation_rows)} violation rows; after dropping ${info.duplicates_dropped} exact duplicates there are **${d3.format(",")(info.citations)} citations** across ${info.codes} codes.

We use the critical flag on each row. 09A has both flags.

## Critical share

```js
display(Inputs.table(flags, {
  select: false,
  columns: ["flag", "citations", "pct_citations"],
  header: {flag: "Flag", citations: "Citations", pct_citations: "% of citations"}
}));
```

## Most cited codes

```js
const show = view(Inputs.select(["Top 15", "All codes"], {label: "Show"}));
```

```js
display(Inputs.table(show === "Top 15" ? codes.slice(0, 15) : codes, {
  select: false,
  columns: ["code", "label", "citations", "critical", "not_critical", "pct_inspections"],
  header: {code: "Code", label: "Violation", citations: "Citations", critical: "Critical", not_critical: "Not Critical", pct_inspections: "% of inspections"},
  width: {code: 50, label: 260}
}));
```

One inspection can have many codes, so this column adds up to more than 100%.

## Simple analysis from the vision

${codes[0].code} (${codes[0].label}) is the most common one, it shows up in ${codes[0].pct_inspections}% of inspections. In total, ${flags.find(d => d.flag === "Critical").pct_citations}% of citations are critical.

## Planned chart

(placeholder)

Bars for the top 15 codes, sorted by count, and the x-axis starts at 0. Each bar is split into Critical and Not Critical. When you hover a bar, it shows the full description and the % of inspections. A toggle switches to all codes.
