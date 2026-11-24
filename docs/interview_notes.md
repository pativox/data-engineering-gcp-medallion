# Notas para entrevista — GCP Medallion

## Problema
Consolidar ventas retail de distintas fuentes y publicar datos confiables para analítica.

## Decisiones
- Bronze conserva el dato de origen.
- Silver aplica tipado, integridad referencial, deduplicación y reglas de negocio.
- Gold publica hechos y agregados analíticos.
- Los rechazos se registran con motivo para mantener trazabilidad.

## Evolución a GCP
- Cloud Storage para landing y persistencia de capas.
- BigQuery para tablas analíticas particionadas y clusterizadas.
- Cloud Run Jobs o Composer para orquestación según complejidad y frecuencia.
- IAM, presupuestos y alertas para controlar acceso y costos.

## Transparencia
El pipeline publicado se ejecuta localmente. BigQuery y Cloud Storage son arquitectura objetivo; no se declara despliegue cloud productivo.
