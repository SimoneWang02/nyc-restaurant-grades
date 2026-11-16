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
5. Which violations are cited most often, and what share of them are critical?
6. Where do mice, roaches and flies show up most?
7. Do restaurants that miss an A on the first inspection recover at the re-inspection?
8. Which restaurants get closed, and how long does it take them to reopen?

## Data

- **DOHMH New York City Restaurant Inspection Results** (NYC Open Data, `43nn-pn8j`): https://data.cityofnewyork.us/d/43nn-pn8j
  Collected by NYC Health Department inspectors during unannounced inspections. One row per violation per inspection; covers currently active restaurants and about three years of inspections. Updated daily, so we work from a dated snapshot.
- **2010 Neighborhood Tabulation Areas** (NYC Department of City Planning), used as the base map for Q2 and Q6. The inspection data uses 2010 NTA codes, so the maps use 2010 NTAs too (not the newer 2020 ones). NYC Open Data no longer has the 2010 NTA boundary file, so we build it from DCP's [2010 Census Tracts](https://data.cityofnewyork.us/City-Government/2010-Census-Tracts/bmjq-373p) table: 2010 NTAs are made of whole tracts, and merging the tracts by their `ntacode` gives the NTA shapes (`scripts/download-nta-boundaries.py`, output `src/data/nta-2010.json`).

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
feedbacks/                      Milestone 1 and 2 feedback from the instructors
docs/                           Milestone 2 write-up for Q4-Q6
```

## Work Distribution

### Q1-Q3 (Simone Wang)

Run after `clean.py`. The scripts use pandas (`pip install pandas`).

```bash
python3 scripts/question-specific/question-1.py   # number of first inspections per score
python3 scripts/question-specific/question-2.py   # current grade per restaurant (shared with Q4), counted by NTA and borough
python3 scripts/question-specific/question-3.py   # box plot numbers of first-inspection scores per cuisine
python3 scripts/download-nta-boundaries.py        # 2010 NTA shapes for the Q2 map (needs Node.js, runs mapshaper with npx)
```

- Each script writes CSV and JSON files to `src/data/` (`q1-*`, `q2-*`, `q3-*`), which the Q1, Q2 and Q3 pages read.
- `question-2.py` needs the NTA name list from `scripts/download-nta-lookup.py` (in `data/reference/`). The map shapes only need to be rebuilt if the source changes; `src/data/nta-2010.json` is in the repo.
- Q1 and Q3 use only first inspections ("Cycle Inspection / Initial Inspection") that have a score, from 2023-01-01 to 2026-10-29 (the same window as Q5 and Q6, set in `scripts/question-specific/common.py`).
- Q3 keeps cuisines with at least 50 first inspections (`MIN_COUNT` in `question-3.py`).

### Q4-Q6 (Yiyang Zhang)

Run after `clean.py`. The scripts use pandas, and the sketch base charts are manually created with matplotlib (`pip install pandas matplotlib`), then hand-drawn in Milestone 1.

```bash
python3 scripts/download-nta-lookup.py                # 2010 NTA code -> name list, saved in data/reference/
python3 scripts/question-specific/question-4.py       # chain branches, their current grade (shared with Q2) and their first inspection scores
python3 scripts/question-specific/question-5.py       # citations per violation code, and how often each code comes with a missed A
python3 scripts/question-specific/question-6.py       # pest citation rates by NTA and cuisine
python3 scripts/question-specific/plot-q4-q6.py       # base charts for the Milestone 2 sketches, saved to ../q4-q6-figures/
```

- Each script writes CSV and JSON files to `src/data/` (`q4-*`, `q5-*`, `q6-*`), which the Q4, Q5 and Q6 pages read. The D3 charts are in those pages.
- The Q4 scores, Q5 and Q6 use routine initial inspections from 2023-01-01 to 2026-10-29 (set in `scripts/question-specific/common.py`). The Q4 grade cards use each branch's current grade, same as Q2.
- A score over 13 counts as a missed A, in the Q4 score chart and the Q5 scatter.
- Q6 compares groups with at least 30 inspections (`MIN_INSPECTIONS` in `question-6.py`). Unknown, Other and Bottled Beverages are not cuisines, so they are left out of the cuisine comparison.
- The Q6 map uses `src/data/nta-2010.json`, the same shapes as the Q2 map.
- The NTA names come from DCP's [2010 Census Tracts](https://data.cityofnewyork.us/City-Government/2010-Census-Tracts/bmjq-373p) table (`ntacode`, `ntaname`), downloaded on 2026-11-02.
- `data/manual/q4-name-decisions.csv` lists the 12 chain names we checked by hand, with a reason and a source link for each.
- The Milestone 2 write-up for these questions is kept in [docs/Milestone2_Q4-Q6_draft.md](docs/Milestone2_Q4-Q6_draft.md).

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

for milestone 2, I used ChatGPT to get suggestions on optimizing the project's directory structure, translate several technical terms, and rewrite tens of words or sentences in the documentation to improve readability. I also made 5-10 searches using Google Gemini. ChatGPT also helped me for color selection.

For milestone 3, I used ChatGPT to polish the text for description sentences(for grammar and clarity), and I also asked once to ChatGPT to find is there any error in milestone 2 write-up for Q4-Q6, it helped me identify one directory error(adopted), and gave me some improve advises(not adopted because they are not errors). For the charts, I did not use gen AI tools, but I did ask Gemini to search for ~20 coding information and documentation.

### Yabo Wang

Used Claude to write Python scripts, verify how Q7 pairs first inspections with re-inspections and how Q8 matches closures to reopenings, and polish the text of the Q7 and Q8 pages.