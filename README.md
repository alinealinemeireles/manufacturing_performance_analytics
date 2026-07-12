# Manufacturing Performance Analytics

This project started as a way to apply, in one single case study, the
things I've been learning in Data Analytics: SQL, Python, Power BI, and
Machine Learning. I'm a Chemical Engineer with a background in Integrated
Management Systems (ISO 9001, 14001, 22716, 22000), and I'm currently
moving from Quality Management into Data & Quality Analytics -- so
instead of using a generic sales dataset like most portfolio projects do,
I built a simulated plastic packaging plant (bottles, caps, screen
printing and hot foil decoration) so I could work with the kind of data
and questions I actually know from the shop floor: OEE, SPC, AQL
sampling, non-conformances, CAPA.

> **Language note:** the data (columns, values, code) is in English. My
> full study notes about the project (`docs/Guia_do_Projeto.docx` / `.pdf`)
> are in Portuguese, since that's the language I think in when I'm
> explaining a concept to myself -- that document is a much longer,
> step-by-step walkthrough of every notebook, formula, and design
> decision. This README is the English-language summary of it: shorter,
> but I've pulled the parts that matter most (formulas, table structure,
> reasoning behind the trickier decisions) into the sections below so
> non-Portuguese readers aren't missing anything essential.

---

## Why this topic

Most of the portfolio projects I looked at while studying use sales,
marketing, or finance data. I didn't want to build another one of those --
partly because it's been done a thousand times, and partly because I
already know the manufacturing/quality world from my actual job
experience, so I could tell if the numbers I was generating made sense
or not. A packaging plant selling to cosmetics companies also let me use
things I already understood well (ISO 2859-1 sampling, control charts,
CAPA workflows) instead of learning both the tool *and* the domain at
the same time.

## How the project actually grew

It didn't start with this scope. Roughly, it went:

1. **Production data + OEE.** First version was just: can I simulate a
   believable production dataset and compute OEE correctly (Availability
   x Performance x Quality)?
2. **Quality control.** Once production existed, it made sense to add
   SPC and AQL sampling on top of it -- caps and bottles need real
   incoming/in-process inspection in a real plant, so I added that.
3. **Maintenance.** Downtime causes, MTBF/MTTR -- this came from
   noticing the production numbers needed *some* explanation for why
   machines weren't always available.
4. **Quality Assurance (customers, suppliers, NC/CAPA).** At some point
   I realized that "quality" in a real company isn't just what happens
   inside the plant -- customers complain, suppliers send bad raw
   material, and there's a formal non-conformance/CAPA system tracking
   all of it. So I added that whole layer.
5. **Machine Learning.** Last addition. I didn't want to just bolt a
   model onto the project to say "it has ML" -- each of the four models
   here answers a specific question a plant would actually ask
   (production forecast, scrap drivers, lot rejection risk, predictive
   maintenance).

I mention this because the project doesn't read like it was planned end
to end from day one -- it wasn't. Each stage exists because the previous
one raised a question the data couldn't answer yet.

---

## The question I'm trying to answer

> Can watching production, quality, and maintenance data together
> actually help make better decisions and cut down on losses -- or is
> that just a nice idea that doesn't hold up once you look at real
> numbers?

I break this down into seven smaller questions, answered with actual
numbers from the data in `scripts/notebook/13_deep_dive_analysis.ipynb`
(the last notebook -- see below for why it runs last). I revisited these
questions once the Quality Assurance data and the ML models existed,
because a couple of the original questions were answered with weaker
evidence than what I had available by the end:

| # | Question | What changed |
|---|---|---|
| Q1, Q2, Q4 | Real-time performance, machine/shift/operator variability, capacity & stability | Kept as-is |
| Q3 | Which indicators matter most to customer satisfaction | Rewritten to use real customer complaint data instead of an internal proxy I was using before that data existed |
| Q5, Q7 | Main losses / where to focus improvement; can problems be anticipated | Backed up with the actual ML results instead of just a historical chart |
| Q6 | Real-time monitoring for daily meetings | Shortened -- I was repeating things already explained elsewhere in this README |

<details>
<summary>The seven questions, spelled out in full (click to expand)</summary>

1. What is the plant's real-time operational performance, and which
   factors most impact productivity and quality?
2. Which machines, shifts, and operators show the most performance
   variability and the biggest impact on quality?
