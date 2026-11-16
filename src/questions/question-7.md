---
title: 7. Recovering from a missed A
---

# Do restaurants that miss an A on the first inspection recover at the re-inspection?

A first inspection that scores 14 or more doesn't give a letter grade. The restaurant gets a second, unannounced visit, the re-inspection, and that visit's score sets the grade (a restaurant that scores 14 or more there can post a "Grade Pending" card until its hearing). This page follows every first inspection that missed an A to its re-inspection: how often the restaurant reaches the A range (0–13 points), how that differs between a B-range start (14–27) and a C-range start (28+), and how long the re-inspection takes.

```js
const flow = FileAttachment("/data/q7-flow.csv").csv({typed: true});
const days = FileAttachment("/data/q7-days.csv").csv({typed: true});
const pairs = FileAttachment("/data/q7-pairs-sample.csv").csv({typed: true});
const q7 = FileAttachment("/data/q7-summary.json").json();
```

```js
const fmt = d3.format(",");
const pct = d3.format(".1%");
const flowCount = (band, outcome) => flow.find((d) => d.first_band === band && d.outcome === outcome)?.count ?? 0;
const bandShare = (band, outcome) => flow.find((d) => d.first_band === band && d.outcome === outcome)?.share_of_band ?? 0;
const scoredShare = (band) => {
  const [a, b, c] = ["A at re-inspection", "B range at re-inspection", "C range at re-inspection"].map((o) => flowCount(band, o));
  return a / (a + b + c);
};
const snapshotDate = q7.snapshot?.match(/\d{4}-\d{2}-\d{2}/)?.[0] ?? "2026-11-02";
```

## From first score to re-inspection result

```js
const bandInput = Inputs.radio(["Both bands", "14–27", "28+"], {label: "First-inspection score", value: "Both bands"});
const band = view(bandInput);
```

```js
display(recoveryFlow(flow, {band, width, onSelect: selectBand}));
```

First inspections from ${q7.window_start} to ${q7.window_end}, the same window as Q1, Q3, Q5 and Q6. Each band's height is the number of first inspections. Click a band on the left, or use the buttons above, to follow it: its flows stay dark, the labels on the right switch to its shares, and the histogram below switches with it. Hover a flow or an outcome for its count. Gray outcomes have no scored re-inspection on file; their labels name the rule that applies, not what actually happened to the restaurant.

## How long the re-inspection took

```js
display(waitHistogram(days, q7, {band, width}));
```

Re-inspections in 30-day bins, as a share of the selected group's re-inspections so both bands use the same axis; the title gives the count. The dashed line marks 30 days, the city guide's "typically within a month". The dotted line marks the selected group's median. Hover a bar for its count.

## What it shows

```js
const cHeading = scoredShare("28+") < scoredShare("14-27")
  ? "A C-range start reaches the A range less often."
  : "Both starts reach the A range about as often.";
const months = Math.round(q7.median_days_to_reinspection / 30.4);
const closureNote = q7.share_long_waits_with_closure < 0.05 ? ", so closures explain few of them" : "";
```

