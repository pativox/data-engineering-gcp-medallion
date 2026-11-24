# Pruebas manuales sugeridas
- Ejecutar pipeline dos veces: el número de órdenes válidas debe ser estable.
- Confirmar que el duplicado se rechaza.
- Confirmar que la orden con customer_id inexistente se rechaza.
- Alterar un total y verificar `amount_mismatch`.
- Verificar que el total de filas válidas + rechazadas = filas fuente.
