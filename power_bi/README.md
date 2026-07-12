# Power BI

Drop the `.pbix` dashboard file(s) built on top of this project's MySQL
views here.

📋 **Full build plan:** `docs/ESQUEMA_POWERBI.md` -- page-by-page layout
for all 4 department dashboards (Production, Quality Control,
Maintenance, Quality Assurance), which visuals go where, which view feeds
each one, and what each department should actually discuss with it in
their meeting.

Connect Power BI Desktop to MySQL (`Get Data -> MySQL database`) and build
every visual against the `vw_*` views in `scripts/sql_view/`, never
against the base `*_processed` tables -- the views are what enforces the
rolling 52-week window and the planned/unplanned downtime split each
dashboard expects. See `scripts/notebook/04_mysql_load_and_views.ipynb`
for the full setup walkthrough.

Suggested dashboards:
- **Production / OEE** -- `vw_fact_production_*` (one per process)
- **Maintenance / Reliability** -- `vw_fact_downtime_unplanned_52w` (Pareto,
  MTBF/MTTR) and `vw_fact_downtime_planned_52w` (capacity-planning view)
  kept as separate visuals, not combined
- **Quality** -- the `vw_fact_*_cq_52w` views (FPY, Cp/Cpk, defect Pareto)
- **Quality Assurance** -- `vw_fact_customer_complaints_52w` +
  `vw_fact_sales_52w` (complaints, CPMU), `vw_fact_raw_material_*_52w` +
  `vw_fact_supplier_complaints_52w` (supplier scorecard), and
  `vw_fact_nonconformance_52w` + `vw_fact_capa_52w` (NC/CAPA aging)
- **Machine Learning / Predictions** -- the `ml_predictions_*` tables
  (production forecast, scrap-rate drivers, lot-rejection risk, and the
  daily predictive-maintenance risk ranking) loaded by
  `scripts/sql_table/03_load_data.py`. Pair each prediction table with
  its `_history` counterpart (actual vs. predicted on the held-out test
  period) so the dashboard can show model performance, not just the
  forward-looking number.