3. How do production signals relate to *real* customer complaints, and
   which ones matter most to customer satisfaction?
4. Does the plant operate within its capacity and process stability
   well enough to guarantee compliance and customer satisfaction?
5. What are the main operational losses, and where should continuous
   improvement be prioritized?
6. How is operational and QMS health monitored in real time?
7. Which factors influence overall performance, and can deviations be
   anticipated?

</details>

---

## Repository structure

```
manufacturing-performance-analytics/
├── datasets/
│   ├── raw/          # raw CSV exports, as received
│   ├── dim/           # reference/master data (small, kept in git)
│   └── processed/     # cleaned data + ML prediction outputs
├── scripts/
│   ├── notebook/            # 13 Jupyter notebooks + etl_lib.py
│   ├── machine_learning/    # ml_lib.py -- shared ML helper functions
│   ├── sql_table/           # MySQL table creation + loading script
│   └── sql_view/            # MySQL rolling 52-week views
├── models/              # trained models (.pkl files)
├── power_bi/            # .pbix dashboard files go here
├── docs/                # data dictionary + my study notes (PT)
├── reports/             # every chart, exported as PNG
├── requirements.txt
└── .gitignore
```

This layout keeps five layers clearly separated: data (`datasets/`),
transformation/analysis/ML logic (`scripts/`), trained models
(`models/`), dashboards (`power_bi/`), and supporting documentation
(`docs/`, `reports/`). It's the same discipline any professional data
engineering project follows: never mix code with data, and never mix
raw data with processed data in the same folder.

### About the file encoding

Every CSV here is saved as UTF-8 with a BOM (`encoding='utf-8-sig'`). I
ran into this the hard way: without the BOM, Excel opens the file
assuming a different encoding and all the accented characters (é, ã, ç)
turn into garbage. Adding the BOM fixed it. MySQL doesn't care either
way since `to_sql` writes the values directly, not the raw file bytes --
it only matters when someone opens the CSV file itself.

## Data

The raw and reference tables are shared through Google Drive (see the
project brief for the link). A couple of the quality-control tables get
pretty wide once exported (tens of MB), so `datasets/raw/` and
`datasets/processed/` are git-ignored -- you regenerate them by running
the notebooks, or grab them from Drive. `datasets/dim/` is small enough
to just keep in the repo.

---

## How to run this

```bash
git clone <this-repo>
cd manufacturing-performance-analytics
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Run the notebooks **in order** -- the last one especially depends on
files the earlier ones create:

```
01_import_and_inspect.ipynb
02_data_cleaning_production.ipynb
03_data_cleaning_quality.ipynb
04_mysql_load_and_views.ipynb            (needs a MySQL server, see below)
05_initial_analysis.ipynb
06_kpi_scorecard.ipynb
07_data_cleaning_qa.ipynb
08_quality_assurance_dashboard.ipynb
09_ml_production_forecast.ipynb
10_ml_scrap_prediction.ipynb
11_ml_lot_quality_classification.ipynb
12_ml_predictive_maintenance.ipynb
13_deep_dive_analysis.ipynb              (run this one last)
```

### MySQL

```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=analytics
export MYSQL_PASSWORD=your_password_here
export MYSQL_DB=manufacturing_performance_analytics

