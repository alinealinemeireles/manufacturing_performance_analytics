-- ============================================================================
-- 04_quality_assurance_52w.sql
-- ============================================================================
-- Rolling-52-week views for the Quality Assurance domain: customer sales/
-- complaints, supplier raw-material inspection/complaints, and non-
-- conformance/CAPA. Same rolling-window pattern as 01-03: anchored to
-- MAX(Date) / MAX(OpenDate) *within the table*, not the calendar date, so
-- the window advances automatically as new records are inserted.
-- ============================================================================

CREATE OR REPLACE VIEW vw_fact_sales_52w AS
SELECT s.*
FROM fact_sales_processed s
WHERE s.Date >= (SELECT DATE_SUB(MAX(Date), INTERVAL 52 WEEK) FROM fact_sales_processed);

CREATE OR REPLACE VIEW vw_fact_customer_complaints_52w AS
SELECT c.*
FROM fact_customer_complaints_processed c
WHERE c.Date >= (SELECT DATE_SUB(MAX(Date), INTERVAL 52 WEEK) FROM fact_customer_complaints_processed);

CREATE OR REPLACE VIEW vw_fact_raw_material_inspection_52w AS
SELECT r.*
FROM fact_raw_material_inspection_processed r
WHERE r.Date >= (SELECT DATE_SUB(MAX(Date), INTERVAL 52 WEEK) FROM fact_raw_material_inspection_processed);

CREATE OR REPLACE VIEW vw_fact_raw_material_lot_disposition_52w AS
SELECT r.*
FROM fact_raw_material_lot_disposition_processed r
WHERE r.Date >= (SELECT DATE_SUB(MAX(Date), INTERVAL 52 WEEK) FROM fact_raw_material_lot_disposition_processed);

CREATE OR REPLACE VIEW vw_fact_supplier_complaints_52w AS
SELECT s.*
FROM fact_supplier_complaints_processed s
WHERE s.Date >= (SELECT DATE_SUB(MAX(Date), INTERVAL 52 WEEK) FROM fact_supplier_complaints_processed);

CREATE OR REPLACE VIEW vw_fact_nonconformance_52w AS
SELECT n.*
FROM fact_nonconformance_processed n
WHERE n.Date >= (SELECT DATE_SUB(MAX(Date), INTERVAL 52 WEEK) FROM fact_nonconformance_processed);

-- CAPA is anchored to OpenDate (when the corrective/preventive action
-- itself was opened), not the underlying NC's date -- a dashboard tracking
-- CAPA aging cares about the CAPA's own timeline.
CREATE OR REPLACE VIEW vw_fact_capa_52w AS
SELECT c.*
FROM fact_capa_processed c
WHERE c.OpenDate >= (SELECT DATE_SUB(MAX(OpenDate), INTERVAL 52 WEEK) FROM fact_capa_processed);
