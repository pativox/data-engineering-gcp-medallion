-- Ventas mensuales
SELECT FORMAT_DATE('%Y-%m', order_date) AS year_month,
       COUNT(DISTINCT order_id) AS orders,
       SUM(total_amount) AS revenue,
       SUM(quantity) AS units
FROM `TU_PROYECTO.retail_dw.fact_sales`
GROUP BY 1 ORDER BY 1;

-- Ranking de categorías
SELECT p.category, SUM(f.total_amount) AS revenue,
       SUM(f.quantity) AS units
FROM `TU_PROYECTO.retail_dw.fact_sales` f
JOIN `TU_PROYECTO.retail_dw.dim_product` p USING(product_id)
GROUP BY p.category ORDER BY revenue DESC;

-- Detección de anomalías: totales inconsistentes
SELECT *
FROM `TU_PROYECTO.retail_dw.fact_sales`
WHERE ABS(total_amount - quantity * unit_price) > 0.01;
