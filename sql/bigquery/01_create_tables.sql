-- Ejecutar después de crear el dataset retail_dw.
CREATE SCHEMA IF NOT EXISTS `TU_PROYECTO.retail_dw`;

CREATE OR REPLACE TABLE `TU_PROYECTO.retail_dw.fact_sales` (
  order_id STRING NOT NULL,
  customer_id STRING NOT NULL,
  product_id STRING NOT NULL,
  order_date DATE NOT NULL,
  quantity INT64 NOT NULL,
  unit_price NUMERIC NOT NULL,
  total_amount NUMERIC NOT NULL,
  channel STRING
)
PARTITION BY order_date
CLUSTER BY customer_id, product_id;

CREATE OR REPLACE TABLE `TU_PROYECTO.retail_dw.dim_customer` (
  customer_id STRING, customer_name STRING, city STRING, created_at DATE
);

CREATE OR REPLACE TABLE `TU_PROYECTO.retail_dw.dim_product` (
  product_id STRING, product_name STRING, category STRING, unit_price NUMERIC
);