- **Two denominators for recovery.** Of the ${fmt(q7.n_missed_a)} first inspections that scored 14 or more, ${fmt(q7.n_a_at_reinspection)} (${pct(q7.share_a_at_reinspection)}) reached the A range at the re-inspection. That share counts every first inspection, including those with no re-inspection on file. Among the ${fmt(q7.n_scored_reinspections)} with a scored re-inspection, ${pct(q7.share_recovered_of_reinspected)} reached the A range.
- **${cHeading}** ${pct(bandShare("14-27", "A at re-inspection"))} of the first inspections that scored 14–27 reached the A range at the re-inspection, against ${pct(bandShare("28+", "A at re-inspection"))} of those that scored 28 or more. Among first inspections with a scored re-inspection, the shares are ${pct(scoredShare("14-27"))} and ${pct(scoredShare("28+"))}.
- **Missing follow-up stays visible.** ${fmt(q7.n_recent_no_reinspection)} first inspections (${pct(q7.share_recent_no_reinspection)}) have no re-inspection on file and fall within ${q7.follow_up_days} days of the end of follow-up, so one may still come. For ${fmt(q7.n_next_cycle_no_reinspection)}, the restaurant's next first inspection came before any re-inspection, and ${fmt(q7.n_older_no_reinspection)} older ones have none on file. These labels are rules applied to the records, not known outcomes.
- **Re-inspections usually come months later.** The median wait was ${q7.median_days_to_reinspection} days, about ${months} months (${q7.median_days_14_27} days after a 14–27 start, ${q7.median_days_28_plus} after a 28+ start). Only ${pct(q7.share_reinspected_under_30_days)} came within 30 days, although the city's guide says the inspector returns "typically within a month" ([How We Score and Grade](https://www.nyc.gov/assets/doh/downloads/pdf/rii/how-we-score-grade.pdf)).
- **Checking the long waits.** ${fmt(q7.n_long_waits)} re-inspections (${pct(q7.share_long_waits)}) came more than ${q7.long_wait_days} days after the first inspection, and ${pct(q7.share_long_waits_with_closure)} of those had a closure in between${closureNote}. The ${fmt(q7.n_waits_with_closure)} cycles with a closure had a median wait of ${q7.median_days_with_closure} days, against ${q7.median_days_without_closure} days for cycles without one. Waits only count re-inspections on file by the end of follow-up, so recent first inspections can only add short waits; among first inspections at least a year before the end of follow-up, the median wait is ${q7.median_days_followed_a_year} days.
- **Who is missing, and what the data can't show.** The file keeps only restaurants that are active at the snapshot, with about three years of inspections. A restaurant that closed for good after a bad first inspection isn't in it, which probably makes recovery look more common than it is. The data show how often restaurants reach the A range, not why.

## How the data were prepared

- **Unit of observation:** one first inspection (`Cycle Inspection / Initial Inspection`) from ${q7.window_start} to ${q7.window_end} that scored 14 or more, paired with the same restaurant's next `Cycle Inspection / Re-inspection` if that comes before the restaurant's next first inspection. The ${fmt(q7.n_first_inspections_before_window)} first inspections before ${q7.window_start} are left out.
- **Cycle boundaries:** a re-inspection after the restaurant's next first inspection belongs to that later cycle; ${fmt(q7.n_moved_to_later_cycle)} matches were moved this way. Of the ${fmt(q7.n_reinspections_in_window)} re-inspections in the window, ${fmt(q7.n_unpaired_reinspections)} have no first inspection in the window to pair with, for example because their first inspection came before ${q7.window_start}.
- **Bands and outcomes:** the first-inspection score puts each visit in the 14–27 band (a B if it were graded on the spot) or the 28+ band (a C). The outcome is the band of the re-inspection score: 0–13 (A range), 14–27 or 28+. We use score bands rather than the posted card, because a restaurant that scores 14 or more at the re-inspection can post "Grade Pending" until its hearing. "Re-inspected, no score" (${fmt(q7.n_reinspected_no_score)} here) means a re-inspection is on file without a score.
- **No re-inspection on file:** three rules, checked in this order. The restaurant's next first inspection came first ("next cycle began"). Otherwise, the first inspection is within ${q7.follow_up_days} days of the end of follow-up ("recent first inspection"). Otherwise, "older first inspection".
- **Snapshot and end of follow-up:** the ${snapshotDate} download; follow-up ends at its latest inspection, ${q7.last_inspection_date}, the same date as Q8.
- **Waits:** days from the first inspection to the paired re-inspection. The ${fmt(q7.n_reinspected_after_a)} re-inspections that followed a first score of 0–13 are left out. A closure counts as "in between" if the restaurant had an inspection that closed it from the first inspection up to the day before the re-inspection.
- **Script:** `scripts/question-specific/question-7.py` writes `q7-flow.csv`, `q7-days.csv`, `q7-pairs-sample.csv` and `q7-summary.json` to `src/data/`.

## Changes since Milestone 2

These follow the TA's Milestone 2 feedback. The Milestone 2 page is kept unchanged (link at the bottom).

- **Window:** Q7 now uses first inspections from ${q7.window_start} to ${q7.window_end}, like Q1, Q3, Q5 and Q6, so its counts differ slightly from Milestone 2.
- **Missing follow-up as rules:** a first inspection followed by the restaurant's next first inspection no longer counts as "awaiting", however recent it is, and the labels name the rule that applies.
- **Two denominators:** the share of all missed-A first inspections and the share among scored re-inspections are given separately, overall and per band.
- **Long waits checked:** closures during the cycle, a median for first inspections followed for at least a year, and the cycle-boundary counts are reported next to the comparison with the city's guide.
- **Snapshot recorded:** the summary file stores the raw file's name and the window.
- **D3:** the flow and the histogram are linked: choosing a band updates the flow, the histogram, its count and its median together.

