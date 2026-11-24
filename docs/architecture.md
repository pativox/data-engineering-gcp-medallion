# Arquitectura y flujo de datos — GCP Medallion

```mermaid
flowchart LR
    A[CSV clientes] --> B[Bronze: data/raw]
    C[CSV productos] --> B
    D[CSV órdenes] --> B
    B --> E[Python batch pipeline]
    E -->|válidos y enriquecidos| F[Silver orders]
    E -->|rechazados + motivo| G[Rejected orders]
    F --> H[Gold fact sales]
    F --> I[Gold monthly sales]
    B --> J[Gold dim customer]
    B --> K[Gold dim product]
    H --> L[BigQuery SQL / BI]
    J --> L
    K --> L
```

## Capas
- **Bronze:** archivos CSV de origen sintéticos, conservados sin modificar.
- **Silver:** órdenes con tipos normalizados, controles de negocio e información descriptiva de clientes y productos.
- **Gold:** tabla de hechos, dimensiones conformadas y agregado mensual.
- **Rejected:** registros que no cumplen reglas, conservados con fila de origen y motivo.

## Límites de implementación
La ejecución actual es local y utiliza la biblioteca estándar de Python. BigQuery contiene DDL y consultas de referencia. No se ha creado un proyecto GCP, bucket, job, dataset ni servicio cloud.
