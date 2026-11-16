---
title: 8. Closures and reopening
---

# Which restaurants get closed, and how long does it take them to reopen?

Inspectors can close a restaurant on the spot for a public health hazard, and it stays closed until a reopening inspection finds the problems fixed. This page follows every closure in the file to the reopening that ends it: how closures end, how many days restaurants stay closed, how often the first reopening attempt fails, and which violations are cited at the inspections that close them. A closing inspection lists the violations on file for that visit; the data don't say which one led to the closure.

```js
const matching = FileAttachment("/data/q8-matching.csv").csv({typed: true});
const jan = FileAttachment("/data/q8-jan2025.csv").csv({typed: true});
const violations = FileAttachment("/data/q8-violations.csv").csv({typed: true});
const daysClosed = FileAttachment("/data/q8-days-closed.csv").csv({typed: true});
const q8 = FileAttachment("/data/q8-summary.json").json();
```

```js
const fmt = d3.format(",");
const pct = d3.format(".1%");
const snapshotDate = q8.snapshot?.match(/\d{4}-\d{2}-\d{2}/)?.[0] ?? "2026-11-02";
```

## How the closures end

```js
display(closureOutcomes(matching, {width}));
```

Closures that began from ${q8.window_start} to ${q8.window_end}, the same window as the other questions. One bar for all closures, split by how each one ends. Gray parts have no reopening on file; their labels name the rule that applies, not the restaurant's real status. Hover a part for its count.

## How long restaurants stay closed

```js
display(daysClosedChart(daysClosed, q8, {width}));
```

Only closures with a recorded reopening. Solid: reopened at the first try. Hatched: reopened after at least one failed reopening attempt. The bins get wider to the right. Hover a part for its count.

## Violations cited at the closing inspection

```js
const topN = view(Inputs.radio([10, 15], {label: "Codes shown", value: 10, format: (d) => `Top ${d}`}));
```

```js
display(violationsChart(violations, q8, {top: topN, width}));
```

Bar: share of closing inspections that cite the code. Black tick: share of routine first inspections that cite it, for comparison. Codes are sorted by how many closing inspections cite them. Hover a row for the full description.

## What it shows

```js
const andList = (items) => new Intl.ListFormat("en-GB").format(items);   // "a, b and c"
const otherPhrase = {
  "No reopening on file (closed over 30 days before the end of follow-up)": "began more than 30 days before the end of follow-up and have no later graded inspection",
  "Closed again before a reopening record": "were followed by another closure",
  "Recent closure, no reopening on file (last 30 days)": "began in the last 30 days",
  "Inspected again without a reopening record": "were followed by a graded inspection",
};
const others = matching.filter((d) => d.status !== "Reopened");
const otherList = andList(others.map((d) => `${fmt(d.closures)} ${otherPhrase[d.status] ?? d.status}`));
const within14 = d3.sum(daysClosed.filter((d) => ["0 (same day)", "1", "2-3", "4-7", "8-14"].includes(String(d.days_closed))), (d) => d.count) / q8.n_reopened;
const describe = (d) => `${d.violation_code} (${shortLabel(d)}: ${pct(d.share_of_closures)} vs ${pct(d.share_of_first_inspections)})`;
const mostOver = d3.sort(violations, (d) => -d.share_of_closures / d.share_of_first_inspections).slice(0, 3).map(describe);
const lessAtClosure = violations.filter((d) => d.share_of_closures < d.share_of_first_inspections).map(describe);
```

