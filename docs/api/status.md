# Status

## GET /api/status
Estado agregado de servicios internos.

Respuesta:
- status: healthy | degraded
- services: { webhook, whatsapp_service, queue_service, websocket_service }

## GET /api/health
Health check simple.

Respuesta:
- {"status": "ok"}
