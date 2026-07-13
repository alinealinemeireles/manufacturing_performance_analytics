# Manufacturing Performance Analytics — Plastic Packaging Plant

> Final Project — Data & Quality Analytics
> Full pipeline: raw data → cleaning (Python) → database (MySQL) → analysis → Machine Learning → dashboard (Power BI)

## 1. Project overview

This project simulates a plastic packaging plant (bottles, caps, screen
printing, and hot foil decoration) and analyzes one year of its
production, quality, maintenance, and customer/supplier data. The goal
was to bring together, in one project, the kind of question I already
know well from my background in Quality Management (OEE, SPC, AQL
sampling, CAPA) with the data analytics tools I'm learning now — Python,
SQL, Power BI, and Machine Learning.

## 2. Business question

**Can integrated monitoring of production, quality, and maintenance
indicators support real-time decisions to reduce losses and improve
efficiency?**

More specific questions the project answers (notebook `13`):

1. What is the plant's operational performance, and what factors affect
   productivity and quality the most?
2. Which machines, shifts, and operators show the most performance
   variation and quality impact?
3. How do production signals relate to real customer complaints?
4. Does the plant operate within its capacity and process stability?
5. What are the main losses, and where should continuous improvement be
   prioritized?
6. How is operational health monitored in real time?
7. Can deviations be anticipated before they affect production?

## 3. Data source

The data is **simulated** — one year of production, machine downtime,
quality inspections, customer complaints, and nonconformances, built
following realistic rules (real ISO/ASTM standards, real AQL sampling
math, plausible defect rates). A simulated dataset let me build in the
manufacturing/quality domain I actually know, instead of working with a
generic public dataset.

- **Period:** 1 year (Jul/2025 to Jul/2026)
- **Tables:** ~30 fact and dimension tables, covering production,
  downtime, quality control (caps/bottles/ink), sales, complaints,
  suppliers, and CAPA

## 4. Technologies used

- **Analysis language:** Python (pandas, matplotlib, scikit-learn)
- **Database:** MySQL (SQL queries, rolling 52-week views on every
  fact table, plain views on every dimension table)
- **Machine Learning:** scikit-learn (Random Forest)
- **Dashboard:** Power BI
- **Version control:** Git

## 5. Repository structure

```
datasets/
  raw/         raw (untreated) data -- not committed to Git
  dim/         small reference tables (committed)
  processed/   cleaned data + ML predictions (produced by the notebooks)
scripts/
  notebook/           the 13 notebooks (01 to 13) + etl_lib.py
  machine_learning/   ml_lib.py -- functions shared by the 6 models
  sql_table/          SQL scripts that create the MySQL tables
  sql_view/           SQL scripts for the views (rolling 52-week window
                       on fact tables, plain views on dimension tables)
models/         the 6 trained Machine Learning models (.pkl)
power_bi/       the dashboard file (.pbix)
reports/        every chart, exported as .png
docs/           data dictionary
README.md
requirements.txt
.gitignore
```

## 6. How the pipeline works, notebook by notebook

**Run the notebooks in this exact order** — later notebooks read files
that earlier ones produce (notebook `13`, for instance, reads outputs
from stages 4, 5, and 6, so it has to run last).

### `01_import_and_inspect.ipynb` — first look at the raw data

Loads every raw CSV and just looks at it: `head()`, `info()`,
`isna().sum()`. No cleaning happens here on purpose — the goal is to
document what's actually wrong with the data (mixed-case categories,
disguised blanks like `"-"`, negative quantities, duplicate rows)
*before* touching anything, so the cleaning decisions in the next
notebook are based on evidence, not guesswork.

### `02_data_cleaning_production.ipynb` — cleaning + OEE

The most important notebook in the pipeline. Cleans the four
production tables and calculates the `LotId` traceability code and
OEE. All of the actual logic lives in `etl_lib.py`, not in the
notebook itself — the notebook just calls functions in the right
order and prints what happened at each step, so the *sequence* of
decisions is easy to follow even though the *implementation* is
centralized.

Key steps, in order:
1. Generic cleaning (same 5-function sequence on every table — see
   section 8 below).
