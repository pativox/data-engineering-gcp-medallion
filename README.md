# Proyecto 1 — Retail Lakehouse con arquitectura Medallion (GCP)

## Resumen ejecutivo
Pipeline batch de ventas que integra clientes, productos y órdenes. Implementa una separación conceptual Bronze, Silver y Gold, controles de calidad, métricas operacionales y un modelo dimensional para analítica.

**Stack:** Python 3.10+, SQL y BigQuery (scripts SQL de referencia).  
**Ejecución local:** Python estándar, sin dependencias externas, cuenta GCP ni servicios pagos.

## Caso de negocio
Una empresa retail consolida ventas de distintos canales. Necesita detectar duplicados, referencias huérfanas y errores de negocio antes de publicar indicadores confiables para las áreas comercial y operaciones.

## Arquitectura lógica
- **Bronze:** archivos CSV originales en `data/raw/`, conservados como fuente inmutable del ejercicio.
- **Silver:** órdenes validadas, tipadas y enriquecidas en `data/processed/silver_orders.csv`.
- **Gold:** tabla de hechos, dimensiones de clientes/productos y agregado mensual.
- **Consumo:** SQL analítico en BigQuery y herramientas BI (integración cloud documentada como evolución, no desplegada).

## Ejecución local
Desde la raíz del repositorio:
```bash
python src/pipeline.py
python -m unittest discover -s tests -p "test_*.py" -v
```

El pipeline genera:
- `data/processed/silver_orders.csv`
- `data/processed/gold_fact_sales.csv`
- `data/processed/gold_dim_customer.csv`
- `data/processed/gold_dim_product.csv`
- `data/processed/gold_monthly_sales.csv`
- `data/processed/rejected_orders.csv`
- `reports/quality_report.json`

## Reglas de calidad
- Validación de estructura y columnas requeridas de cada fuente.
- Claves de clientes y productos no vacías ni duplicadas en sus dimensiones.
- `order_id` único; duplicados rechazados.
- Integridad referencial con clientes y productos.
- Cantidad y precio positivos; rechazo de valores numéricos no finitos.
- Total consistente con cantidad × precio, usando decimal para evitar errores binarios de punto flotante.
- Fecha válida y canal informado.
- Trazabilidad de filas aceptadas y rechazadas con motivo y número de fila.

## Modelo analítico
- `fact_sales`: una fila por orden válida.
- `dim_customer`: cliente, ciudad y fecha de alta.
- `dim_product`: producto, categoría y precio de referencia.
- `gold_monthly_sales`: ventas, órdenes y unidades por mes.

## SQL / BigQuery
Los scripts de `sql/bigquery/` contienen DDL de referencia con particionamiento por fecha y clustering por claves de cliente/producto, además de consultas analíticas. Reemplaza `TU_PROYECTO` por tu proyecto/dataset antes de ejecutar. No se ha desplegado infraestructura GCP en este repositorio.

## Calidad continua
GitHub Actions ejecuta el pipeline y la suite de pruebas unitarias en cada push y pull request. El estado real de cada ejecución se consulta en la pestaña **Actions** del repositorio.

## Evolución cloud (diseño, no despliegue)
1. Ingestar los archivos en Cloud Storage.
2. Mantener Bronze en una zona raw con control de lote.
3. Ejecutar transformación con Cloud Run Jobs o Dataflow según volumen.
4. Publicar Silver/Gold en BigQuery con particionamiento y clustering.
5. Orquestar con Workflows o Composer cuando existan dependencias y calendario.
6. Incorporar IAM de mínimo privilegio, logging, alertas y presupuesto.

## Decisiones técnicas para entrevista
- Los archivos raw permiten auditoría y reproceso.
- Silver concentra calidad, tipado, deduplicación e integridad referencial.
- Gold separa hechos y dimensiones para facilitar consumo analítico.
- Se usa `Decimal` para importes monetarios.
- El procesamiento es determinista: las salidas se regeneran desde raw.
- Las pruebas cubren reglas de negocio y casos límite sin requerir servicios cloud.

## Documentación complementaria
- [Diagrama de arquitectura](docs/architecture.md)
- [Runbook de ejecución y diagnóstico](docs/runbook.md)

Los artefactos generados en `data/processed/` y `reports/` se excluyen de Git mediante `.gitignore`.

## Estructura
- `data/raw`: datos fuente sintéticos.
- `src`: pipeline local.
- `tests`: pruebas unitarias automatizadas.
- `sql/bigquery`: DDL y consultas analíticas.
- `reports`: reporte de calidad generado.
