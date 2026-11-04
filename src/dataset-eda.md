---
title: Dataset EDA
---

# What's in the data

Before getting into the questions, we wanted to see what we're actually working with: what the raw file from NYC Open Data looks like, what we cleaned up, and what's left after. The raw CSV is way too big to put on the site, so everything here comes from a small summary file (`src/data/eda.json`) that `scripts/eda.py` spits out.

```js
const eda = FileAttachment("/data/eda.json").json();
const format = d3.format(",");
const percentage = d3.format(".1%");
const countFormat = {n: format, share: percentage};
```

**Snapshot:** ${eda.snapshot}.

Inspections go from **${eda.dates.min}** to **${eda.dates.max}**.

<div class="grid grid-cols-4">
  <div class="card">
    <h2>Raw rows</h2>
    <span class="big">${format(eda.raw.rows)}</span>
  </div>
  <div class="card">
    <h2>Restaurants</h2>
    <span class="big">${format(eda.tables.restaurants.rows)}</span>
  </div>
  <div class="card">
    <h2>Inspections</h2>
    <span class="big">${format(eda.tables.inspections.rows)}</span>
  </div>
  <div class="card">
    <h2>Violations</h2>
    <span class="big">${format(eda.tables.violations.rows)}</span>
  </div>
</div>

## Raw CSV

The raw file has ${format(eda.raw.rows)} rows and ${eda.raw.columns} columns, covering ${format(eda.raw.restaurants)} restaurants. One thing to know up front: each row is one *violation*, not one inspection. If an inspector writes up five things in one visit, that visit shows up five times, with the same date, score and grade copied onto every row.

Here are the first 5 rows:

```js
display(Inputs.table(eda.raw.head, {layout: "auto"}));
```

## What each column means

| Field | Meaning |
|---|---|
| CAMIS | Unique ID of the restaurant. Links all of its rows. |
| DBA | "Doing business as": the restaurant's public name |
| BORO | Borough (Manhattan, Brooklyn, Queens, Bronx, Staten Island) |
| BUILDING | Building number of the address |
| STREET | Street name of the address |
| ZIPCODE | ZIP code |
| PHONE | Phone number |
| CUISINE DESCRIPTION | Type of food, as reported by the restaurant |
| INSPECTION DATE | Date of the inspection. 01/01/1900 means not inspected yet. |
| ACTION | What the Health Department did: violations cited, no violations, closed, re-opened or re-closed |
| VIOLATION CODE | Code for the violation, e.g. 04L is mice |
| VIOLATION DESCRIPTION | What the violation code means, in words |
| CRITICAL FLAG | Critical (more likely to cause foodborne illness), Not Critical, or Not Applicable |
| SCORE | Total points for the inspection. Lower is better; 0 to 13 is an A. |
| GRADE | A, B or C; N = not yet graded; Z = grade pending; P = grade pending after a reopening. Blank when no grade was given. |
| GRADE DATE | Date the grade was given |
| RECORD DATE | When the city made this file (same on every row) |
| INSPECTION TYPE | Program and visit type, such as Cycle Inspection / Initial Inspection |
| Latitude | Latitude of the address. 0 means unknown. |
| Longitude | Longitude of the address. 0 means unknown. |
| Community Board | Community district: borough digit plus district number, such as 107 |
| Council District | City Council district |
| Census Tract | Census tract of the address |
| BIN | Building Identification Number (city building ID) |
| BBL | Borough, block and lot: the city's tax lot ID |
| NTA | Neighborhood Tabulation Area code (2010 boundaries), such as BX62. Used for the Q2 map. |
| Location | Latitude and longitude again, just as a map point |

## What we cleaned

1. Threw out restaurants that haven't been inspected yet. The city gives them a fake date of 01/01/1900 and no score. That's ${format(eda.raw.placeholder_rows)} rows from ${format(eda.raw.placeholder_restaurants)} restaurants.
2. Turned dates into actual dates, and scores and coordinates into numbers. Everything comes in as text.
3. Some missing values pretend to be real ones, like a borough of "0" or a latitude of 0. We made those blank.
4. Split everything into three tables: restaurants, inspections and violations. CAMIS ties them together, and one inspection is a CAMIS + date + inspection type.

## One restaurant, before and after

To see what the split actually does, here's one restaurant (${eda.example.camis}). It has ${eda.example.raw.length} rows in the raw file, which turn into ${eda.example.inspections.length} inspections and ${eda.example.violations.length} violations.

The raw rows (just the useful columns):

