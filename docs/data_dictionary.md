# Data Dictionary & Traceability Reference

Quick-reference companion to the main README. See `scripts/notebook/etl_lib.py`
for the authoritative, documented implementation of everything below.

## Calculated columns added in Stage 3

| Column | Tables | Meaning |
|---|---|---|
| `ISOWeek` | all fact tables | ISO week number of `Date` |
| `ISOWeekday` | all fact tables | ISO weekday, 1=Monday...7=Sunday |
| `ShiftNumber` | all fact tables | Numeric shift: 1 (06-14h), 2 (14-22h), 3 (22-06h) |
| `LotId` | production, downtime, all QC tables | 16-char batch traceability code — see README |
| `LotIdStart` / `LotIdEnd` | material consumption | Lot code at the start/end of that consumption record |
| `LeadTimeProdHours` | production, downtime | Duration in decimal hours |
| `Availability`, `Performance`, `Quality`, `OEE` | production | OEE pillars, per work order |
| `ActualCycleTimeSec`, `SetupTimeHours`, `ThroughputLeadTimeHours` | production | Supporting OEE metrics |
| `XBarUCL/LCL`, `RangeRUCL/LCL`, `Cp`, `Cpk`, `Pp`, `Ppk`, `Cpm`, `SigmaLevel` | QC variable-inspection tables | SPC / process-capability metrics |
| `DefectRateP`, `DPU`, `DPMO` | QC attribute-inspection tables | AQL / Six Sigma defect-rate metrics |
| `DowntimeDurationMin`, `UnplannedFailure`, `IsChangeoverSetup`, `IsPreventiveMaintenance` | downtime | Maintenance classification flags (see "Planned vs. unplanned downtime" in the README) |

## Process code map (used inside `LotId`)

| Process | Code |
|---|---|
| Blow Molding | 1 |
| Injection Molding | 2 |
| Screen Printing | 4 |
| Hot Foil Stamping | 5 |

(Digit `3` is intentionally unused/reserved, per the original specification.)

## Table grain (one row = ...)

| Table | Grain |
|---|---|
| `fact_production_plan_processed` | one planned work order |
| `fact_production_processed` | one actual work order |
| `fact_downtime_processed` | one machine stoppage event |
| `fact_material_consumption_processed` | one raw-material lot consumption record |
| `fact_*_inspection_variable_cq_processed` | one SPC subgroup sample, per characteristic |
| `fact_*_attribute_inspection_cq_processed` | one AQL attribute inspection, per lot per characteristic |
| `fact_*_disposition_lot_cq_processed` | one final accept/reject decision, per lot |

## KPIs intentionally *not* stored as columns

FPY, Pareto tables, MTBF/MTTR, inspector-bias ranking, and similar are true
*aggregates* over many rows (sometimes across tables) — they are computed
in the Stage 4/5 notebooks (or would be, in a BI tool, at report time),
not stored on the fact tables. See the "Why some KPIs are columns here"
note in `03_data_cleaning_quality.ipynb`.

## Machine Learning tables and models (notebooks 09-12)

| Table | Grain | Produced by |
|---|---|---|
| `ml_predictions_production_forecast` | one row per process, next-week forecast | `09_ml_production_forecast.ipynb` |
| `ml_predictions_production_forecast_history` | one row per process x test-set week (actual vs. predicted) | `09_ml_production_forecast.ipynb` |
| `ml_predictions_scrap_rate` | one row per test-set work order (actual vs. predicted scrap %) | `10_ml_scrap_prediction.ipynb` |
| `ml_predictions_lot_quality` | one row per test-set lot, with predicted rejection risk | `11_ml_lot_quality_classification.ipynb` |
| `ml_predictions_predictive_maintenance` | one row per machine, today's failure-risk ranking | `12_ml_predictive_maintenance.ipynb` |
| `ml_predictions_predictive_maintenance_history` | one row per machine x test-set day (actual vs. predicted risk) | `12_ml_predictive_maintenance.ipynb` |

Trained models are saved to `models/*.pkl` via `ml_lib.save_model` (a
dict of `{model, metadata}`, where `metadata` includes the feature list,
model name, and test-set metrics) and reloaded with `ml_lib.load_model`.
See `scripts/machine_learning/ml_lib.py` for the shared time-based-split,
regression/classification evaluation, and persistence helpers every ML
notebook uses.

## Columns dropped before `datasets/processed/` (see README "Hiding columns")

| Column | Table | Why it's dropped |
|---|---|---|
| `_start_dt`, `_end_dt`, `_next_start_dt` | production (in-memory only) | Internal timestamp helpers, superseded by `LotId` + OEE time columns |
| `RecordSeq` | material consumption | MES auto-increment id, only needed to compute `MaterialLotSeq`; no analytical value afterward |

## KPI checklist cross-reference

`scripts/notebook/06_kpi_scorecard.ipynb` is the authoritative cross-reference
for the full production (13 indicators) and quality (14 indicators) KPI
checklists, including which were already computed in Stage 3-5 vs. added
in that notebook, and its coverage summary table at the end. One
indicator -- **Rework** -- is an estimate rather than a directly-measured
figure: this dataset has no rework-transaction field anywhere upstream,
so the notebook approximates it from each defect characteristic's
`ReactionPlan` (control-plan dimension tables), counting only
`Reprocess (...)` reaction plans as reworkable. Treat it as directional.

## Quality Assurance domain tables (notebooks 07-08)

| Table | Grain |
|---|---|
| `fact_sales_processed` | one finished-goods shipment (one row per work order shipped to a customer) |
| `fact_customer_complaints_processed` | one customer complaint |
| `fact_raw_material_inspection_processed` | one incoming raw-material lot x characteristic tested |
| `fact_raw_material_lot_disposition_processed` | one incoming raw-material lot (final decision) |
| `fact_supplier_complaints_processed` | one complaint filed to a supplier |
| `fact_nonconformance_processed` | one non-conformance record (Internal or External) |
| `fact_capa_processed` | one corrective/preventive action |

Calculated columns: `ResolutionDays` (customer complaints), `ResponseDays`
+ `ResolutionDays` (supplier complaints), `ClosureDays` + `IsOverdue`
(CAPA), `IsAccepted` + `IsRejected` (raw material lot disposition) -- all
via `etl_lib.add_days_between`. Complaints-per-million-shipped and
supplier approval rate are aggregates, computed in notebook 08, not
stored as fact columns (same "true aggregates live in the analysis
layer" principle as the rest of the project).
