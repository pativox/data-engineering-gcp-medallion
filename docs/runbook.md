# Runbook — GCP Medallion

## Requisitos
- Python 3.10 o superior.
- Git (opcional, para clonar).
- No requiere paquetes externos ni credenciales cloud.

## Ejecución en Windows
Desde PowerShell, en la raíz del repositorio:
```powershell
py -3 src/pipeline.py
py -3 -m unittest discover -s tests -p "test_*.py" -v
```

## Ejecución en Linux/macOS
```bash
python3 src/pipeline.py
python3 -m unittest discover -s tests -p "test_*.py" -v
```

## Salidas
El proceso regenera los archivos bajo `data/processed/` y `reports/` en cada ejecución. Son artefactos reproducibles y están excluidos de Git para mantener el repositorio limpio.

## Diagnóstico
- **Falta un CSV:** revisar `data/raw/` y el nombre exacto del archivo.
- **Faltan columnas:** comparar encabezados con el contrato documentado en `src/pipeline.py`.
- **Hay órdenes rechazadas:** revisar `data/processed/rejected_orders.csv` y el conteo por motivo en `reports/quality_report.json`.
- **Fallan pruebas:** ejecutar el comando unittest desde la raíz para obtener el caso y traceback.
- **CI:** revisar la pestaña Actions del repositorio. El workflow ejecuta pipeline y pruebas en push y pull request.

## Reproceso
No se modifican archivos raw. Cada ejecución vuelve a generar Silver y Gold a partir de las fuentes. Antes de reemplazar datos de entrada, conservar una copia/versionado externo si se requiere auditoría histórica.