- **Most closures end in a recorded reopening.** Of ${fmt(q8.n_closures)} closures at ${fmt(q8.n_restaurants)} restaurants, ${fmt(q8.n_reopened)} (${pct(q8.share_reopened)}) end in a recorded reopening. The other ${fmt(q8.n_closures - q8.n_reopened)} have no reopening on file: ${otherList}.
- **About a week, for closures that reopened.** Among the ${fmt(q8.n_reopened)} closures with a recorded reopening, the median closure lasted ${q8.median_days_closed} days (middle half: ${q8.p25_days_closed} to ${q8.p75_days_closed} days), and ${pct(within14)} reopened within two weeks. This median covers matched reopenings only, not the closures with no reopening on file.
- **Closures with a failed attempt lasted longer.** ${pct(q8.share_with_failed_reopening)} of all closures include at least one failed reopening attempt; among the ${fmt(q8.n_reopened)} that reopened, ${pct(q8.n_reopened_after_failed_try / q8.n_reopened)} reopened only after one. Those lasted a median of ${q8.median_days_after_failed_try} days, against ${q8.median_days_first_try} days for closures that reopened at the first try.
- **Cited at closures, compared with first inspections.** ${q8.top_code} (${shortLabel(violations[0])}) is cited at ${pct(q8.top_code_share)} of closing inspections, against ${pct(q8.top_code_first_share)} of first inspections. Relative to first inspections, the codes most over-represented at closures are ${andList(mostOver)}.${lessAtClosure.length ? ` Of the ${violations.length} codes cited most at closures, only ${andList(lessAtClosure)} ${lessAtClosure.length > 1 ? "are" : "is"} cited less often at closures than at first inspections.` : ""} These are violations present at the closing inspection, not proof of what caused the closure.
- **Who is missing.** The file keeps only restaurants that are active at the snapshot, so a restaurant that closed for good isn't in it. The reopening share and the median describe restaurants that are still in the file.

## How the data were prepared

- **Unit of observation:** one closure, from an inspection whose action begins "Establishment Closed" to the same restaurant's next "Establishment re-opened" record. Closures are followed through the whole file, and those that began from ${q8.window_start} to ${q8.window_end} are kept; ${fmt(q8.n_closures_before_window)} earlier closures are left out.
- **Failed attempts:** "re-closed" records, and reopening inspections that close the restaurant again, between the closure and the reopening.
- **No reopening on file:** the closure is labeled by what comes after it: closed again before a reopening record, inspected again in a graded program, closed within 30 days of the end of follow-up ("recent closure"), or no reopening record and no later graded inspection for a closure more than 30 days before the end of follow-up.
- **Snapshot and end of follow-up:** the ${snapshotDate} download; follow-up ends at its latest inspection, ${q8.last_inspection_date}, the same date as Q7.
- **Violations:** the share of the ${fmt(q8.n_closing_inspections)} closing inspections, and of the routine first inspections, in the same window that cite each code; a code counts once per inspection.
- **Records left out:** in the whole file, ${fmt(q8.reopened_without_closure)} "re-opened" and ${fmt(q8.reclosed_without_closure)} "re-closed" records have no closure on file, probably because the closure is older than the retained history.
- **Script:** `scripts/question-specific/question-8.py` writes `q8-matching.csv`, `q8-jan2025.csv`, `q8-violations.csv`, `q8-days-closed.csv` and `q8-summary.json` to `src/data/`.

## Changes since Milestone 2

These follow the TA's Milestone 2 feedback. The Milestone 2 page is kept unchanged (link at the bottom).

- **No causal wording:** the page and the chart describe "violations cited at the closing inspection", not why restaurants close.
- **Window:** Q8 now keeps closures that began from ${q8.window_start} to ${q8.window_end}, like the other questions, so its counts differ slightly from Milestone 2. The violation comparison uses closing and first inspections from the same window.
- **Missing reopenings as rules:** "still closed" is now "recent closure, no reopening on file", and every label names the rule that applies.
- **Median limited to matched reopenings:** the text and the chart say that the median covers only closures with a recorded reopening.
- **Snapshot recorded:** the summary file stores the raw file's name and the window.

<details>
<summary>Closures that began January 1–10, 2025: the sample we matched first (M1 feedback, point 2)</summary>