2. Fill blank `MaterialLot` values forward (an empty cell almost always
   means "operator forgot to write it down", not "new lot started
   here").
3. Add calendar columns (`ISOWeek`, `ISOWeekday`) and `ShiftNumber`.
4. Build the `LotId` code.
5. Match every downtime event to the work order it interrupted.
6. Look up each machine's rated capacity and calculate
   `Availability`, `Performance`, `Quality`, and `OEE`.
7. Save the cleaned tables to `datasets/processed/`.

### `03_data_cleaning_quality.ipynb` — quality tables + dimensions

Cleans the eight quality-control tables (cap/bottle/ink × variable
inspection, attribute inspection, lot disposition), links every
inspection back to the `LotId` of the production that generated it,
computes SPC control limits and Cp/Cpk, and derives six dimension
tables (`dim_machine`, `dim_mold`, `dim_operator`, `dim_cap`,
`dim_bottle`, `dim_ink`) from the already-clean data.

### `04_mysql_load_and_views.ipynb` — database

Creates the MySQL database and tables (if they don't already exist),
loads every processed CSV, and creates the SQL views Power BI connects
to. Two kinds of view, both under `scripts/sql_view/`:

- **Fact-table views** (`01` to `04`) — filter to a **rolling 52-week
  window**: `WHERE Date >= (most recent Date in the table) - 52 weeks`.
  This means the view always shows "the last year of data as of the
  most recent record", without anyone needing to update a hard-coded
  date.
- **Dimension-table views** (`05_dim_views.sql`) — no time filter at
  all, just `SELECT * FROM the_table`. Machines, molds, and customers
  aren't a time series, so there's nothing to roll — the view exists
  purely so every table Power BI reads from follows the same `vw_*`
  naming convention, fact or dimension.

### `05_initial_analysis.ipynb` — first charts

Answers the business questions with charts, one per indicator:
production (OEE by process, weekly trend, OEE by machine, downtime
Pareto split into planned/unplanned), quality (FPY, defect Pareto, Cpk
heatmap), and maintenance (MTBF/MTTR by machine, planned vs. unplanned
split, downtime hours by process). It also has a dedicated section on
**downtime and production hours broken down every way a shift meeting
would ask for them**: total hours, by operator, by machine, by process,
and by stoppage reason — all in hours, not minutes, since that's the
unit a supervisor actually thinks in. See section 9 below for why "by
operator" needed a small design decision of its own.

### `06_kpi_scorecard.ipynb` — the rest of the scorecard

Completes the indicator set: planned vs. actual production, efficiency
by machine/shift/operator, scrap %, estimated rework, setup time,
schedule adherence, inspection approval rate, PPM, DPU/DPMO, lot
counts, a control chart example, and defect trends.

### `07_data_cleaning_qa.ipynb` and `08_quality_assurance_dashboard.ipynb`

Extend the project past the shop floor: customers, sales, complaints,
incoming raw material inspection, supplier complaints, and
nonconformance/CAPA. Same cleaning discipline as notebooks `02`-`03`.

### `09_ml_production_forecast.ipynb` — three forecasting models in one notebook

Three related weekly, per-process forecasts, built with the same
approach (lag features, 4-week rolling average as the honest baseline
to beat, Random Forest, date-based train/test split):

1. **Production forecast** — units produced next week, by process.
2. **Downtime forecast** — unplanned downtime hours next week, by
   process. Paired with #1, this gives a "production hours vs. stopped
   hours" view for the coming week.
3. **Rejected-units forecast** — units rejected next week, by process.
   Paired with #1, this gives a "produced vs. rejected" view for the
   coming week — a different question from the scrap-rate model in
   notebook `10`, which predicts a single order's risk, not a weekly
   plant-wide volume.

### `10_ml_scrap_prediction.ipynb`, `11_ml_lot_quality_classification.ipynb`, `12_ml_predictive_maintenance.ipynb`

Three more models, each answering a specific per-order or per-day
question rather than a weekly aggregate: expected scrap rate for a
given order, approve/reject risk for a given lot, and failure risk for
a given machine tomorrow. See section 10 for what each one is for and
how well it performs.

### `13_deep_dive_analysis.ipynb` — final synthesis

Runs last on purpose. Pulls together results from every other notebook
to answer the seven business questions and the central question, with
real numbers, not general statements.

## 7. Concepts used in this project

### OEE (Overall Equipment Effectiveness)

OEE is the standard Lean Manufacturing metric for how effectively a
machine is used, decomposed into three multiplied components:

- **Availability** = Run Time / Planned Time. Measures time lost to
  unplanned downtime.
- **Performance** = actual output rate / rated capacity. Measures speed
  loss — running slower than the machine's rated speed.
- **Quality** = good units / total units produced. Measures yield loss
  — units made but rejected.
- **OEE = Availability x Performance x Quality**

Multiplying the three is deliberate: a machine running at half speed
for its entire planned time hurts OEE exactly as much as a machine down
for half its planned time. A world-class OEE benchmark is around 85%;
40%-60% is typical for an unmanaged process.

### Lean Manufacturing and the Six Big Losses

Lean Manufacturing is a management philosophy focused on eliminating
waste ("muda") and maximizing customer value with the fewest resources.
OEE, together with the "six big losses" framework (breakdowns,
setup/changeover, minor stops, reduced speed, startup rejects,
production rejects), is one of its core diagnostic tools — used in this
project's loss-breakdown analysis (notebook `13`) to see exactly where
planned time is going.

### Six Sigma, DPU, and DPMO

Six Sigma is a data-driven methodology for reducing process variation
and defects. It measures performance in "sigma level" — the higher it
is, the fewer Defects Per Million Opportunities (DPMO). A 6-sigma
process runs around 3.4 DPMO; most real-world plants operate between 3
and 4 sigma. DPU (Defects Per Unit) and DPMO put defect rates from very
different sample sizes on a common scale, so processes can be compared
directly — used throughout the quality notebooks (`03`, `06`) for cap,
bottle, and ink attribute inspections.

### SPC (Statistical Process Control) and control charts

Instead of inspecting every unit, SPC samples small subgroups over time
and plots the subgroup average (X-bar) and range (R). If the process is
stable, both stay within control limits computed from the process's own
historical behavior (not the specification limits). A point outside
those limits signals the process has shifted and needs investigation —
this project computes X-bar/R control limits per characteristic x
machine x mold x product (notebook `03`) and plots an example chart
(notebook `06`).

### Cp / Cpk (Process Capability)

Cp asks whether the specification window would fit inside the process's
variation at all. Cpk asks the more useful question: given where the
process is actually centered, how much room is left before it goes out
of spec. Cpk is always ≤ Cp; a large gap between them means the process
isn't centered on target, not just "too spread out." Cpk ≥ 1.33 is a
common threshold for calling a process "capable."

### AQL sampling (ISO 2859-1)

Instead of inspecting 100% of a lot, AQL sampling checks a sample size
based on lot size and the desired inspection strictness ("General Level
II" in this project), and a defined number of defects in that sample
(Ac = accept, Re = reject) still passes for a given AQL (Acceptable
Quality Level — the maximum tolerable percentage defective). A Critical
characteristic typically uses a tight AQL like 0.10% — even a single
defect in the sample can reject the whole lot.

### Maintenance reliability metrics: MTBF and MTTR

- **MTBF (Mean Time Between Failures)** = total run hours / number of
  unplanned failures. Measures how reliable a machine is — a bigger
  number is better.
- **MTTR (Mean Time To Repair)** = average duration of an unplanned
  failure, in hours. Measures how quickly the plant recovers from a
  failure — a smaller number is better.

Both are computed strictly from genuine unplanned failures (equipment
breakdowns, material shortages) — not from planned changeovers or
preventive maintenance, since mixing the two would make a machine look
less reliable than it actually is (a planned stop is a management
decision, not an equipment failure). Both are reported in **hours**
throughout the project, not minutes, matching how a maintenance team
actually talks about downtime.

### The `LotId` traceability code

A 16-character code (`YYWWDTPMMOOOOOSS`) built for every production
record, encoding year, ISO week, weekday, shift, process, machine, work
order, and a raw-material lot sequence number. It's the mechanism that
lets any quality inspection be traced back to the exact work order and
material lot that produced it — a core requirement of ISO 9001's
traceability clause.

## 8. The five generic cleaning functions

Every fact table goes through the same sequence, in `etl_lib.py`,
before any table-specific logic runs:

1. `clean_disguised_blanks` — turns `-`, `--`, `/`, a lone space, etc.
   into a real `NaN`. Without this, `isna()` wouldn't catch them, and a
   maintenance technician named `"-"` could show up in a groupby.
2. `strip_extra_spaces` — trims and collapses whitespace in text
   columns.
3. `standardize_categories` — `.title()`-cases text so
   `INJECTION MOLDING` / `injection molding` / `Injection Molding `
   all become the same category.
4. `fix_negative_quantities` — applies `abs()` to quantity columns that
   should never be negative (a sign typo shouldn't cost a whole row).
5. `drop_duplicate_rows` — removes exact duplicate rows and reports how
   many, so nothing disappears silently.

## 9. A design decision worth explaining: "downtime hours by operator"

The downtime table doesn't have an `OperatorId` column — only the
maintenance technician who attended the stoppage. To get a meaningful
"hours stopped by operator" (notebook `05`), I link each stoppage to
the work order it interrupted (`MatchedWorkOrder`, computed in notebook
`02`), and from there to the operator who was running that order at
the time. That answers a different, more useful question than "which
technician fixed it": it shows which operator's shift absorbed the
downtime, which is what a production supervisor actually needs when
reviewing how a shift went.

## 10. The six Machine Learning models

All six use Random Forest, with simple hyperparameters and no
comparison across multiple algorithms — a deliberate choice to keep
the project focused rather than turning it into an algorithm
comparison exercise. All six split train/test **by date** (oldest
rows train, newest rows test), never randomly — shuffling first would
let the model "see" information from the future during training.

| Model | Notebook | Question it answers | Result |
|---|---|---|---|
| Production forecast | `09` | Units produced next week, by process | R²≈0.97 |
| Downtime forecast | `09` | Unplanned downtime hours next week, by process | R²≈0.91 |
| Rejected-units forecast | `09` | Units rejected next week, by process | R²≈0.99 |
| Scrap rate | `10` | Expected scrap % for a specific upcoming order | R²≈0.77 |
| Lot quality classification | `11` | Will this lot be approved or rejected? | ROC-AUC≈0.61 |
| Predictive maintenance | `12` | Will this machine fail tomorrow? | ROC-AUC≈0.72 |

Two results are honestly modest, and that's reported as such rather
than hidden: the lot classification model's signal is weak because lot
disposition depends heavily on AQL sampling randomness, not just
production conditions; the downtime forecast is close to its own
4-week moving-average baseline, meaning weekly downtime hours don't
have much more structure to learn beyond recent history. Both are
useful findings about the data, not failures of the modeling.

## 11. How to run the project

1. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Create a `.env` file at the project root with your MySQL credentials:
   ```
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password_here
   MYSQL_DB=manufacturing_performance_analytics
   ```
3. Run the notebooks **in order**, from `scripts/notebook/01...` through
   `scripts/notebook/13...` (`Run All` on each one). Notebook `04`
   creates the database, the tables, and the views on its own -- no
   manual SQL needed.
4. Open `power_bi/dashboard.pbix` and connect directly to the MySQL
   views (`vw_*`) — every fact table and every dimension table now has
   one.

## 12. Key results

*(From notebook `13`, based on the current data.)*

- **Plant-wide OEE: ~69%** (Availability 79%, Performance 90%, Quality
  98%).
- **Unplanned downtime is by far the biggest loss** (~22% of planned
  time) — well ahead of speed loss (~8%), quality loss (~2%), and
  setup/changeover (<1%). It's also the strongest correlation with
  work-order-level OEE (r=-0.89) — meaning that, order by order, no
  other factor moves OEE as much as how long the machine sat idle
  unexpectedly.
- **Process capability is strong:** 100% of machine x characteristic
  combinations clear a Cpk of 1.33 (the common "capable process"
  threshold). The bottleneck is operational (downtime), not structural
  — the plant *can* hit its quality targets consistently; what's
  costing it is uptime, not precision.
- **The link between production signals and real customer complaints is
  weak** in this dataset (correlation ≈ 0, not significant) — an honest
  result showing that lot approve/reject decisions depend more on AQL
  sampling variation than on production conditions. Reporting this
  honestly, instead of assuming a stronger link exists, is itself a
  more defensible conclusion than an untested claim would be.
- **Six Machine Learning models** turn historical monitoring into a
  forward-looking one: two of the six (lot classification, downtime
  forecast) have modest performance, and that's reported as a genuine
  finding about the data's limits, not smoothed over.

## 13. Limitations

- All data is simulated. Machine Learning results (especially the
  production forecast) may look better than they would on real data
  with real demand variation.
- One year of history isn't enough to learn true seasonality.
- The "rework" indicator is an estimate (there's no rework transaction
  in the raw data), computed from each quality characteristic's
  reaction plan.
- All six Machine Learning models use Random Forest, with simple
  hyperparameters — I didn't compare several algorithms, on purpose, to
  keep the project focused.

## 14. Authorship

Individual project — Aline.
