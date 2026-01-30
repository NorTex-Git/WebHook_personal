# Queue

## GET /api/queue/status
Estado general y longitudes.

## GET /api/queue/lengths
Longitudes de las colas.

## POST /api/queue/retry_failed
Reintenta mensajes fallidos.

Body opcional:
- limit (int, default: 10)

## DELETE /api/queue/clear
Limpia todas las colas.

## POST /api/queue/test
Inserta un mensaje de prueba en la cola.

## POST /api/queue/restart
Reinicia el procesador FIFO.