```js
display(Inputs.table(jan, {
  layout: "auto",
  rows: 20,
  header: {
    camis: "CAMIS",
    dba: "Restaurant",
    closed_on: "Closed",
    closing_inspection: "Closing inspection",
    failed_reopenings: "Failed attempts",
    reopened_on: "Reopened",
    days_closed: "Days closed",
    status: "Status"
  },
  format: {
    camis: String,
    closed_on: (d) => d3.utcFormat("%Y-%m-%d")(d),
    reopened_on: (d) => (d ? d3.utcFormat("%Y-%m-%d")(d) : "")
  }
}))
```

</details>

## D3 code

<details>
<summary>Show the D3 code for the three charts</summary>

```js echo
// One stacked bar: how every closure ends, with a legend in the same order
function closureOutcomes(matching, {width}) {
  const fmt = d3.format(",");
  const pct = d3.format(".1%");
  const colors = ["#3f9db2", "#8f8f8f", "#adadad", "#c8c8c8", "#dedede"];   // reopened, then the four kinds with no reopening
  const total = d3.sum(matching, (d) => d.closures);
  let start = 0;
  const parts = matching.map((d, i) => {
    const part = {...d, x0: start, color: colors[i]};
    start += d.closures;
    return part;
  });

  const w = Math.max(560, Math.min(width, 960));
  const h = 70 + 20 * parts.length;
  const x = d3.scaleLinear([0, total], [0, w]);

  const svg = d3.create("svg")
    .attr("viewBox", [0, 0, w, h])
    .attr("width", w)
    .attr("height", h)
    .attr("fill", "currentColor")
    .attr("style", "max-width: 100%; height: auto; font: 12px var(--sans-serif);");

  svg.append("text").attr("y", 14).attr("font-weight", 600).text(`How the ${fmt(total)} closures end`);
  svg.append("g")
    .selectAll("rect")
    .data(parts)
    .join("rect")
    .attr("x", (d) => x(d.x0))
    .attr("y", 24)
    .attr("width", (d) => Math.max(1, x(d.closures)))
    .attr("height", 32)
    .attr("fill", (d) => d.color)
    .attr("stroke", "var(--theme-background)")
    .append("title")
    .text((d) => `${d.status}: ${fmt(d.closures)} closures, ${pct(d.closures / total)}`);

  const legend = svg.append("g")
    .selectAll("g")
    .data(parts)
    .join("g")
    .attr("transform", (d, i) => `translate(0,${80 + 20 * i})`);
  legend.append("rect").attr("y", -9).attr("width", 10).attr("height", 10).attr("fill", (d) => d.color);
  legend.append("text").attr("x", 16).text((d) => `${d.status}: ${fmt(d.closures)} (${pct(d.closures / total)})`);

  return svg.node();
}
```

