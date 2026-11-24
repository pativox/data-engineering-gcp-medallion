# Guía de defensa técnica — Proyecto GCP

## Pitch de 60 segundos
Diseñé un pipeline batch para consolidar órdenes, clientes y productos de múltiples canales. Separé la ingesta en Bronze, la limpieza y validación en Silver y la publicación analítica en Gold. Implementé deduplicación, validación referencial, consistencia de montos y reporte de rechazos. La arquitectura está preparada para migrar el almacenamiento a Cloud Storage y el warehouse a BigQuery.

## Preguntas que debes poder responder
1. ¿Por qué Medallion? Separa dato original, dato confiable y producto analítico.
2. ¿Cómo evitas duplicados? Clave de negocio `order_id`; en producción, `MERGE`/upsert y watermark.
3. ¿Cómo reprocesas? Mantienes raw inmutable, versión de transformación y particiones de salida.
4. ¿Cómo escalas? BigQuery particionado y clusterizado, procesamiento distribuido con Dataflow/Dataproc cuando el volumen lo justifique.
5. ¿Cómo monitoreas? Filas leídas/aceptadas/rechazadas, duración, frescura, errores y alertas.
6. ¿Qué falta para producción? Secret Manager/IAM, orquestación, CI/CD, pruebas automatizadas, catálogo, SLA y observabilidad.

## Métricas de demostración
Ejecuta el pipeline y registra filas fuente, válidas, rechazadas y razones. No inventes porcentajes de mejora ni resultados de negocio.
