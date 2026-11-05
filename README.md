# Behind the A: What NYC Restaurant Grades Tell You

Every New York restaurant posts a letter grade by its door. This project looks at what an A actually tells a diner: how restaurants earn it, where and for whom it is harder to get, which violations are behind low scores, and what happens to restaurants that fail. Built with Observable Framework and D3 for NYU CS-GY 6313 Information Visualization (Fall 2026).

**Live site:** https://simonewang02.github.io/nyc-restaurant-grades/

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

## Scripts

```bash
python3 scripts/download.py   # use NYC API to download today's raw data and store it in data/raw
python3 scripts/explore.py    # returns the shape of the CSV and the header columns
python3 scripts/clean.py      # drops never-inspected restaurants, fixes types, splits into 3 tables in data/interim
```

`clean.py` writes three tables to `data/interim/` (ignored by git, rebuilt from the raw CSV):

```
restaurants.csv   one row per restaurant (CAMIS)
inspections.csv   one row per inspection (CAMIS + date + type)
violations.csv    one row per cited violation
```

## Run the site

Fetch today's data using NYC API and store it in data/raw (make sure to have at least one CSV before processing the data)

```bash
python3 scripts/download.py
```

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
Milestone1_Proposal.pdf         Milestone 1 proposal
Milestone1_Feedback.pdf         Milestone 1 feedback from the instructors
```

## Work Distribution

### Q1-Q3 (Simone Wang)

Run after `clean.py`. The scripts use pandas (`pip install pandas`).

```bash
python3 scripts/question-specific/question-1.py   # number of first inspections per score
python3 scripts/question-specific/question-2.py   # latest grade per restaurant, counted by NTA and borough
python3 scripts/question-specific/question-3.py   # box plot numbers of first-inspection scores per cuisine
```

- Each script writes one or two CSV files to `src/data/` (`q1-*`, `q2-*`, `q3-*`), which the Q1, Q2 and Q3 pages read.
- Q1 and Q3 use only first inspections ("Cycle Inspection / Initial Inspection") that have a score.
- Q3 keeps cuisines with at least 50 first inspections (`MIN_COUNT` in `question-3.py`).

### Q4-Q6 (Yiyang)

Run after `clean.py`. The scripts use pandas, and the chart drafts use matplotlib (`pip install pandas matplotlib`).

```bash
python3 scripts/download-nta-lookup.py                # 2010 NTA code -> name list, saved in data/reference/
python3 scripts/question-specific/question-4.py       # chain branches and their latest grade
python3 scripts/question-specific/question-5.py       # citations per violation code
python3 scripts/question-specific/question-6.py       # pest citation rates by NTA and cuisine
python3 scripts/question-specific/plot-q4-q6.py       # base charts for the sketches, saved to ../q4-q6-figures/
```

- Q5 and Q6 use routine initial inspections from 2023-01-01 to 2026-10-29 (set in `scripts/question-specific/common.py`).
- The NTA names come from DCP's [2010 Census Tracts](https://data.cityofnewyork.us/City-Government/2010-Census-Tracts/bmjq-373p) table (`ntacode`, `ntaname`), downloaded on 2026-11-02.
- `data/manual/q4-name-decisions.csv` lists the 12 chain names we checked by hand, with a reason and a source link for each.
- The write-up for these questions is [docs/Milestone2_Q4-Q6_draft.md](docs/Milestone2_Q4-Q6_draft.md).

### Q7-Q8 (Yabo Wang)

Run after `clean.py`. The scripts use pandas and numpy.

```bash
python3 scripts/question-specific/question-7.py   # pairs each first inspection with its re-inspection
python3 scripts/question-specific/question-8.py   # follows each closure to its reopening
```

- Both write small CSV and JSON files to `src/data/` (`q7-*`, `q8-*`), which the Q7 and Q8 pages read.
- Q7 and Q8 use all routine initial inspections in the snapshot, so their shares of first inspections differ slightly from Q5 and Q6, which start on 2023-01-01.

## AI Disclosure

### Simone Wang

Used Claude to help polish writing, find background sources, scaffold and check code, write python scripts and set up the GitHub Pages deployment.

### Yiyang Zhang

I used ChatGPT to get suggestions on optimizing the project's directory structure, translate several technical terms, and rewrite tens of words or sentences in the documentation to improve readability. I also made 5-10 searches using Google Gemini.

### Yabo Wang

Used Claude to write Python scripts, verify how Q7 pairs first inspections with re-inspections and how Q8 matches closures to reopenings, and polish the text of the Q7 and Q8 pages.