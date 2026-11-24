# Estrategia de pruebas

La validación continua ejecuta el pipeline con Python 3.11 mediante GitHub Actions.

Casos a automatizar con pytest:
- Orden válida pasa a Silver y Gold.
- Orden duplicada se rechaza.
- Cliente o producto inexistente se rechaza.
- Cantidad o precio no positivo se rechaza.
- Total inconsistente se rechaza.
- Reejecución regenera las salidas desde Bronze sin duplicar filas.
