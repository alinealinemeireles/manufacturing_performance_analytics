-- ============================================================================
-- 03_quality_control_52w.sql
-- ============================================================================
-- Rolling-52-week views for every quality-control fact table, keyed off
-- `ProductionDate` (the date the *inspected lot* was produced, which is
-- the meaningful timeline for a quality dashboard -- not the inspection
-- timestamp, which can lag production by a few hours).
-- ============================================================================

CREATE OR REPLACE VIEW vw_fact_cap_inspection_variable_cq_52w AS
SELECT t.*
FROM fact_cap_inspection_variable_cq_processed t
WHERE t.ProductionDate >= (
    SELECT DATE_SUB(MAX(ProductionDate), INTERVAL 52 WEEK) FROM fact_cap_inspection_variable_cq_processed
);

CREATE OR REPLACE VIEW vw_fact_cap_attribute_inspection_cq_52w AS
SELECT t.*
FROM fact_cap_attribute_inspection_cq_processed t
WHERE t.ProductionDate >= (
    SELECT DATE_SUB(MAX(ProductionDate), INTERVAL 52 WEEK) FROM fact_cap_attribute_inspection_cq_processed
);

CREATE OR REPLACE VIEW vw_fact_cap_disposition_lot_cq_52w AS
SELECT t.*
FROM fact_cap_disposition_lot_cq_processed t
WHERE t.ProductionDate >= (
    SELECT DATE_SUB(MAX(ProductionDate), INTERVAL 52 WEEK) FROM fact_cap_disposition_lot_cq_processed
);

CREATE OR REPLACE VIEW vw_fact_bottle_inspection_variables_cq_52w AS
SELECT t.*
FROM fact_bottle_inspection_variables_cq_processed t
WHERE t.ProductionDate >= (
    SELECT DATE_SUB(MAX(ProductionDate), INTERVAL 52 WEEK) FROM fact_bottle_inspection_variables_cq_processed
);

CREATE OR REPLACE VIEW vw_fact_bottle_attribute_inspection_cq_52w AS
SELECT t.*
FROM fact_bottle_attribute_inspection_cq_processed t
WHERE t.ProductionDate >= (
    SELECT DATE_SUB(MAX(ProductionDate), INTERVAL 52 WEEK) FROM fact_bottle_attribute_inspection_cq_processed
);

CREATE OR REPLACE VIEW vw_fact_bottle_disposition_lot_cq_52w AS
SELECT t.*
FROM fact_bottle_disposition_lot_cq_processed t
WHERE t.ProductionDate >= (
    SELECT DATE_SUB(MAX(ProductionDate), INTERVAL 52 WEEK) FROM fact_bottle_disposition_lot_cq_processed
);

CREATE OR REPLACE VIEW vw_fact_ink_attribute_inspection_cq_52w AS
SELECT t.*
FROM fact_ink_attribute_inspection_cq_processed t
WHERE t.ProductionDate >= (
    SELECT DATE_SUB(MAX(ProductionDate), INTERVAL 52 WEEK) FROM fact_ink_attribute_inspection_cq_processed
);

CREATE OR REPLACE VIEW vw_fact_ink_disposition_lot_cq_52w AS
SELECT t.*
FROM fact_ink_disposition_lot_cq_processed t
WHERE t.ProductionDate >= (
    SELECT DATE_SUB(MAX(ProductionDate), INTERVAL 52 WEEK) FROM fact_ink_disposition_lot_cq_processed
);
