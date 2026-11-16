---
title: 4. Chain restaurants
---

# Do branches of the same chain get similar grades?

We compare Dunkin, Starbucks and McDonald's. One CAMIS is one branch.

<div class="tip">
  <strong>Grade definition (same as Q2):</strong> a restaurant's grade is the grade of its most recent graded inspection, which is the card it posts now. A later Grade Pending (Z or P) or Not Yet Graded (N) replaces an earlier A, B or C. The branch list still shows that earlier letter and its date. The A share is out of all branches with a grade, like in Q2.
</div>

```js
const summary = FileAttachment("/data/q4-chain-summary.csv").csv({typed: true});
const branches = FileAttachment("/data/q4-branches.csv").csv({typed: true});
```

## How we found the branches

We look for DUNKIN, STARBUCKS or MCDONALD in the name, and keep the ones that start with the brand. Combo stores like "DUNKIN / BASKIN ROBBINS" are out, because one grade is for two brands. 12 names were unclear, like ferry shops and shared counters, so we checked them by hand. Only the Pace University Starbucks counts.

## Grades per chain

```js
display(Inputs.table(summary, {
  layout: "auto",
  select: false,
  columns: ["chain", "branches", "A", "B", "C", "grade_pending", "not_graded", "never_graded", "pct_A"],
  header: {chain: "Chain", branches: "Branches", grade_pending: "Grade Pending", not_graded: "Not Yet Graded", never_graded: "Never graded", pct_A: "% A (of branches with a grade)"}
}));
```

## Branch list

```js
const grade = view(Inputs.select(["All", "A", "B", "C", "Grade Pending", "Not Yet Graded", "Never graded"], {label: "Grade"}));
```

```js
const day = d => d instanceof Date ? d.toISOString().slice(0, 10) : d;
const shown = branches
  .filter(d => d.in_sample)
  .filter(d => grade === "All" || (grade === "Never graded" ? !d.card : d.card === grade));
display(Inputs.table(shown, {
  layout: "auto",
  select: false,
  columns: ["chain", "camis", "dba", "boro", "card", "grade_date", "latest_letter", "latest_letter_date", "last_status"],
  header: {chain: "Chain", camis: "CAMIS", dba: "Name", boro: "Borough", card: "Grade", grade_date: "Grade date", latest_letter: "Latest letter", latest_letter_date: "Letter date", last_status: "Last inspection's grade"},
  format: {camis: d => String(d), grade_date: day, latest_letter_date: day}
}));
```

## Planned chart

Base chart is firstly drawn by python(matplotlib), then add some elements by hand.

![Q4 sketch](../images/q4-sketch.jpg)

Each chain is a row and each grade is a column: A, B, C and no A/B/C yet. Each dot is one branch, and a hollow dot means no letter. Each row shows its n. When you hover a dot, it shows the branch name, borough, grade date and latest status.

The sketch was drawn with the earlier grade definition (latest A, B or C). The chart will use the definition above, so the "no A/B/C yet" column becomes two columns, Grade Pending and Not Yet Graded.

## D3 Chart

The first chart is the card each branch shows today, the second one goes back to the first inspection before that card.

### 1. The card on the door

```js
const highlight = view(Inputs.select(["All", "A", "B", "C", "Grade Pending", "Not Yet Graded"], {label: "Highlight grade"}));
```

```js
display(gradeDots(branches.filter(d => d.in_sample), highlight));
```

<p class="q4-caption">One dot is one branch. The grade is the card from the branch's most recent graded inspection, like in Q2. ${d3.sum(summary, d => d.branches)} branches in the 2026-11-02 snapshot. Hover a dot to see the branch.</p>