```js
display(Inputs.table(eda.example.raw, {layout: "auto"}));
```

Same restaurant in the inspections table, one row per visit:

```js
display(Inputs.table(eda.example.inspections, {layout: "auto"}));
```

And in the violations table, one row per thing the inspector wrote up:

```js
display(Inputs.table(eda.example.violations, {layout: "auto"}));
```

## The three tables

### Restaurants

One row per restaurant, with its name, cuisine, borough and location. ${format(eda.tables.restaurants.rows)} rows total.

```js
display(Inputs.table(eda.tables.restaurants.head, {layout: "auto"}));
```

### Inspections

One row per visit, with the score, the grade and what the inspector did. ${format(eda.tables.inspections.rows)} rows.

```js
display(Inputs.table(eda.tables.inspections.head, {layout: "auto"}));
```

### Violations

One row per violation, with the code, what it means and whether it's critical. ${format(eda.tables.violations.rows)} rows.

```js
display(Inputs.table(eda.tables.violations.head, {layout: "auto"}));
```

### What's still missing

Pick a table to see how many blanks each column has after cleaning.

```js
const table = view(Inputs.radio(["restaurants", "inspections", "violations"], {label: "Table", value: "restaurants"}));
```

```js
display(Inputs.table(eda.tables[table].missing, {layout: "auto", sort: "missing", reverse: true, format: {missing: format, share: percentage}}));
```

## The columns we care about most

Our questions filter or group by these, so it's worth knowing which values show up and how often.

### Inspection type

```js
display(Inputs.table(eda.counts.inspection_type, {layout: "auto", format: countFormat}));
```

### Grade

Lots of inspections have no grade, and that's mostly on purpose. If a restaurant scores over 13 on its first visit, it doesn't get a grade until the inspector comes back. N, Z and P all mean "pending" in some way: not graded yet, grade pending, and pending after a reopening.

```js
display(Inputs.table(eda.counts.grade, {layout: "auto", format: countFormat}));
```

### Action

```js
display(Inputs.table(eda.counts.action, {layout: "auto", format: countFormat}));
```

### Borough (restaurants)

```js
display(Inputs.table(eda.counts.boro, {layout: "auto", format: countFormat}));
```

### Critical flag (violations)

```js
display(Inputs.table(eda.counts.critical_flag, {layout: "auto", format: countFormat}));
```

## Inspections per year

The city only keeps restaurants that are open right now, plus roughly their last three years of inspections. So a few old ones are still hanging around, but almost everything is from 2023 on.

```js
display(yearChart(eda.dates.per_year, {width}));
```

```js
function yearChart(data, {width}) {   // using {width}, Observable set max available size of container
  const margin = {top: 0, right: 0, bottom: 60, left: 65};

  const dims = {
    width: width - margin.left - margin.right,
    height: 240,
    margin: margin
  };

  const chart_svg = d3.create("svg")
    .attr("width", dims.width + dims.margin.left + dims.margin.right)
    .attr("height", dims.height + dims.margin.top + dims.margin.bottom);

  const chart = chart_svg.append("g")
    .attr("transform", `translate(${dims.margin.left}, ${dims.margin.top})`)
    .attr("width", dims.width)
    .attr("height", dims.height);

  const x = d3.scaleBand()
    .domain(data.map((d) => d.year))
    .range([0, dims.width])
    .padding(0.15);

  const y = d3.scaleLinear()
    .domain([0, d3.max(data, (d) => d.inspections)])
    .range([dims.height, 0]);

  chart.append("g")
    .attr("transform", `translate(0, ${dims.height})`)
    .call(d3.axisBottom(x));

  chart.append("g")
    .call(d3.axisLeft(y).ticks(5));

  chart.append("text")
    .attr("x", dims.width / 2)
    .attr("y", dims.height + 40)
    .attr("text-anchor", "middle")
    .text("Year");

  chart.append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -dims.height / 2)
    .attr("y", -50)
    .attr("text-anchor", "middle")
    .text("Inspections");

  chart.selectAll("rect.year")
    .data(data)
    .join("rect")
      .attr("class", "year")
      .style("fill", "var(--color-accent)")
      .attr("x", (d) => x(d.year))
      .attr("y", (d) => y(d.inspections))
      .attr("width", x.bandwidth())
      .attr("height", (d) => dims.height - y(d.inspections))
    .append("title")
      .text((d) => `${d.year}: ${format(d.inspections)} inspections`);

  return chart_svg.node();
}
```
