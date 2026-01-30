# Messages

## Mensajes individuales

### POST /api/send-message
Body:
- phone (string, requerido)
- message (string, requerido)
- use_queue (bool, opcional)

### POST /api/send-template
Body:
- phone (string, requerido)
- template_name (string, requerido)
- language (string, opcional, default: es)
- parameters (array, opcional)
- use_queue (bool, opcional)

### POST /api/send-template-advanced
Body:
- phone (string, requerido)
- template_name (string, requerido)
- language (string, opcional, default: es)
- components (array, opcional)
- parameters (array, opcional, compatibilidad)
- use_queue (bool, opcional)

### POST /api/send-location-request
Body:
- phone (string, requerido)
- body_text (string, requerido)

### GET /api/media/<media_id>
Obtiene la URL de un media_id.

### GET /api/task-status/<task_id>
Estado de una tarea de cola.

## Interactivos individuales

### POST /api/send-interactive
Body:
- phone (string, requerido)
- body_text (string, requerido)
- header_type (string, opcional)
- header_content (string, opcional)
- button_text (string, opcional)
- button_url (string, opcional)
- footer_text (string, opcional)
- use_queue (bool, opcional)

### POST /api/send-list
Body:
- phone (string, requerido)
- header_text (string, requerido)
- body_text (string, requerido)
- footer_text (string, requerido)
- button_text (string, requerido)
- sections (array, requerido)

### POST /api/send-button
Body:
- phone (string, requerido)
- body_text (string, requerido)
- buttons (array, requerido, 1-3 botones)
- header_type (string, opcional)
- header_content (string, opcional)
- footer_text (string, opcional)
- use_queue (bool, opcional)

## Envios masivos

### POST /api/send-bulk
Body:
- recipients (array, requerido; items: {phone, message})
- use_queue (bool, opcional, default: true)

### POST /api/send-bulk-list
Body:
- recipients (array, requerido; items: {phone, body_text})
- header_text (string, requerido)
- footer_text (string, requerido)
- button_text (string, requerido)
- sections (array, requerido)
- use_queue (bool, opcional, default: true)

### POST /api/send-bulk-interactive
Body:
- recipients (array, requerido; items: {phone, body_text})
- use_queue (bool, opcional, default: true)

### POST /api/send-bulk-button
Body:
- recipients (array, requerido; items: {phone, body_text})
- buttons (array, requerido, 1-3 botones)
- header_type (string, opcional)
- header_content (string, opcional)
- footer_text (string, opcional)
- use_queue (bool, opcional, default: true)

### POST /api/send-bulk-template
Body:
- recipients (array, requerido; items: {phone, template_name})
- use_queue (bool, opcional, pero actualmente forzado a false en codigo)

## Broadcast

### POST /api/send-broadcast-interactive
Body:
- phones (array, requerido)
- body_text (string, requerido)
- header_type (string, opcional)
- header_content (string, opcional)
- button_text (string, opcional)
- button_url (string, opcional)
- footer_text (string, opcional)
- use_queue (bool, opcional, default: true)

### POST /api/send-personalized-broadcast
Body:
- recipients (array, requerido; items: {phone, body_text})
- header_type (string, opcional)
- header_content (string, opcional)
- button_text (string, opcional)
- button_url (string, opcional)
- footer_text (string, opcional)
- use_queue (bool, opcional, default: true)

### POST /api/send-broadcast-template
Body:
- phones (array, requerido)
- template_name (string, requerido)
- language (string, opcional, default: es)
- components (array, opcional)
- parameters (array, opcional, compatibilidad)
- use_queue (bool, opcional, default: true)
