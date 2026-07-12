"""
03_load_data.py
----------------
Etapa 3 - "Guardar numa base de dados no MySQL": loads every cleaned/processed
CSV produced by the notebooks into MySQL, using pandas.to_sql (SQLAlchemy).

Usage
-----
1. Create the schema first (run 01_create_fact_tables.sql and
   02_create_dim_tables.sql against your MySQL server -- e.g. with the
   `mysql` CLI, MySQL Workbench, or DBeaver).
2. Set your connection details as environment variables (never hard-code
   credentials into a script that goes on GitHub):

     export MYSQL_HOST=localhost
     export MYSQL_PORT=3306
     export MYSQL_USER=analytics
     export MYSQL_PASSWORD=...
     export MYSQL_DB=manufacturing_performance_analytics

3. python scripts/sql_table/03_load_data.py

Why `to_sql` with `if_exists="replace"` and a pre-created schema via SQL,
instead of just letting pandas create the tables?
Pandas' automatic type inference for `to_sql` is often too generic
(e.g. TEXT for every string column, no explicit VARCHAR sizing), which
hurts index performance and storage. Creating the schema explicitly first
(01/02 .sql scripts) and then loading with `if_exists="append"` keeps the
column types we actually want; we truncate first so the load stays
idempotent (safe to re-run).
"""
import os
import glob
import pandas as pd
from sqlalchemy import create_engine, text

DATASETS_PROCESSED = os.path.join(os.path.dirname(__file__), '..', '..', 'datasets', 'processed')
DATASETS_DIM = os.path.join(os.path.dirname(__file__), '..', '..', 'datasets', 'dim')

# Maps the physical CSV file to the MySQL table name (must match the DDL
# in 01_create_fact_tables.sql / 02_create_dim_tables.sql).
TABLE_MAP = {
    # fact tables (production side)
    'fact_production_processed.csv': 'fact_production_processed',
    'fact_downtime_processed.csv': 'fact_downtime_processed',
    'fact_material_consumption_processed.csv': 'fact_material_consumption_processed',
    'fact_production_plan_processed.csv': 'fact_production_plan_processed',
    # fact tables (quality side)
    'fact_cap_inspection_variable_cq_processed.csv': 'fact_cap_inspection_variable_cq_processed',
    'fact_cap_attribute_inspection_cq_processed.csv': 'fact_cap_attribute_inspection_cq_processed',
    'fact_cap_disposition_lot_cq_processed.csv': 'fact_cap_disposition_lot_cq_processed',
    'fact_bottle_inspection_variables_cq_processed.csv': 'fact_bottle_inspection_variables_cq_processed',
    'fact_bottle_attribute_inspection_cq_processed.csv': 'fact_bottle_attribute_inspection_cq_processed',
    'fact_bottle_disposition_lot_cq_processed.csv': 'fact_bottle_disposition_lot_cq_processed',
    'fact_ink_attribute_inspection_cq_processed.csv': 'fact_ink_attribute_inspection_cq_processed',
    'fact_ink_disposition_lot_cq_processed.csv': 'fact_ink_disposition_lot_cq_processed',
    # fact tables (quality assurance side: customers, suppliers, NC/CAPA)
    'fact_sales_processed.csv': 'fact_sales_processed',
    'fact_customer_complaints_processed.csv': 'fact_customer_complaints_processed',
    'fact_raw_material_inspection_processed.csv': 'fact_raw_material_inspection_processed',
    'fact_raw_material_lot_disposition_processed.csv': 'fact_raw_material_lot_disposition_processed',
    'fact_supplier_complaints_processed.csv': 'fact_supplier_complaints_processed',
    'fact_nonconformance_processed.csv': 'fact_nonconformance_processed',
    'fact_capa_processed.csv': 'fact_capa_processed',
    # fact tables (machine learning predictions -- Stage 6)
    'ml_predictions_production_forecast.csv': 'ml_predictions_production_forecast',
    'ml_predictions_production_forecast_history.csv': 'ml_predictions_production_forecast_history',
    'ml_predictions_scrap_rate.csv': 'ml_predictions_scrap_rate',
    'ml_predictions_lot_quality.csv': 'ml_predictions_lot_quality',
    'ml_predictions_predictive_maintenance.csv': 'ml_predictions_predictive_maintenance',
    'ml_predictions_predictive_maintenance_history.csv': 'ml_predictions_predictive_maintenance_history',
    # dimension tables produced by the pipeline
    'dim_bottle.csv': 'dim_bottle',
    'dim_cap.csv': 'dim_cap',
    'dim_ink.csv': 'dim_ink',
    'dim_machine.csv': 'dim_machine',
    'dim_mold.csv': 'dim_mold',
    'dim_operator.csv': 'dim_operator',
    'dim_customer.csv': 'dim_customer',
    'dim_supplier.csv': 'dim_supplier',
    'dim_raw_material_control_plan.csv': 'dim_raw_material_control_plan',
}

# dimension tables that are copied through as-is from datasets/dim
DIM_PASSTHROUGH = {
    'dim_masterbatch.csv': 'dim_masterbatch',
    'dim_machine_setup.csv': 'dim_machine_setup',
    'dim_cap_control_plan_cq.csv': 'dim_cap_control_plan_cq',
    'dim_bottle_control_plan_cq.csv': 'dim_bottle_control_plan_cq',
    'dim_ink_control_plan_cq.csv': 'dim_ink_control_plan_cq',
}


def get_engine():
    user = os.environ.get('MYSQL_USER', 'root')
    password = os.environ.get('MYSQL_PASSWORD', '')
    host = os.environ.get('MYSQL_HOST', 'localhost')
    port = os.environ.get('MYSQL_PORT', '3306')
    db = os.environ.get('MYSQL_DB', 'manufacturing_performance_analytics')
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4"
    return create_engine(url)


def load_csv_to_table(engine, csv_path: str, table_name: str, chunksize: int = 5000):
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE `{table_name}`"))
    df.to_sql(table_name, engine, if_exists='append', index=False, chunksize=chunksize, method='multi')
    print(f"  loaded {len(df):>7,} rows -> {table_name}")


def main():
    engine = get_engine()
    print(f"Connecting to {engine.url.render_as_string(hide_password=True)}")

    print("\nLoading processed fact + derived dim tables from datasets/processed/ ...")
    for csv_name, table_name in TABLE_MAP.items():
        path = os.path.join(DATASETS_PROCESSED, csv_name)
        if os.path.exists(path):
            load_csv_to_table(engine, path, table_name)
        else:
            print(f"  [skip] {csv_name} not found -- run the Etapa 2/3 notebooks first")

    print("\nLoading governed master-data tables from datasets/dim/ ...")
    for csv_name, table_name in DIM_PASSTHROUGH.items():
        path = os.path.join(DATASETS_DIM, csv_name)
        if os.path.exists(path):
            load_csv_to_table(engine, path, table_name)
        else:
            print(f"  [skip] {csv_name} not found")

    print("\nDone. Run scripts/sql_view/*.sql next to create the Power BI-facing rolling-52-week views.")


if __name__ == '__main__':
    main()
