-- ============================================================================
-- 01_production_by_process_52w.sql
-- ============================================================================
-- Splits `fact_production_processed` into 4 process-specific views, each
-- restricted to the last 52 ISO weeks *relative to the most recent record
-- currently in the table* (not relative to today's calendar date). Every
-- time a new production record is inserted, MAX(Date) moves forward and
-- the window automatically drops whatever is now more than 52 weeks older
-- than the newest record -- no scheduled job or manual refresh needed,
-- because a VIEW re-evaluates its query on every SELECT.
--
-- Power BI (or any other BI tool) should point at these views, not at the
-- base table, so each process team only ever sees its own rolling year of
-- data.
-- ============================================================================

CREATE OR REPLACE VIEW vw_fact_production_injection_molding AS
SELECT p.*
FROM fact_production_processed p
WHERE p.Process = 'Injection Molding'
  AND p.Date >= (
      SELECT DATE_SUB(MAX(Date), INTERVAL 52 WEEK) FROM fact_production_processed
  );

CREATE OR REPLACE VIEW vw_fact_production_blow_molding AS
SELECT p.*
FROM fact_production_processed p
WHERE p.Process = 'Blow Molding'
  AND p.Date >= (
      SELECT DATE_SUB(MAX(Date), INTERVAL 52 WEEK) FROM fact_production_processed
  );

CREATE OR REPLACE VIEW vw_fact_production_screen_printing AS
SELECT p.*
FROM fact_production_processed p
WHERE p.Process = 'Screen Printing'
  AND p.Date >= (
      SELECT DATE_SUB(MAX(Date), INTERVAL 52 WEEK) FROM fact_production_processed
  );

CREATE OR REPLACE VIEW vw_fact_production_hot_foil_stamping AS
SELECT p.*
FROM fact_production_processed p
WHERE p.Process = 'Hot Foil Stamping'
  AND p.Date >= (
      SELECT DATE_SUB(MAX(Date), INTERVAL 52 WEEK) FROM fact_production_processed
  );