mysql -u "$MYSQL_USER" -p -e "CREATE DATABASE $MYSQL_DB CHARACTER SET utf8mb4;"
mysql -u "$MYSQL_USER" -p "$MYSQL_DB" < scripts/sql_table/01_create_fact_tables.sql
mysql -u "$MYSQL_USER" -p "$MYSQL_DB" < scripts/sql_table/02_create_dim_tables.sql
python scripts/sql_table/03_load_data.py
mysql -u "$MYSQL_USER" -p "$MYSQL_DB" < scripts/sql_view/01_production_by_process_52w.sql
mysql -u "$MYSQL_USER" -p "$MYSQL_DB" < scripts/sql_view/02_downtime_material_plan_52w.sql
mysql -u "$MYSQL_USER" -p "$MYSQL_DB" < scripts/sql_view/03_quality_control_52w.sql
mysql -u "$MYSQL_USER" -p "$MYSQL_DB" < scripts/sql_view/04_quality_assurance_52w.sql
```

Power BI should connect to the views (`vw_*`), not the raw tables --
that's what keeps the 52-week window and the planned/unplanned split
working automatically. `.pbix` files go in `power_bi/`.

The 52-week window isn't a scheduled job -- each view filters by
`Date >= (most recent date in the table - 52 weeks)`, and since a SQL
`VIEW` re-runs its query on every read, the window shifts forward by
itself the moment a new production record is inserted. Downtime gets
three views: one combined (`vw_fact_downtime_52w`) and two split
(`vw_fact_downtime_planned_52w` / `..._unplanned_52w`), so a report is
structurally prevented from mixing planned and unplanned stops on the
same Pareto by accident.

---

## What's in each stage

**Stage 1-2 -- first look (`01`).** Load everything, then actually look
at it before touching anything: `df.head(30)` for a row-by-row visual
gut check, `df.info()` for column names/types/non-null counts, and
`df.isna().sum()` for missing values, column by column. I kept "look"
and "fix" as separate steps on purpose, mostly so I'd have to actually
write down what was wrong before jumping to fix it. That diagnostic
pass surfaced the classic shop-floor data problems across the four
production tables: inconsistent category casing (`Injection Molding`,
`injection molding`, `INJECTION MOLDING`), missing values, impossible
negative quantities (a negative `RejectedQty` -- you can't reject "-12"
units), duplicate rows, and nulls disguised as text (a lone space, a
dash `-`, a slash `/`). If those slip through uncaught, the error
propagates silently into every downstream indicator (OEE, Cp/Cpk,
MTBF) -- so this pass matters more than it looks like it should.

**Stage 3 -- cleaning, feature engineering, MySQL (`02`, `03`, `04`).**
The biggest chunk of work. All the transformation logic lives in one
reusable module, `scripts/notebook/etl_lib.py`, organized into six
sections, so every notebook that needs to "clean this column" or
"calculate OEE" calls the exact same tested code and results never
drift between notebooks. I ended up doing the cleaning in Python
instead of SQL mainly because several rules are sequential and depend
on the previous row's history -- most notably the `LotId` traceability
code (explained below), which depends on comparing each row to the row
before it for the same work order. That's a natural `for` loop in
pandas but awkward as a single SQL query; MySQL only enters once the
data is already clean, as the serving layer for Power BI, not the place
where I debug data-quality logic.

Generic cleaning is applied to every fact table, in this order:
`normalize_placeholder_nulls` (turn `-`, `--`, `/`, `//`, a lone space,
etc. into a real `NaN`) → `strip_whitespace` → `standardize_categories`
(Title Case, so `Injection Molding` everywhere) →
`fix_negative_quantities` (absolute value on quantity columns that
should never be negative) → `drop_exact_duplicates`. Every cleaning
function prints how many rows it affected, so the cleaning stays
auditable instead of silently dropping data.

