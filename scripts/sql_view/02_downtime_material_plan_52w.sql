-- ============================================================================
-- 02_downtime_material_plan_52w.sql
-- ============================================================================
-- Same rolling-52-week logic as 01_production_by_process_52w.sql. Downtime,
-- material consumption and the production plan stay as ONE view each (not
-- split by process), since maintenance and material-planning teams work
-- across all four processes at once.
--
-- Downtime additionally gets THREE views instead of one:
--   * vw_fact_downtime_52w             -- everything (kept for completeness /
--                                          totals-level reporting)
--   * vw_fact_downtime_planned_52w     -- PlannedStoppage = 'Yes' only
--   * vw_fact_downtime_unplanned_52w   -- PlannedStoppage = 'No' only
--
-- This mirrors the analysis split made in notebook 05: a Pareto over
-- *all* stoppage reasons together is dominated by scheduled events (mold
-- changes, cleaning, the shift-3 meal break) simply because they are
-- frequent by design, which buries the unplanned failures a reliability
-- team actually needs to chase. Power BI should build the "Top downtime
-- causes" visual against vw_fact_downtime_unplanned_52w, and a separate
-- "Planned stoppage load" visual against vw_fact_downtime_planned_52w --
-- never against the combined view for a Pareto-style ranking.
-- ============================================================================

CREATE OR REPLACE VIEW vw_fact_downtime_52w AS
SELECT d.*
FROM fact_downtime_processed d
WHERE d.Date >= (
    SELECT DATE_SUB(MAX(Date), INTERVAL 52 WEEK) FROM fact_downtime_processed
);

CREATE OR REPLACE VIEW vw_fact_downtime_planned_52w AS
SELECT d.*
FROM fact_downtime_processed d
WHERE d.PlannedStoppage = 'Yes'
  AND d.Date >= (
      SELECT DATE_SUB(MAX(Date), INTERVAL 52 WEEK) FROM fact_downtime_processed
  );

CREATE OR REPLACE VIEW vw_fact_downtime_unplanned_52w AS
SELECT d.*
FROM fact_downtime_processed d
WHERE d.PlannedStoppage = 'No'
  AND d.Date >= (
      SELECT DATE_SUB(MAX(Date), INTERVAL 52 WEEK) FROM fact_downtime_processed
  );

CREATE OR REPLACE VIEW vw_fact_material_consumption_52w AS
SELECT m.*
FROM fact_material_consumption_processed m
WHERE m.Date >= (
    SELECT DATE_SUB(MAX(Date), INTERVAL 52 WEEK) FROM fact_material_consumption_processed
);

CREATE OR REPLACE VIEW vw_fact_production_plan_52w AS
SELECT pl.*
FROM fact_production_plan_processed pl
WHERE pl.Date >= (
    SELECT DATE_SUB(MAX(Date), INTERVAL 52 WEEK) FROM fact_production_plan_processed
);