<details>
<summary>Sample of matched pairs (two per outcome)</summary>

```js
display(Inputs.table(pairs, {
  layout: "auto",
  rows: 20,
  header: {
    camis: "CAMIS",
    first_date: "First inspection",
    first_score: "First score",
    reinspection_date: "Re-inspection",
    reinspection_score: "Re-inspection score",
    grade_after_reinspection: "Card after re-inspection",
    days_to_reinspection: "Days",
    outcome: "Outcome"
  },
  format: {
    camis: String,
    first_date: (d) => d3.utcFormat("%Y-%m-%d")(d),
    reinspection_date: (d) => (d ? d3.utcFormat("%Y-%m-%d")(d) : "")
  }
}))
```

</details>

## D3 code

<details>
<summary>Show the D3 code for both charts</summary>

```js echo
// Flow from first-inspection band (left) to re-inspection outcome (right).
// Both sides use the same scale, so a flow is as wide where it leaves as where it arrives.
function recoveryFlow(flow, {band, width, onSelect}) {
  const fmt = d3.format(",");
  const pct = d3.format(".1%");
  const bands = [
    {key: "14-27", label: "14–27", color: "#a28be0"},
    {key: "28+", label: "28+", color: "#5a2ea6"}
  ];
  const outcomes = [
    {key: "A at re-inspection", label: "A range (0–13) at re-inspection", color: "#2f6fba"},
    {key: "B range at re-inspection", label: "B range (14–27) at re-inspection", color: "#2e9150"},
    {key: "C range at re-inspection", label: "C range (28+) at re-inspection", color: "#dc9a12"},
    {key: "Re-inspected, no score", label: "Re-inspected, no score", color: "#7f7f7f"},
    {key: "Next cycle began, no re-inspection on file", label: "Next cycle began, none on file", color: "#8f8f8f"},
    {key: "No re-inspection on file, first inspection within 365 days of the end of follow-up", label: "None on file, recent first inspection", color: "#adadad"},
    {key: "No re-inspection on file, first inspection more than 365 days before the end of follow-up", label: "None on file, older first inspection", color: "#cbcbcb"}
  ];
  const count = (b, o) => flow.find((d) => d.first_band === b && d.outcome === o)?.count ?? 0;
  for (const b of bands) b.total = d3.sum(outcomes, (o) => count(b.key, o.key));
  for (const o of outcomes) o.total = d3.sum(bands, (b) => count(b.key, o.key));
  const shown = outcomes.filter((o) => o.total > 0);
  const total = d3.sum(bands, (b) => b.total);
  const selected = bands.find((b) => b.label === band);

  const w = Math.max(640, Math.min(width, 960));
  const h = 500, top = 40, left = 180, right = 280, nodeW = 14, gap = 16, bandGap = 28;
  const xL = left, xR = w - right - nodeW;
  const k = (h - top - 16 - gap * (shown.length - 1)) / total;   // pixels per first inspection

  let y = top;
  for (const o of shown) {
    o.y = y;
    y += o.total * k + gap;
  }
  y = top + (gap * (shown.length - 1) - bandGap) / 2;
  for (const b of bands) {
    b.y = y;
    y += b.total * k + bandGap;
  }

  // Flows leave each band in outcome order and arrive at each outcome 14–27 first
  const links = [];
  const leftNext = new Map(bands.map((b) => [b, b.y]));
  for (const b of bands) {
    for (const o of shown) {
      const n = count(b.key, o.key);
      if (!n) continue;
      links.push({b, o, n, y0: leftNext.get(b)});
      leftNext.set(b, leftNext.get(b) + n * k);
    }
  }
  const rightNext = new Map(shown.map((o) => [o, o.y]));
  for (const l of links) {
    l.y1 = rightNext.get(l.o);
    rightNext.set(l.o, l.y1 + l.n * k);
  }
  const ribbon = (l) => {
    const xa = xL + nodeW, xb = xR, xm = (xa + xb) / 2, t = l.n * k;
    return `M${xa},${l.y0}C${xm},${l.y0} ${xm},${l.y1} ${xb},${l.y1}` +
      `L${xb},${l.y1 + t}C${xm},${l.y1 + t} ${xm},${l.y0 + t} ${xa},${l.y0 + t}Z`;
  };

  const svg = d3.create("svg")
    .attr("viewBox", [0, 0, w, h])
    .attr("width", w)
    .attr("height", h)
    .attr("fill", "currentColor")
    .attr("style", "max-width: 100%; height: auto; font: 12px var(--sans-serif); overflow: visible;");

  svg.append("text").attr("x", xL + nodeW).attr("y", 16).attr("text-anchor", "end").attr("font-weight", 600).text("First inspection");
  svg.append("text").attr("x", xR).attr("y", 16).attr("font-weight", 600).text("Re-inspection outcome");

  svg.append("g")
    .selectAll("path")
    .data(links)
    .join("path")
    .attr("d", ribbon)
    .attr("fill", (l) => l.b.color)
    .attr("fill-opacity", (l) => (!selected ? 0.45 : l.b === selected ? 0.75 : 0.08))
    .append("title")
    .text((l) => `${l.b.label} → ${l.o.label}: ${fmt(l.n)} first inspections, ${pct(l.n / l.b.total)} of the band`);

  svg.append("g")
    .selectAll("rect")
    .data(shown)
    .join("rect")
    .attr("x", xR)
    .attr("y", (o) => o.y)
    .attr("width", nodeW)
    .attr("height", (o) => Math.max(1, o.total * k))
    .attr("fill", (o) => o.color)
    .append("title")
    .text((o) => `${o.label}: ${fmt(o.total)} first inspections, ${pct(o.total / total)} of all`);

  // Spread the outcome labels so small nodes don't overlap
  let last = -Infinity;
  for (const o of shown) last = o.ly = Math.max(o.y + (o.total * k) / 2, last + 34);
  for (let i = shown.length - 1; i >= 0; i--) {
    shown[i].ly = Math.min(shown[i].ly, i === shown.length - 1 ? h - 17 : shown[i + 1].ly - 34);
  }
  const detail = (o) => selected
    ? `${fmt(count(selected.key, o.key))} · ${pct(count(selected.key, o.key) / selected.total)} of the ${selected.label} band`
    : `${fmt(o.total)} · 14–27: ${pct(count("14-27", o.key) / bands[0].total)} · 28+: ${pct(count("28+", o.key) / bands[1].total)}`;
  const labels = svg.append("g").selectAll("g").data(shown).join("g");
  labels.append("path")
    .attr("d", (o) => `M${xR + nodeW + 2},${o.y + (o.total * k) / 2}L${xR + nodeW + 8},${o.ly}`)
    .attr("stroke", "currentColor")
    .attr("stroke-opacity", 0.35);
  labels.append("text").attr("x", xR + nodeW + 12).attr("y", (o) => o.ly - 3).attr("font-weight", 600).text((o) => o.label);
  labels.append("text").attr("x", xR + nodeW + 12).attr("y", (o) => o.ly + 13).attr("fill-opacity", 0.8).text(detail);

  // Band nodes: click one to follow it, click it again to show both
  const bandNodes = svg.append("g")
    .selectAll("g")
    .data(bands)
    .join("g")
    .style("cursor", "pointer")
    .on("click", (event, b) => onSelect(b === selected ? "Both bands" : b.label));
  bandNodes.append("title").text("Click to follow this band, click again to show both");
  bandNodes.append("rect").attr("width", xL + nodeW).attr("y", (b) => b.y).attr("height", (b) => b.total * k).attr("fill", "transparent");
  bandNodes.append("rect")
    .attr("x", xL)
    .attr("y", (b) => b.y)
    .attr("width", nodeW)
    .attr("height", (b) => b.total * k)
    .attr("fill", (b) => b.color)
    .attr("stroke", (b) => (b === selected ? "currentColor" : null))
    .attr("stroke-width", 2);
  bandNodes.append("text")
    .attr("x", xL - 10)
    .attr("y", (b) => b.y + (b.total * k) / 2 - 4)
    .attr("text-anchor", "end")
    .attr("font-weight", (b) => (b === selected ? 800 : 600))
    .text((b) => `First score ${b.label}`);
  bandNodes.append("text")
    .attr("x", xL - 10)
    .attr("y", (b) => b.y + (b.total * k) / 2 + 12)
    .attr("text-anchor", "end")
    .text((b) => `${fmt(b.total)} first inspections`);

  return svg.node();
}
```