Two calendar columns feed almost everything downstream: `ISOWeek` (the
ISO week number -- Monday-Sunday, week 1 is the one containing the
year's first Thursday, which guarantees every week has a full 7 days)
and `ISOWeekday` (1=Monday...7=Sunday). `ShiftNumber` is derived from
each record's `StartTime`: shift 1 (06h-14h), shift 2 (14h-22h), shift 3
(22h-06h).

**Stage 4 -- analysis (`05`, `06`).** OEE, Pareto charts, Cp/Cpk,
MTBF/MTTR, and then a "scorecard" notebook where I went through the
production/quality KPI lists I'd been given and checked which ones I'd
actually already built vs. which ones were still missing (Scrap %,
schedule adherence, an actual X-bar/R chart, etc.).

The indicator formulas, spelled out:

| Indicator | Formula | What it measures |
|---|---|---|
| Availability | Production time / Planned time | How much of the planned time the machine was actually producing (excludes unplanned stops) |
| Performance | (Units produced / Production time) / Nominal capacity | How close to nominal speed the run was |
| Quality (OEE) | Good units / Produced units | 100% yield of the run -- different from the AQL sample decision |
| **OEE** | **Availability x Performance x Quality** | Overall equipment effectiveness -- 85% is generally considered "world class" |
| Cp | Spec window width / process variation | Would the spec fit the process's variation at all, ignoring centering |
| Cpk | Distance to nearest spec limit / (3 x sigma) | The more useful question -- given where the process is actually centered, how much room is left. Always `Cpk <= Cp` |
| Pp / Ppk | Same as Cp/Cpk, using total long-term variation | The gap between Cpk and Ppk shows how much spread is drift between subgroups vs. noise within them |
| MTBF | Total production time / number of unplanned failures | Average time between breakdowns -- higher is more reliable |
| MTTR | Average duration of unplanned stops | Average time to repair -- lower is more responsive |

A machine running 100% of planned time at half its nominal speed
(Performance = 0.5) hurts OEE exactly as much as a machine that's down
for half the planned time -- that symmetry is intentional; it's what
forces you to decompose "the plant is slow" into which of the three
causes it actually is. The project also derives real cycle time
(seconds/unit), setup time (stoppages of type "changeover" linked to
each order), and throughput lead time (time from the start of one order
to the start of the next on the same machine -- captures queue/wait time
that "production time" alone wouldn't see).

Cp/Cpk/Pp/Ppk are grouped by Characteristic x Machine x Mold x Product
-- mixing two different products on the same control chart would hide
real shifts behind noise. MTBF/MTTR are calculated strictly from events
classified as unplanned failures (mechanical/electrical breakdowns,
utility shortages), deliberately excluding planned mold/tool changeovers
and scheduled preventive maintenance -- mixing the two would make a
machine look less reliable than it actually is, since a planned stop is
a management decision, not an equipment failure.

**AQL sampling (ISO 2859-1).** Instead of inspecting 100% of a lot, the
sample size comes from lot size and the desired inspection strictness
("General Level II" here), and a defined number of defects in that
sample (Ac = accept, Re = reject) still passes for a given AQL
(Acceptable Quality Level -- the maximum tolerable percentage
defective). A Critical characteristic typically uses a tight AQL like
0.10% -- even a single defect in the sample can reject the whole lot,
appropriate for something like a bottle that leaks, where the defect is
a functional/safety failure, not just cosmetic.

**DPU / DPMO (Six Sigma).** Defects Per Unit and Defects Per Million
Opportunities let you compare defect rates across processes with very
different sample sizes and opportunity counts, on a common scale. A
"3-sigma" process (~66,807 DPMO) is materially worse than a "5-sigma"
process (~233 DPMO) -- the gap between them is the real size of the
improvement opportunity.

**A design decision on what gets stored vs. computed on the fly.** Not
every indicator became a saved column -- that split was deliberate.
Per-row values that are constant within a group (control limits,
Cp/Cpk, DPU/DPMO) are stored, since they only need their own group and
are cheap to propagate with `groupby().transform()` -- a BI tool can
then draw a control chart with zero extra calculation. True aggregates
over many rows/tables (FPY, Pareto, MTBF/MTTR, inspector ranking) are
*not* stored as columns -- a First Pass Yield is a summary of a table,
not a property of a row, so it belongs in a view/query/notebook,
computed at report time. This follows standard data-warehousing
practice: keep the fact table at its natural grain, and push
aggregation to the semantic/reporting layer.

The `06_kpi_scorecard.ipynb` notebook is a dedicated audit: it walks
through two checklists -- 13 Production and 14 Quality indicators --
confirms which ones Stages 3-4 already covered, and adds whatever was
missing (Planned vs. Actual production, efficiency per operator, Scrap
%, rework -- estimated, see below -- setup time per process, schedule
adherence, inspection approval rate, defect PPM, approved/rejected lot
counts, inspections performed, an actual X-bar/R control chart, top
defect trends). It ends with a coverage table confirming all 27
requested indicators are in the project.

**Stage 5 -- Quality Assurance (`07`, `08`).** Customer complaints,
supplier raw-material inspection, NC/CAPA. This stage extends the
project past the shop floor: what happens after a product ships, and
what happens before raw material even reaches the plant. It follows the
exact same discipline as the earlier stages -- generic cleaning, then
domain-specific feature engineering, then analysis -- and feeds the
same `datasets/processed → MySQL → Power BI` pipeline. See the section
below.

**Stage 6 -- Machine Learning (`09`-`12`).** Four models. See below.

**Stage 7 -- putting it together (`13`).** This one runs last because
it's the only notebook that uses results from every other stage --
production, quality, QA, and the ML models -- to actually answer the
project's questions. Three things came out of it:

- Production loss stays dominated by maintenance events (unplanned
  stops, tool changeovers), not by process speed or quality.
- Production signals carry a real, if modest, early-warning signal for
  customer outcomes, not just internal QMS outcomes -- and the honest
  strength of that signal, quantified against real complaint data, is a
  more credible result than a stronger claim that was never actually
  tested.
- The plant has the process and machine capability it needs to hit its
  quality targets; the constraint is operational (unplanned downtime),
  not structural.

Which answers the central question: yes, and specifically because the
domains aren't independent -- monitoring production, quality,
maintenance, and customer/supplier outcomes together, paired with a
small set of well-evaluated predictive models, surfaces both the
root causes an isolated dashboard would miss and a forward-looking view
that a purely historical approach can't offer.

---

## The four ML models

I wanted each model to answer a specific question a plant would actually
ask, not just "have a model" for the sake of it. All four use a
time-based train/test split (train on older data, test on the most
recent) instead of a random split -- a random split would let the model
"see the future" during training, which isn't how it would work if you
actually deployed it.

| Notebook | Question | Type | Models compared | How it did |
|---|---|---|---|---|
| `09` | How much will we produce next week, by process? | Regression | Linear Regression, Random Forest, XGBoost | Very accurate -- almost too accurate, honestly. I explain in the notebook why: one year of data with no real demand swings makes this an easy problem. On real data with actual seasonality this would be harder. |
| `10` | How much scrap should I expect, and what's driving it? | Regression | XGBoost (feature importance is the real deliverable) | R² ≈ 0.83 vs. ≈ 0.00 for just guessing the average -- a real, useful result. Turns "scrap is high" into "scrap is high specifically on these machine/mold combinations," which a continuous-improvement team can actually act on. |
| `11` | Will this lot pass or get rejected? | Classification | Logistic Regression, Decision Tree (the explainable one -- you can show the tree to a quality manager), Random Forest, XGBoost | ROC-AUC ≈ 0.63. Not great, and I say so in the notebook -- in this dataset, the AQL disposition is driven substantially by random sampling variation, not by a strong deterministic link to production conditions. |
| `12` | Which machine is likely to break down tomorrow? | Classification | Same ensemble as `11` | ROC-AUC ≈ 0.72, F1 ≈ 0.78 on the "failure" class -- the strongest of the four. Recent failure frequency turned out to be the strongest signal, which matches how MTBF works conceptually, just applied at daily resolution. |

A couple of things I had to get right or the results would've been
meaningless:
- **Not leaking the answer into the features.** E.g. the scrap model
  can't use `Quality`, because `Quality` is basically calculated from the
  same rejected/produced numbers I'm trying to predict -- using it would
  make the model "cheat." More generally: any column that's
  definitionally later than the target, or arithmetically derived from
  it, gets excluded from the feature set for all four models.
- **Picking the right time grain for predictive maintenance.** I first
  tried weekly data, and it didn't work -- almost every machine has some
  failure every single week, so "will there be a failure next week" is
  basically always "yes," which isn't a useful prediction. Switching to
  daily data gave a real ~61/39 split and a model that actually means
  something. All features come from day *t* or earlier; the target is
  day *t+1*, so nothing leaks from the future.
- **Metrics that fit rare targets.** Every classification target here
  is rare (lot rejections, complaints, daily breakdowns -- all well
  under 50%), so I report precision, recall, F1, and ROC-AUC instead of
  plain accuracy, since a model that always predicts "no problem" would
  look great on accuracy and be useless in practice.
- Every trained model is saved to `models/*.pkl` (via `joblib`) along
  with its feature list and test metrics, and each notebook exports its
  predictions to `datasets/processed/ml_predictions_*.csv` for the
  MySQL/Power BI layer.

---

## Quality Assurance module

This part covers what happens after a product ships (customer
complaints) and before raw material even reaches the plant (incoming
inspection). Same pipeline as everything else: raw CSV -> cleaned ->
MySQL -> views.

| Table | What it holds |
|---|---|
| `dim_customer` | Cosmetics companies in the Curitiba, Brazil area (made-up names) |
| `dim_supplier` | Resin/masterbatch suppliers (also made-up names) |
| `dim_raw_material_control_plan` | Incoming inspection plan, with real ASTM/ISO test standards |
| `fact_sales_processed` | One row per shipment |
| `fact_customer_complaints_processed` | One row per complaint, traceable back to the exact lot |
| `fact_raw_material_inspection_processed` / `..._lot_disposition_processed` | Incoming material test results and accept/reject decisions |
| `fact_supplier_complaints_processed` | Complaints filed to suppliers |
| `fact_nonconformance_processed` / `fact_capa_processed` | Internal/external NCs and the corrective actions opened from them |

I used made-up company names for customers and suppliers on purpose --
the complaint and rejection rates in this data are fabricated, and I
didn't want to attach fabricated numbers to real, identifiable companies,
even in a project that's obviously a simulation.

Indicators built here: number of complaints (by customer, product,
family, defect type), monthly trend, and Complaints Per Million Units
shipped (CPMU) -- both plant-wide and per customer. Defect types include
things like broken cap, leaking bottle, wrong color, out-of-spec weight,
late delivery, excessive torque, "cap back-off" (the cap re-opens on its
own after closing, from a torque-retention failure), plus missing
label, smudged print, contamination, wrong product, and short shipment.
On the supplier side: complaints filed to suppliers (by problem type),
rejected raw material (rate, by material type), supplier approval rate,
and average supplier response time to a filed complaint.

NC/CAPA indicators: Internal vs. External NCs, NCs by process, NCs by
area, open/closed/overdue CAPAs, and average CAPA closure time (by
severity). External NCs originate from customer or supplier complaints;
Internal NCs come from internal audits and in-process deviations.
CAPAs open automatically for Critical/Major NCs (plus a sample of Minor
ones), with a target closing date that depends on severity -- a CAPA
past its target date with no closure date gets flagged as Overdue.

---

## A couple of decisions worth explaining

**Why I split planned and unplanned downtime into separate charts.** My
first version had one combined Pareto of stoppage reasons, and it looked
wrong -- the top of the list was always mold changes and the shift-3
meal break, because those happen on *every single order*. That's not
useful for a maintenance team; it buries the actual failures under
routine, scheduled stops. Splitting them (there's a `PlannedStoppage`
flag) fixed it -- now the unplanned Pareto actually shows what breaks.

**Why `LotId` is 16 characters and rebuilt the way it is.** This was the
part of the brief that took the most back-and-forth to get right. It
lets you trace any quality inspection back to the exact work order,
shift, and raw-material lot that produced it:

`YY WW D T P MM OOOOO SS` → e.g. `26 09 2 2 1 01 06005 01`

| Segment | Digits | Meaning |
|---|---|---|
| YY | 2 | Last 2 digits of the year |
| WW | 2 | ISO week number |
| D | 1 | ISO weekday (1=Mon...7=Sun) |
| T | 1 | Shift: 1 (06-14h), 2 (14-22h), 3 (22-06h) |
| P | 1 | Process: Blow Molding=1, Injection Molding=2, Screen Printing=4, Hot Foil Stamping=5 |
| MM | 2 | Machine number (`ISBM-001` → `01`) |
| OOOOO | 5 | Work order number (`WO-6005` → `06005`) |
| SS | 2 | Raw-material lot sequence (see below) |

The last two digits start at `01` for each new work order and only
increase when the *physical* material lot in use actually changes -- a
shift change alone doesn't advance the counter. Getting that right
meant processing the material consumption records in order and
comparing each one to the last, which is why this part is Python and
not a SQL window function. It's also why `fact_material_consumption_raw`
has two lot columns, `LotIdStart` and `LotIdEnd`: the first 14
characters can differ between the start and end of one consumption
record if it crosses a shift change, while the material sequence digits
stay the same, since it's still physically the same lot.

One subtlety the code handles: after normalizing placeholder nulls,
some `MaterialLot` values end up blank -- almost always because the
operator forgot to log it, not because a new lot actually started. So
before computing the sequence, missing values get forward-filled with
the last known lot within the same work order (`ffill_material_lot`);
otherwise every blank would read as "a new lot," inflating the counter
for no real reason.

**How downtime gets linked to a work order.** Machine stoppages don't
carry their own `WorkOrder` column -- a stoppage isn't "produced" by an
order the way a lot is. To assign a stoppage to whichever order was
running at that moment, the code reconstructs the exact start/end
instant of each order (not just the time of day, since an order can run
past midnight) and checks which interval each stoppage falls into, per
machine.

**Why some columns get dropped or hidden before the final tables.** A
few columns only existed to help calculate something else (an internal
timestamp, an auto-increment ID used just to sort rows correctly) and
have no analytical value once that calculation is done. I dropped them
rather than carry dead weight into every dashboard query.

## Some difficulties along the way

- Getting the ISO week/weekday logic right took a couple of tries --
  pandas' `.isocalendar()` behaves slightly differently than I expected
  around year boundaries, and I had a bug where a handful of records got
  assigned to the wrong week for a while.
- The predictive maintenance model was disappointing at first (see
  above) until I figured out the weekly-vs-daily grain problem. That was
  a useful mistake to make, honestly -- it's the kind of thing you only
  really understand by trying the wrong version first.
- Deciding what to do about the "rework" KPI was tricky -- there's no
  column anywhere in the data that tracks rework directly, so I had to
  build an estimate from the control plan's reaction-plan field instead
  of just skipping the indicator. I flagged it clearly as an estimate
  rather than pretending it's a measured number.

## Limitations

- All the data is simulated. I tried to make the generation rules
  realistic (real ISO/ASTM standards, real AQL sampling math, plausible
  defect rates), but it's still synthetic -- some of the ML results
  (especially the production forecast) look better than they would on
  real data with real demand variation.
- One year of history isn't enough to learn real seasonality.
- Customer and supplier names are invented, not real companies.
- The "rework" indicator is an estimate, not a measured value (see above).

## What I got out of building this

Mainly: how much of a real analytics project is actually data engineering
and decision-making about grain, leakage, and what a number is even
supposed to mean, rather than the modeling itself. The ML models were
probably the fastest part to build; figuring out the `LotId` logic and
the daily-vs-weekly framing for predictive maintenance took a lot longer
than fitting the actual models did. I also got a lot more comfortable
moving between SQL, Python, and Power BI as one connected pipeline
instead of three separate tools.

---

## Concepts, briefly

**Lean Manufacturing** -- a management philosophy focused on eliminating
waste ("muda") and maximizing customer value with the fewest resources.
OEE and the "six big losses" analysis (breakdowns, setup/changeover,
minor stops, reduced speed, startup rejects, production rejects) used
here are core Lean tools.

**Six Sigma** -- a data-driven methodology for reducing variability and
defects, measuring performance in "sigma level": the higher it is, the
fewer defects per million opportunities (DPMO). A 6-sigma process runs
around 3.4 DPMO; most real-world plants operate between 3 and 4 sigma.

**DPU / DPMO** -- Defects Per Unit and Defects Per Million Opportunities
put defect rates from very different sample sizes on a common scale, so
processes can actually be compared apples-to-apples.

**SPC / control charts** -- instead of checking every unit, you sample
small groups over time and plot the group average and range. If the
process is stable, both stay inside limits calculated from the process's
own past behavior (not the spec limits).

**Cp / Cpk** -- Cp asks if the spec window would fit the process's
variation at all; Cpk asks the more useful question, given where the
process is actually centered, how much room is left before it goes out
of spec.

**ISO 9001** -- the international quality management systems standard.
It requires a process approach, traceability, and continuous
improvement -- the `LotId` code in this project is exactly the kind of
traceability mechanism ISO 9001 requires: being able to trace any
delivered product back to its exact production origin.

**ISO 2859-1 / AQL** -- instead of inspecting every unit, you sample a
size based on lot size and how strict you want to be (Ac = accept, Re =
reject), and a defined number of defects in that sample still passes,
for a given AQL (Acceptable Quality Level).

**OEE** -- Availability x Performance x Quality. It's multiplicative on
purpose: running at half speed for the whole shift hurts OEE exactly as
much as stopping for half the shift.

**MTBF / MTTR** -- reliability metrics, calculated only from genuine
unplanned failures (not scheduled stops), otherwise a machine looks less
reliable than it actually is.

**Time-based validation (ML)** -- train on older data, test on newer
data, never a random split, because factory data has a real time order
and a random split would let the model peek at the future.

---

## Tools used

SQL (MySQL) · Python (pandas, scikit-learn, XGBoost, matplotlib) ·
Power BI · ISO 9001 / ISO 2859-1 · SPC/CEP · OEE and Lean basics ·
customer/supplier quality tracking and CAPA.
