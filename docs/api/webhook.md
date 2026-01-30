# Webhook

## GET /webhook
Verificacion del webhook de WhatsApp.

Query params:
- hub.mode
- hub.verify_token
- hub.challenge

Respuestas:
- 200 con el challenge si el token es valido.
- 403 si la verificacion falla.

## POST /webhook
Recepcion de eventos de WhatsApp y reenvio al WebSocket.

Body:
- JSON completo enviado por WhatsApp.

Respuestas:
- 200 si se reenvia correctamente.
- 500 si hay error interno.