```js echo
// Days to re-inspection for the selected band. Bars are shares of that band's re-inspections on
// one fixed axis, so switching bands changes the bars, the count and the median together.
function waitHistogram(days, q7, {band, width}) {
  const fmt = d3.format(",");
  const pct = d3.format(".1%");
  const groups = {
    "Both bands": {column: "count", label: "a first score of 14 or more", color: "#8e78d8", median: q7.median_days_to_reinspection},
    "14–27": {column: "count_14_27", label: "a first score of 14–27", color: "#a28be0", median: q7.median_days_14_27},
    "28+": {column: "count_28_plus", label: "a first score of 28+", color: "#5a2ea6", median: q7.median_days_28_plus}
  };
  const g = groups[band];
  const n = d3.sum(days, (d) => d[g.column]);
  const yMax = d3.max(Object.values(groups), (gr) => d3.max(days, (d) => d[gr.column] / d3.sum(days, (e) => e[gr.column])));

  const w = Math.max(560, Math.min(width, 960));
  const h = 360, m = {top: 64, right: 24, bottom: 46, left: 56};
  const x = d3.scaleLinear([0, 30 * days.length], [m.left, w - m.right]);
  const y = d3.scaleLinear([0, yMax], [h - m.bottom, m.top]).nice();

  const svg = d3.create("svg")
    .attr("viewBox", [0, 0, w, h])
    .attr("width", w)
    .attr("height", h)
    .attr("fill", "currentColor")
    .attr("style", "max-width: 100%; height: auto; font: 12px var(--sans-serif);");

  svg.append("text").attr("x", m.left).attr("y", 16).attr("font-weight", 600)
    .text(`Days to re-inspection: ${fmt(n)} re-inspections after ${g.label}`);

  svg.append("g")
    .attr("fill", g.color)
    .selectAll("rect")
    .data(days)
    .join("rect")
    .attr("x", (d, i) => x(i * 30) + 1)
    .attr("width", x(30) - x(0) - 2)
    .attr("y", (d) => y(d[g.column] / n))
    .attr("height", (d) => y(0) - y(d[g.column] / n))
    .append("title")
    .text((d) => `${d.days} days: ${fmt(d[g.column])} re-inspections, ${pct(d[g.column] / n)} of ${fmt(n)}`);

  // The guide's 30 days and the group's median
  const marks = [[30, "30 days: the guide's “typically within a month”", "5,4", 36], [g.median, `median ${g.median} days`, "2,3", 52]];
  for (const [day, text, dash, textY] of marks) {
    svg.append("line")
      .attr("x1", x(day))
      .attr("x2", x(day))
      .attr("y1", textY + 4)
      .attr("y2", h - m.bottom)
      .attr("stroke", "currentColor")
      .attr("stroke-dasharray", dash);
    svg.append("text").attr("x", x(day) + 5).attr("y", textY).text(text);
  }

  svg.append("g")
    .attr("transform", `translate(0,${h - m.bottom})`)
    .call(d3.axisBottom(x).tickValues(d3.range(0, 30 * days.length, 60)).tickFormat((v) => (v >= 360 ? "360+" : v)))
    .call((a) => a.append("text").attr("x", w - m.right).attr("y", 36).attr("fill", "currentColor").attr("text-anchor", "end")
      .text("days from the first inspection to the re-inspection (30-day bins) →"));
  svg.append("g")
    .attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5, "%"))
    .call((a) => a.select(".domain").remove())
    .call((a) => a.append("text").attr("transform", "rotate(-90)").attr("x", -(m.top + h - m.bottom) / 2).attr("y", -42).attr("fill", "currentColor")
      .attr("text-anchor", "middle").text("share of re-inspections"));

  return svg.node();
}

// Clicking a band in the flow sets the radio buttons, which redraws both charts
function selectBand(value) {
  bandInput.value = value;
  bandInput.dispatchEvent(new Event("input", {bubbles: true}));
}
```

</details>

The processed tables and the sketch submitted for Milestone 2 are kept unchanged at [Milestone 2 · Q7](../milestone-2/question-7).