```js echo
// Days closed, stacked with d3.stack: reopened at the first try (solid) or after a failed attempt (hatched)
function daysClosedChart(daysClosed, q8, {width}) {
  const fmt = d3.format(",");
  const pct = d3.format(".1%");
  const bins = daysClosed.map((d) => ({...d, label: String(d.days_closed)}));   // autoType reads "1" as a number
  const n = d3.sum(bins, (d) => d.count);
  const id = `hatch-${Math.random().toString(36).slice(2)}`;
  const kinds = [
    {key: "reopened_first_try", label: "reopened at the first try", fill: "#3f9db2", stroke: null},
    {key: "reopened_after_failed_try", label: "after a failed attempt", fill: `url(#${id})`, stroke: "#c2640f"}
  ];
  const series = d3.stack().keys(kinds.map((k) => k.key))(bins);

  const w = Math.max(560, Math.min(width, 960));
  const h = 360, m = {top: 84, right: 20, bottom: 46, left: 56};
  const x = d3.scaleBand(bins.map((d) => d.label), [m.left, w - m.right]).padding(0.25);
  const y = d3.scaleLinear([0, d3.max(bins, (d) => d.count)], [h - m.bottom, m.top]).nice();

  const svg = d3.create("svg")
    .attr("viewBox", [0, 0, w, h])
    .attr("width", w)
    .attr("height", h)
    .attr("fill", "currentColor")
    .attr("style", "max-width: 100%; height: auto; font: 12px var(--sans-serif);");

  // Hatch pattern, so the two parts differ by more than color
  const pattern = svg.append("defs").append("pattern")
    .attr("id", id)
    .attr("width", 6)
    .attr("height", 6)
    .attr("patternUnits", "userSpaceOnUse")
    .attr("patternTransform", "rotate(45)");
  pattern.append("rect").attr("width", 6).attr("height", 6).attr("fill", "#fbe8d4");
  pattern.append("line").attr("y2", 6).attr("stroke", "#c2640f").attr("stroke-width", 2);

  svg.append("text").attr("x", m.left).attr("y", 16).attr("font-weight", 600)
    .text(`Days closed, for the ${fmt(n)} closures with a recorded reopening`);
  svg.append("text").attr("x", m.left).attr("y", 34).attr("fill-opacity", 0.8)
    .text(`median ${q8.median_days_closed} days, middle half ${q8.p25_days_closed}–${q8.p75_days_closed} days`);
  kinds.forEach((k, i) => {
    const key = svg.append("g").attr("transform", `translate(${m.left + i * 250},58)`);
    key.append("rect").attr("y", -11).attr("width", 14).attr("height", 14).attr("fill", k.fill).attr("stroke", k.stroke);
    key.append("text").attr("x", 20).text(`${k.label} (${fmt(d3.sum(bins, (d) => d[k.key]))})`);
  });

  svg.append("g")
    .selectAll("g")
    .data(series)
    .join("g")
    .attr("fill", (s) => kinds[s.index].fill)
    .attr("stroke", (s) => kinds[s.index].stroke)
    .selectAll("rect")
    .data((s) => s.map((d) => ({...d, kind: kinds[s.index].label})))
    .join("rect")
    .attr("x", (d) => x(d.data.label))
    .attr("width", x.bandwidth())
    .attr("y", (d) => y(d[1]))
    .attr("height", (d) => y(d[0]) - y(d[1]))
    .append("title")
    .text((d) => `${d.data.label === "1" ? "1 day" : d.data.label.startsWith("0") ? "same day" : `${d.data.label} days`}, ${d.kind}: ${fmt(d[1] - d[0])}, ${pct((d[1] - d[0]) / n)} of ${fmt(n)}`);

  svg.append("g")
    .attr("text-anchor", "middle")
    .selectAll("text")
    .data(bins)
    .join("text")
    .attr("x", (d) => x(d.label) + x.bandwidth() / 2)
    .attr("y", (d) => y(d.count) - 5)
    .text((d) => fmt(d.count));

  svg.append("g")
    .attr("transform", `translate(0,${h - m.bottom})`)
    .call(d3.axisBottom(x).tickSizeOuter(0))
    .call((a) => a.append("text").attr("x", w - m.right).attr("y", 36).attr("fill", "currentColor").attr("text-anchor", "end")
      .text("days closed (the bins get wider to the right) →"));
  svg.append("g")
    .attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5))
    .call((a) => a.select(".domain").remove())
    .call((a) => a.append("text").attr("x", -m.left).attr("y", m.top - 8).attr("fill", "currentColor").attr("text-anchor", "start")
      .text("↑ closures"));

  return svg.node();
}
```

```js echo
// Violations cited at closing inspections (bars), against routine first inspections (ticks)
function violationsChart(violations, q8, {top, width}) {
  const fmt = d3.format(",");
  const pct = d3.format(".1%");
  const rows = violations.slice(0, top);

  const w = Math.max(600, Math.min(width, 960));
  const m = {top: 56, right: 64, bottom: 42, left: 300};
  const h = m.top + rows.length * 26 + m.bottom;
  const x = d3.scaleLinear([0, 1], [m.left, w - m.right]);
  const y = d3.scaleBand(rows.map((d) => d.violation_code), [m.top, h - m.bottom]).padding(0.25);

  const svg = d3.create("svg")
    .attr("viewBox", [0, 0, w, h])
    .attr("width", w)
    .attr("height", h)
    .attr("fill", "currentColor")
    .attr("style", "max-width: 100%; height: auto; font: 12px var(--sans-serif);");

  svg.append("text").attr("y", 16).attr("font-weight", 600)
    .text(`Violations cited at the ${fmt(q8.n_closing_inspections)} closing inspections`);
  svg.append("rect").attr("y", 28).attr("width", 18).attr("height", 12).attr("fill", "#9fcdd8");
  svg.append("text").attr("x", 24).attr("y", 38).text("closing inspections");
  svg.append("line").attr("x1", 170).attr("x2", 170).attr("y1", 26).attr("y2", 42).attr("stroke", "currentColor").attr("stroke-width", 3);
  svg.append("text").attr("x", 180).attr("y", 38).text("routine first inspections");

  const row = svg.append("g")
    .selectAll("g")
    .data(rows)
    .join("g")
    .attr("transform", (d) => `translate(0,${y(d.violation_code)})`);
  row.append("title")
    .text((d) => `${d.violation_code} (${d.critical_flag}): ${d.violation_description}\n` +
      `Closing inspections: ${fmt(d.closures_citing)} (${pct(d.share_of_closures)})\nFirst inspections: ${pct(d.share_of_first_inspections)}`);
  row.append("rect").attr("x", m.left).attr("width", (d) => x(d.share_of_closures) - m.left).attr("height", y.bandwidth()).attr("fill", "#9fcdd8");
  row.append("line")
    .attr("x1", (d) => x(d.share_of_first_inspections))
    .attr("x2", (d) => x(d.share_of_first_inspections))
    .attr("y1", -3)
    .attr("y2", y.bandwidth() + 3)
    .attr("stroke", "currentColor")
    .attr("stroke-width", 3);
  row.append("text")
    .attr("x", (d) => Math.max(x(d.share_of_closures), x(d.share_of_first_inspections)) + 6)
    .attr("y", y.bandwidth() / 2)
    .attr("dy", "0.35em")
    .text((d) => pct(d.share_of_closures));
  row.append("text")
    .attr("x", m.left - 10)
    .attr("y", y.bandwidth() / 2)
    .attr("dy", "0.35em")
    .attr("text-anchor", "end")
    .text((d) => `${d.violation_code}  ${shortLabel(d)}`);

  svg.append("g")
    .attr("transform", `translate(0,${h - m.bottom})`)
    .call(d3.axisBottom(x).ticks(5, "%"))
    .call((a) => a.append("text").attr("x", w - m.right).attr("y", 34).attr("fill", "currentColor").attr("text-anchor", "end")
      .text("share of inspections that cite the code →"));

  return svg.node();
}

// Short names for the codes cited most at closures
function shortLabel(d) {
  const names = new Map([
    ["08A", "Conditions that attract pests"],
    ["06C", "Food not protected from contamination"],
    ["04L", "Mice"],
    ["10F", "Non-food surfaces not clean or sealed"],
    ["02G", "Cold food above 41 °F"],
    ["10B", "Plumbing or drainage problem"],
    ["02B", "Hot food below 140 °F"],
    ["04N", "Flies"],
    ["06D", "Food-contact surface not sanitized"],
    ["04M", "Live roaches"],
    ["04H", "Food contaminated or not discarded"],
    ["05D", "No hand-washing sink nearby"],
    ["04A", "No Food Protection Certificate holder"],
    ["28-06", "No pest-control contract or records"],
    ["08C", "Pesticide misused or stored badly"]
  ]);
  return names.get(d.violation_code) ?? d.violation_description.slice(0, 36);
}
```

</details>

The processed tables and the sketch submitted for Milestone 2 are kept unchanged at [Milestone 2 · Q8](../milestone-2/question-8).