```js
function gradeDots(data, highlight) {
  const cards = ["A", "B", "C", "Grade Pending", "Not Yet Graded"];
  const chains = ["Dunkin", "Starbucks", "McDonald's"];
  // the colors of the real grade cards: A blue, B green, C orange
  const color = {"A": "#2b59c3", "B": "#3a9d5d", "C": "#f29d38", "Grade Pending": "#9b8ec4", "Not Yet Graded": "white"};
  const step = 9;
  const perRow = card => card === "A" ? 25 : 4;



  // where each grade column starts
  const colX = {};
  let x = 130;
  for (const card of cards) {
    colX[card] = x;
    x += perRow(card) * step + 60;
  }
  const width = x;



  // where each chain row starts, the tallest group of dots sets the row height
  const rowY = {};
  let y = 40;
  for (const chain of chains) {
    rowY[chain] = y;
    const rows = d3.max(cards, card => Math.ceil(data.filter(d => d.chain === chain && d.card === card).length / perRow(card)));
    y += rows * step + 45;
  }
  const height = y;



  // dot positions: fill each group left to right, row by row
  const dots = [];
  for (const chain of chains) {
    for (const card of cards) {
      data.filter(d => d.chain === chain && d.card === card).forEach((d, i) => {
        dots.push({...d, x: colX[card] + (i % perRow(card)) * step + step / 2, y: rowY[chain] + 20 + Math.floor(i / perRow(card)) * step});
      });
    }
  }



  const container = d3.create("div").style("position", "relative");
  const svg = container.append("svg")
      .attr("viewBox", [0, 0, width, height])
      .style("width", "100%")
      .style("max-width", `${width}px`)
      .style("font", "12px sans-serif");



  // grade names on top
  svg.selectAll(".card-name").data(cards).join("text")
      .attr("x", d => colX[d])
      .attr("y", 16)
      .attr("font-weight", "bold")
      .text(d => d);



  for (const chain of chains) {
    const n = data.filter(d => d.chain === chain).length;
    svg.append("text").attr("x", 0).attr("y", rowY[chain] + 30).attr("font-weight", "bold").text(chain);
    svg.append("text").attr("x", 0).attr("y", rowY[chain] + 46).attr("fill", "#666").text(`n = ${n}`);
    for (const card of cards) {
      const count = data.filter(d => d.chain === chain && d.card === card).length;
      svg.append("text").attr("x", colX[card]).attr("y", rowY[chain] + 10).attr("fill", "#666").text(count);
    }
    svg.append("line")
        .attr("x1", 0).attr("x2", width)
        .attr("y1", rowY[chain] - 6).attr("y2", rowY[chain] - 6)
        .attr("stroke", "#eee");
  }



  const tip = container.append("div").attr("class", "q4-tip");
  const day = d => d instanceof Date ? d.toISOString().slice(0, 10) : d;



  svg.selectAll("circle").data(dots).join("circle")
      .attr("cx", d => d.x)
      .attr("cy", d => d.y)
      .attr("r", 3.2)
      .attr("fill", d => highlight === "All" || d.card === highlight ? color[d.card] : "#ece7df")
      .attr("stroke", d => d.card === "Not Yet Graded" ? "#9aa0a6" : "none")
      .on("mouseenter", (event, d) => {
        const earlier = d.latest_letter && d.latest_letter !== d.grade ? `<br>Earlier letter: ${d.latest_letter} on ${day(d.latest_letter_date)}` : "";
        let pending = "";
        if (d.grade === "Z") pending = ", Z: waiting for a hearing";
        if (d.grade === "P") pending = ", P: after a reopening";
        tip.style("opacity", 1).html(`<b>${d.dba}</b> (${d.boro})<br>${d.card}${pending} since ${day(d.grade_date)}${earlier}<br>Last inspection's grade: ${d.last_status}`);
      })
      .on("mousemove", event => {
        const [px, py] = d3.pointer(event, container.node());
        tip.style("left", `${px + 12}px`).style("top", `${py + 12}px`);
      })
      .on("mouseleave", () => tip.style("opacity", 0));



  return container.node();
}
```

### 2. First inspection scores

```js
const scores = FileAttachment("/data/q4-scores.csv").csv({typed: true});
const scoreSummary = FileAttachment("/data/q4-score-summary.csv").csv({typed: true});
const allScores = FileAttachment("/data/q1-scores.csv").csv({typed: true});
```

```js
display(scoreBars(scores, allScores, scoreSummary));
```

<p class="q4-caption">Each bar is the share of a chain's first inspections with that score. Blue scores are 13 or less and get an A right away, orange ones miss it and the inspector comes back. Routine initial inspections from 2023-01-01 to 2026-10-29, like Q1, Q5 and Q6. The city's file keeps about three years of inspections, so 2023 is only partly covered. The last bar is 45 points or more, and the bottom row is all restaurants in the city.</p>

```js
function scoreBars(scores, allScores, scoreSummary) {
  const maxScore = 45;
  const bin = s => Math.min(s, maxScore);
  const chains = ["Starbucks", "McDonald's", "Dunkin"];



  const rows = chains.map(chain => {
    const counts = d3.rollup(scores.filter(d => d.chain === chain), v => v.length, d => bin(d.score));
    return {name: chain, counts};
  });
  rows.push({name: "All restaurants", counts: d3.rollup(allScores, v => d3.sum(v, d => d.count), d => bin(d.score))});
  for (const row of rows) {
    row.total = d3.sum(row.counts.values());
    row.bars = d3.range(0, maxScore + 1).map(score => {
      const n = row.counts.get(score) || 0;
      return {row, score, n, share: n / row.total};
    });
    row.summary = scoreSummary.find(d => d.chain === row.name);
  }



  const width = 900;
  const marginLeft = 140;
  const marginRight = 240;
  const rowHeight = 100;
  const height = rows.length * rowHeight + 40;



  const x = d3.scaleBand().domain(d3.range(0, maxScore + 1)).range([marginLeft, width - marginRight]).padding(0.12);
  const y = d3.scaleLinear().domain([0, d3.max(rows, r => d3.max(r.bars, d => d.share))]).range([rowHeight - 25, 5]);
  const cutoff = x(14) - x.step() * x.padding() / 2;



  const container = d3.create("div").style("position", "relative");
  const svg = container.append("svg")
      .attr("viewBox", [0, 0, width, height])
      .style("width", "100%")
      .style("font", "12px sans-serif");
  const tip = container.append("div").attr("class", "q4-tip");



  rows.forEach((row, i) => {
    const g = svg.append("g").attr("transform", `translate(0,${i * rowHeight})`);
    const isCity = row.name === "All restaurants";



    g.append("text").attr("x", 0).attr("y", 30).attr("font-weight", "bold").attr("fill", isCity ? "#666" : "black").text(row.name);
    g.append("text").attr("x", 0).attr("y", 46).attr("fill", "#666").text(`${d3.format(",")(row.total)} first inspections`);



    g.selectAll("rect").data(row.bars).join("rect")
        .attr("x", d => x(d.score))
        .attr("y", d => y(d.share))
        .attr("width", x.bandwidth())
        .attr("height", d => y(0) - y(d.share))
        .attr("fill", d => d.score <= 13 ? "#2b59c3" : "#f29d38")
        .attr("opacity", isCity ? 0.55 : 1)
        .on("mouseenter", (event, d) => {
          tip.style("opacity", 1).html(`<b>${d.row.name}</b><br>Score ${d.score}${d.score === maxScore ? " or more" : ""}: ${d3.format(",")(d.n)} first inspections, ${d3.format(".1%")(d.share)}`);
        })
        .on("mousemove", event => {
          const [px, py] = d3.pointer(event, container.node());
          tip.style("left", `${Math.min(px + 12, container.node().clientWidth - 270)}px`).style("top", `${py + 12}px`);
        })
        .on("mouseleave", () => tip.style("opacity", 0));



    g.append("line")
        .attr("x1", marginLeft).attr("x2", width - marginRight)
        .attr("y1", y(0)).attr("y2", y(0))
        .attr("stroke", "#ccc");



    // what share of first inspections missed an A, and how many branches missed at least once
    g.append("text").attr("x", width - marginRight + 15).attr("y", 30)
        .attr("font-weight", "bold").attr("fill", "#d9772b")
        .text(`${row.summary.pct_missed_a.toFixed(1)}% missed an A`);
    g.append("text").attr("x", width - marginRight + 15).attr("y", 46).attr("fill", "#666")
        .text(isCity ? `${row.summary.pct_branches_missed_once.toFixed(0)}% of restaurants at least once` : `${row.summary.pct_branches_missed_once.toFixed(0)}% of branches at least once`);
  });



  svg.append("line")
      .attr("x1", cutoff).attr("x2", cutoff)
      .attr("y1", 0).attr("y2", rows.length * rowHeight - 20)
      .attr("stroke", "black").attr("stroke-dasharray", "4 3");
  svg.append("text")
      .attr("x", cutoff + 4).attr("y", 10)
      .attr("font-size", 11)
      .text("A cutoff, 13 | 14");



  svg.append("g")
      .attr("transform", `translate(0,${rows.length * rowHeight - 20})`)
      .call(d3.axisBottom(x).tickValues([0, 5, 10, 13, 20, 27, 35, 45]).tickFormat(d => d === maxScore ? "45+" : d));
  svg.append("text")
      .attr("x", (marginLeft + width - marginRight) / 2).attr("y", height - 2)
      .attr("text-anchor", "middle").attr("fill", "#666")
      .text("First inspection score, lower is better");



  return container.node();
}
```

## Simple analysis from the vision

```js
// const starbucks = scoreSummary.find(d => d.chain === "Starbucks");
// const mcdonalds = scoreSummary.find(d => d.chain === "McDonald's");
const dunkin = scoreSummary.find(d => d.chain === "Dunkin");
const city = scoreSummary.find(d => d.chain === "All restaurants");
```

- Today the cards hardly differ. At all three chains more than ${Math.floor(d3.min(summary, d => d.pct_A))}% of the graded branches show an A, and there is only a few B's and one C. The C and all the Grade Pending cards are at Dunkin.
- First inspections differ a lot more. Dunkin missed an A in ${Math.round(dunkin.pct_missed_a)}% of them, which is close to double than the Starbucks rate. McDonald's is in between.
- Many branches missed an A at least once in these three years. Almost all of them still show an A today, usually because the re-inspection goes better, so from the street you can't see any of it.
- Next to the whole city the chains still look good. The city misses an A in ${Math.round(city.pct_missed_a)}% of first inspections and has a long orange tail, the chain bars stay mostly left of the line.

<style>
.q4-caption {
  font-size: 13px;
  color: #6b6f7a;
  border-left: 2px solid #2b59c3;
  padding-left: 10px;
}
.q4-tip {
  position: absolute;
  pointer-events: none;
  opacity: 0;
  background: #22223b;
  color: #f2e9e4;
  border-left: 4px solid #2b59c3;
  border-radius: 8px;
  padding: 8px 11px;
  font-size: 12.5px;
  line-height: 1.5;
  box-shadow: 0 6px 18px rgba(34, 34, 59, 0.25);
  max-width: 260px;
}
</style>
