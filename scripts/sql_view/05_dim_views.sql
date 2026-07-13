-- 05_dim_views.sql
--
-- Views for the dimension (reference) tables. Unlike the fact-table
-- views, these don't filter to a rolling 52-week window -- dimension
-- tables (machines, molds, customers, control plans...) are reference
-- lists, not time series, so there's nothing to "roll" here. The view
-- exists purely for consistency: every table Power BI reads from is a
-- view, not a raw table, so the naming convention (vw_*) is the same
-- across the whole model.

CREATE OR REPLACE VIEW vw_dim_machine AS
SELECT * FROM dim_machine;

CREATE OR REPLACE VIEW vw_dim_mold AS
SELECT * FROM dim_mold;

CREATE OR REPLACE VIEW vw_dim_operator AS
SELECT * FROM dim_operator;

CREATE OR REPLACE VIEW vw_dim_cap AS
SELECT * FROM dim_cap;

CREATE OR REPLACE VIEW vw_dim_bottle AS
SELECT * FROM dim_bottle;

CREATE OR REPLACE VIEW vw_dim_ink AS
SELECT * FROM dim_ink;

CREATE OR REPLACE VIEW vw_dim_customer AS
SELECT * FROM dim_customer;

CREATE OR REPLACE VIEW vw_dim_supplier AS
SELECT * FROM dim_supplier;

CREATE OR REPLACE VIEW vw_dim_raw_material_control_plan AS
SELECT * FROM dim_raw_material_control_plan;

CREATE OR REPLACE VIEW vw_dim_masterbatch AS
SELECT * FROM dim_masterbatch;

CREATE OR REPLACE VIEW vw_dim_machine_setup AS
SELECT * FROM dim_machine_setup;

CREATE OR REPLACE VIEW vw_dim_cap_control_plan_cq AS
SELECT * FROM dim_cap_control_plan_cq;

CREATE OR REPLACE VIEW vw_dim_bottle_control_plan_cq AS
SELECT * FROM dim_bottle_control_plan_cq;

CREATE OR REPLACE VIEW vw_dim_ink_control_plan_cq AS
SELECT * FROM dim_ink_control_plan_cq;
