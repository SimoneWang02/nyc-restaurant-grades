# Behind the A: What NYC Restaurant Grades Tell You

Every New York restaurant posts a letter grade by its door. This project looks at what an A actually tells a diner: how restaurants earn it, where and for whom it is harder to get, which violations are behind low scores, and what happens to restaurants that fail. Built with Observable Framework and D3 for NYU CS-GY 6313 Information Visualization (Fall 2026).

**Live site:** TODO

## Team: Night's Watch

- Simone Wang (sw7317)
- Yabo Wang (yw10450)
- Yiyang Zhang (yz12500)

## Questions

1. How does a restaurant earn its A, and how are first-inspection scores distributed?
2. How much does the share of A grades vary by borough and neighborhood?
3. How much do scores differ by cuisine?
4. Do branches of the same chain get similar grades?
5. Which violations drive scores up, and what share of them are critical?
6. Where do mice, roaches and flies show up most?
7. Do restaurants that miss an A on the first inspection recover at the re-inspection?
8. Which restaurants get closed, and how long does it take them to reopen?

## Data

- **DOHMH New York City Restaurant Inspection Results** (NYC Open Data, `43nn-pn8j`): https://data.cityofnewyork.us/d/43nn-pn8j
  Collected by NYC Health Department inspectors during unannounced inspections. One row per violation per inspection; covers currently active restaurants and about three years of inspections. Updated daily, so we work from a dated snapshot.
- **2010 Neighborhood Tabulation Areas** (NYC Department of City Planning), used as the base map for Q2.

The raw CSV is large and is not stored in this repo. Download it to `data/raw/` (ignored by git):

```
https://data.cityofnewyork.us/api/views/43nn-pn8j/rows.csv?accessType=DOWNLOAD
```

## Run the site

Requires Node.js 18 or later.

```bash
npm install
npm run dev       # preview at http://127.0.0.1:3000, reloads on save
npm run build     # static site in dist/
npm run clean     # clear the Framework cache
```

## Repo layout

```
observablehq.config.js          site title, sidebar order and stylesheet
src/custom-style.css            site-wide CSS (Framework defaults plus our tweaks)
src/index.md                    home page
src/questions/question-N.md     one page per question (1 to 8)
src/markdown-cheatsheet.md      Markdown and Framework syntax reference (temporary)
Project_Proposal.pdf            Milestone 1 proposal
```

Planned: `src/data/` for processed data and `src/components/` for D3 chart code.

## Use of AI

We used Claude to help polish writing, find background sources, and scaffold and check code.
