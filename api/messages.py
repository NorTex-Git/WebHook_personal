from flask import Blueprint, request, jsonify, Response
import logging
from services.whatsapp_service import WhatsAppService
from services.queue_service import QueueService

logger = logging.getLogger(__name__)

messages_bp = Blueprint('messages', __name__)

# Inicializar servicios
whatsapp_service = None
queue_service = None

def init_services():
    global whatsapp_service, queue_service
    try:
        # Forzar recarga de .env
        from dotenv import load_dotenv
        load_dotenv()
        whatsapp_service = WhatsAppService()
        queue_service = QueueService()
    except Exception as e:
        logger.error(f"Error inicializando servicios de mensajes: {str(e)}")

@messages_bp.route('/send-message', methods=['POST'])
def send_message():
    """Endpoint para enviar mensajes individuales"""
    global whatsapp_service, queue_service
    
    if not whatsapp_service:
        init_services()
    
    try:
        if not whatsapp_service:
            return jsonify({"error": "Servicio no disponible"}), 500
        
        data = request.json
        phone = data.get('phone')
        message = data.get('message')
        use_queue = data.get('use_queue', False)
        context_message_id = data.get('context_message_id')

        if not phone or not message:
            return jsonify({"error": "Faltan parámetros: phone y message son requeridos"}), 400

        if use_queue and queue_service:
            # Enviar usando cola (la cola no propaga el contexto de respuesta).
            task = queue_service.send_message_async(phone, message)
            return jsonify({
                "success": True,
                "message": "Mensaje enviado a cola",
                "task_id": task.id
            }), 200
        else:
            # Enviar directamente
            result = whatsapp_service.send_text_message(phone, message, context_message_id=context_message_id)
            
            if result['success']:
                return jsonify({
                    "success": True,
                    "message": "Mensaje enviado exitosamente",
                    "data": result['data']
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": result['error']
                }), 400
            
    except Exception as e:
        logger.error(f"Error enviando mensaje: {str(e)}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/send-template', methods=['POST'])
def send_template():
    """Endpoint para enviar mensajes de plantilla"""
    global whatsapp_service, queue_service
    
    if not whatsapp_service:
        init_services()
    
    try:
        if not whatsapp_service:
            return jsonify({"error": "Servicio no disponible"}), 500
        
        data = request.json
        phone = data.get('phone')
        template_name = data.get('template_name')
        language = data.get('language', 'es')
        parameters = data.get('parameters', [])
        use_queue = data.get('use_queue', False)
        
        if not phone or not template_name:
            return jsonify({"error": "Faltan parámetros: phone y template_name son requeridos"}), 400
        
        if use_queue and queue_service:
            # Enviar usando cola
            task = queue_service.send_template_async(phone, template_name, language, parameters)
            return jsonify({
                "success": True,
                "message": "Plantilla enviada a cola",
                "task_id": task.id
            }), 200
        else:
            # Enviar directamente
            result = whatsapp_service.send_template_message(phone, template_name, language, parameters)
            
            if result['success']:
                return jsonify({
                    "success": True,
                    "message": "Plantilla enviada exitosamente",
                    "data": result['data']
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": result['error']
                }), 400
            
    except Exception as e:
        logger.error(f"Error enviando plantilla: {str(e)}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/send-bulk', methods=['POST'])
def send_bulk():
    """Endpoint para envío masivo de mensajes"""
    global whatsapp_service, queue_service
    
    if not whatsapp_service:
        init_services()
    
    try:
        if not whatsapp_service:
            return jsonify({"error": "Servicio no disponible"}), 500
        
        data = request.json
        recipients = data.get('recipients', [])
        use_queue = data.get('use_queue', True)  # Por defecto usar cola para masivos
        
        if not recipients:
            return jsonify({"error": "Falta parámetro: recipients es requerido"}), 400
        
        # Validar estructura de recipients
        for recipient in recipients:
            if not recipient.get('phone') or not recipient.get('message'):
                return jsonify({"error": "Cada recipient debe tener 'phone' y 'message'"}), 400
        
        if use_queue and queue_service:
            # Enviar usando cola
            task = queue_service.send_bulk_messages_async(recipients)
            return jsonify({
                "success": True,
                "message": "Envío masivo enviado a cola",
                "task_id": task.id
            }), 200
        else:
            # Enviar directamente
            result = whatsapp_service.send_bulk_messages(recipients)
            
            return jsonify({
                "success": True,
                "message": "Envío masivo completado",
                "result": result
            }), 200
        
    except Exception as e:
        logger.error(f"Error en envío masivo: {str(e)}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/send-bulk-list', methods=['POST'])
def send_bulk_list():
    """Endpoint para envío masivo de mensajes de lista personalizados"""
    global whatsapp_service, queue_service
    
    if not whatsapp_service:
        init_services()
    
    try:
        if not whatsapp_service:
            return jsonify({"error": "Servicio no disponible"}), 500
        
        data = request.json
        
        if not data:
            return jsonify({"error": "Se requiere un JSON con los datos del mensaje"}), 400
        
        # Validar que se proporcionen los recipients
        recipients = data.get('recipients', [])
        if not isinstance(recipients, list) or len(recipients) == 0:
            return jsonify({"error": "Se requiere el campo 'recipients' con un array de destinatarios"}), 400
        
        # Validar estructura de recipients
        for recipient in recipients:
            if not isinstance(recipient, dict):
                return jsonify({"error": "Cada recipient debe ser un objeto"}), 400
            
            phone = recipient.get('phone')
            body_text = recipient.get('body_text')
            
            if not phone:
                return jsonify({"error": "Cada recipient debe tener un 'phone'"}), 400
            
            if not body_text:
                return jsonify({"error": "Cada recipient debe tener un 'body_text'"}), 400
        
        # Extraer parámetros comunes del mensaje
        header_text = data.get('header_text')
        footer_text = data.get('footer_text')
        button_text = data.get('button_text')
        sections = data.get('sections', [])
        use_queue = data.get('use_queue', True)  # Por defecto usar cola para masivos
        
        # Validar parámetros comunes requeridos
        if not header_text:
            return jsonify({"error": "Se requiere el campo 'header_text'"}), 400
        if not footer_text:
            return jsonify({"error": "Se requiere el campo 'footer_text'"}), 400
        if not button_text:
            return jsonify({"error": "Se requiere el campo 'button_text'"}), 400
        if not sections or not isinstance(sections, list):
            return jsonify({"error": "Se requiere el campo 'sections' como array"}), 400
        
        # Validar estructura de sections
        for section in sections:
            if not isinstance(section, dict):
                return jsonify({"error": "Cada section debe ser un objeto"}), 400
            
            if not section.get('title'):
                return jsonify({"error": "Cada section debe tener un 'title'"}), 400
            
            rows = section.get('rows', [])
            if not rows or not isinstance(rows, list):
                return jsonify({"error": "Cada section debe tener un array 'rows'"}), 400
            
            for row in rows:
                if not isinstance(row, dict):
                    return jsonify({"error": "Cada row debe ser un objeto"}), 400
                
                if not row.get('id'):
                    return jsonify({"error": "Cada row debe tener un 'id'"}), 400
                
                if not row.get('title'):
                    return jsonify({"error": "Cada row debe tener un 'title'"}), 400
        
        if use_queue and queue_service:
            # Enviar usando cola
            task = queue_service.send_bulk_list_messages_async(
                recipients, header_text, footer_text, button_text, sections
            )
            return jsonify({
                "success": True,
                "message": "Envío masivo de listas enviado a cola",
                "task_id": task.id
            }), 200
        else:
            # Enviar directamente
            result = whatsapp_service.send_bulk_list_messages(
                recipients, header_text, footer_text, button_text, sections
            )
            
            return jsonify({
                "success": True,
                "message": "Envío masivo de listas completado",
                "result": result
            }), 200
        
    except Exception as e:
        logger.error(f"Error en envío masivo de listas: {str(e)}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/task-status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Endpoint para obtener el estado de una tarea"""
    global queue_service
    
    if not queue_service:
        init_services()
    
    try:
        if not queue_service:
            return jsonify({"error": "Servicio de cola no disponible"}), 500
        
        status = queue_service.get_task_status(task_id)
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de tarea: {str(e)}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/send-location-request', methods=['POST'])
def send_location_request():
    """Endpoint para enviar mensaje de solicitud de ubicación"""
    global whatsapp_service
    
    if not whatsapp_service:
        init_services()
    
    try:
        if not whatsapp_service:
            return jsonify({"error": "Servicio no disponible"}), 500
        
        data = request.json
        phone = data.get('phone')
        body_text = data.get('body_text')
        
        if not phone or not body_text:
            return jsonify({"error": "Faltan parámetros: phone y body_text son requeridos"}), 400
        
        result = whatsapp_service.send_location_request_message(phone, body_text)
        
        if result['success']:
            return jsonify({
                "success": True,
                "message": "Solicitud de ubicación enviada exitosamente",
                "data": result['data']
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 400
        
    except Exception as e:
        logger.error(f"Error enviando solicitud de ubicación: {str(e)}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/media/<media_id>', methods=['GET'])
def get_media(media_id):
    """Endpoint para obtener URL de contenido multimedia"""
    global whatsapp_service
    
    if not whatsapp_service:
        init_services()
    
    try:
        if not whatsapp_service:
            return jsonify({"error": "Servicio no disponible"}), 500
        
        media_url = whatsapp_service.get_media_url(media_id)
        
        if media_url:
            return jsonify({
                "success": True,
                "media_url": media_url
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "No se pudo obtener la URL del archivo"
            }), 404
            
    except Exception as e:
        logger.error(f"Error obteniendo media: {str(e)}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/send-media', methods=['POST'])
def send_media():
    """Reenvía una media entrante (image/audio/video/sticker) por su media_id."""
    global whatsapp_service

    if not whatsapp_service:
        init_services()

    try:
        if not whatsapp_service:
            return jsonify({"error": "Servicio no disponible"}), 500

        data = request.json or {}
        phone = data.get('phone')
        media_type = data.get('type')
        media_id = data.get('media_id') or data.get('id')
        caption = data.get('caption', '')
        context_message_id = data.get('context_message_id')

        if not phone or not media_type or not media_id:
            return jsonify({"error": "Faltan parámetros: phone, type y media_id son requeridos"}), 400

        result = whatsapp_service.send_media_by_id(phone, media_type, media_id, caption, context_message_id=context_message_id)
        if result.get('success'):
            return jsonify({"success": True, "data": result.get('data')}), 200
        return jsonify({"success": False, "error": result.get('error')}), 400

    except Exception as e:
        logger.error(f"Error enviando media: {str(e)}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/media/<media_id>/download', methods=['GET'])
def download_media(media_id):
    """Descarga los bytes del archivo multimedia (server-side, con el token)."""
    global whatsapp_service

    if not whatsapp_service:
        init_services()

    try:
        if not whatsapp_service:
            return jsonify({"error": "Servicio no disponible"}), 500

        content, mime_type = whatsapp_service.download_media(media_id)
        if content is None:
            return jsonify({"success": False, "error": "No se pudo descargar el archivo"}), 404

        return Response(content, mimetype=mime_type or 'application/octet-stream')

    except Exception as e:
        logger.error(f"Error descargando media: {str(e)}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/send-interactive', methods=['POST'])
def send_interactive():
    """Endpoint para enviar mensajes interactivos individuales"""
    global whatsapp_service, queue_service
    
    if not whatsapp_service:
        init_services()
    
    try:
        if not whatsapp_service:
            return jsonify({"error": "Servicio no disponible"}), 500
        
        data = request.json
        phone = data.get('phone')
        header_type = data.get('header_type')
        header_content = data.get('header_content')
        body_text = data.get('body_text')
        button_text = data.get('button_text')
        button_url = data.get('button_url')
        footer_text = data.get('footer_text')
        use_queue = data.get('use_queue', False)
        
        if not phone or not body_text:
            return jsonify({"error": "Faltan parámetros: phone y body_text son requeridos"}), 400
        
        if use_queue and queue_service:
            # Enviar usando cola
            task = queue_service.send_interactive_message_async(
                phone, header_type, header_content, body_text, button_text, button_url, footer_text
            )
            return jsonify({
                "success": True,
                "message": "Mensaje interactivo enviado a cola",
                "task_id": task.id
            }), 200
        else:
            # Enviar directamente
            result = whatsapp_service.send_interactive_message(
                phone, header_type, header_content, body_text, button_text, button_url, footer_text
            )
            
            if result['success']:
                return jsonify({
                    "success": True,
                    "message": "Mensaje interactivo enviado exitosamente",
                    "data": result['data']
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": result['error']
                }), 400
            
    except Exception as e:
        logger.error(f"Error enviando mensaje interactivo: {str(e)}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/send-bulk-interactive', methods=['POST'])
def send_bulk_interactive():
    """Endpoint para envío masivo de mensajes interactivos"""
    global whatsapp_service, queue_service
    
    if not whatsapp_service:
        init_services()
    
    try:
        if not whatsapp_service:
            return jsonify({"error": "Servicio no disponible"}), 500
        
        data = request.json
        recipients = data.get('recipients', [])
        use_queue = data.get('use_queue', True)  # Por defecto usar cola para masivos
        
        if not recipients:
            return jsonify({"error": "Falta parámetro: recipients es requerido"}), 400
        
        # Validar estructura de recipients
        for recipient in recipients:
            if not recipient.get('phone') or not recipient.get('body_text'):
                return jsonify({"error": "Cada recipient debe tener 'phone' y 'body_text'"}), 400
        
        if use_queue and queue_service:
            # Enviar usando cola
            task = queue_service.send_bulk_interactive_messages_async(recipients)
            return jsonify({
                "success": True,
                "message": "Envío masivo interactivo enviado a cola",
                "task_id": task.id
            }), 200
        else:
            # Enviar directamente
            result = whatsapp_service.send_bulk_interactive_messages(recipients)
            
            return jsonify({
                "success": True,
                "message": "Envío masivo interactivo completado",
                "result": result
            }), 200
        
    except Exception as e:
        logger.error(f"Error en envío masivo interactivo: {str(e)}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/send-list', methods=['POST'])
def send_list():
    """Endpoint para enviar mensajes de lista"""
    global whatsapp_service, queue_service
    
    if not whatsapp_service:
        init_services()
    
    try:
        if not whatsapp_service:
            return jsonify({"error": "Servicio no disponible"}), 500
        
        data = request.json
        
        if not data:
            return jsonify({"error": "Se requiere un JSON con los datos del mensaje"}), 400
        
        # Validar parámetros requeridos
        phone = data.get('phone')
        header_text = data.get('header_text')
        body_text = data.get('body_text')
        footer_text = data.get('footer_text')
        button_text = data.get('button_text')
        sections = data.get('sections', [])
        
        if not phone:
            return jsonify({"error": "Se requiere el campo 'phone'"}), 400
        
        if not header_text:
            return jsonify({"error": "Se requiere el campo 'header_text'"}), 400
        
        if not body_text:
            return jsonify({"error": "Se requiere el campo 'body_text'"}), 400
        
        if not footer_text:
            return jsonify({"error": "Se requiere el campo 'footer_text'"}), 400
        
        if not button_text:
            return jsonify({"error": "Se requiere el campo 'button_text'"}), 400
        
        if not sections or not isinstance(sections, list):
            return jsonify({"error": "Se requiere el campo 'sections' como array"}), 400
        
        # Validar estructura de sections
        for section in sections:
            if not isinstance(section, dict):
                return jsonify({"error": "Cada section debe ser un objeto"}), 400
            
            if not section.get('title'):
                return jsonify({"error": "Cada section debe tener un 'title'"}), 400
            
            rows = section.get('rows', [])
            if not rows or not isinstance(rows, list):
                return jsonify({"error": "Cada section debe tener un array 'rows'"}), 400
            
            for row in rows:
                if not isinstance(row, dict):
                    return jsonify({"error": "Cada row debe ser un objeto"}), 400
                
                if not row.get('id'):
                    return jsonify({"error": "Cada row debe tener un 'id'"}), 400
                
                if not row.get('title'):
                    return jsonify({"error": "Cada row debe tener un 'title'"}), 400
        
        # Enviar mensaje directamente (sin cola por ahora)
        result = whatsapp_service.send_list_message(
            phone, header_text, body_text, footer_text, button_text, sections
        )
        
        if result['success']:
            return jsonify({
                "success": True,
                "message": "Mensaje de lista enviado exitosamente",
                "data": result['data']
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 400
        
    except Exception as e:
        logger.error(f"Error enviando mensaje de lista: {str(e)}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/send-button', methods=['POST'])
def send_button():
    """Endpoint para enviar mensajes con botones de respuesta"""
    global whatsapp_service, queue_service
    
    if not whatsapp_service:
        init_services()
    
    try:
        if not whatsapp_service:
            return jsonify({"error": "Servicio no disponible"}), 500
        
        data = request.json
        phone = data.get('phone')
        header_type = data.get('header_type')
        header_content = data.get('header_content')
        body_text = data.get('body_text')
        buttons = data.get('buttons', [])
        footer_text = data.get('footer_text')
        use_queue = data.get('use_queue', False)
        
        if not phone or not body_text:
            return jsonify({"error": "Faltan parámetros: phone y body_text son requeridos"}), 400
        
        if not buttons or not isinstance(buttons, list) or len(buttons) == 0:
            return jsonify({"error": "Se requiere al menos un botón en el campo 'buttons'"}), 400
        
        if len(buttons) > 3:
            return jsonify({"error": "Máximo 3 botones permitidos"}), 400
        
        # Validar estructura de botones
        for i, button in enumerate(buttons):
            if not isinstance(button, dict):
                return jsonify({"error": f"Botón {i+1} debe ser un objeto"}), 400
            
            if not button.get('id'):
                return jsonify({"error": f"Botón {i+1} debe tener un 'id'"}), 400
            
            if not button.get('title'):
                return jsonify({"error": f"Botón {i+1} debe tener un 'title'"}), 400
            
            if len(button['title']) > 20:
                return jsonify({"error": f"Título del botón {i+1} debe tener máximo 20 caracteres"}), 400
        
        if use_queue and queue_service:
            # Enviar usando cola
            task = queue_service.send_button_message_async(
                phone, header_type, header_content, body_text, buttons, footer_text
            )
            return jsonify({
                "success": True,
                "message": "Mensaje con botones enviado a cola",
                "task_id": task.id
            }), 200
        else:
            # Enviar directamente
            result = whatsapp_service.send_button_message(
                phone, header_type, header_content, body_text, buttons, footer_text
            )
            
            if result['success']:
                return jsonify({
                    "success": True,
                    "message": "Mensaje con botones enviado exitosamente",
                    "data": result['data']
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": result['error']
                }), 400
            
    except Exception as e:
        logger.error(f"Error enviando mensaje con botones: {str(e)}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/send-bulk-button', methods=['POST'])
def send_bulk_button():
    """Endpoint para envío masivo de mensajes con botones de respuesta"""
    global whatsapp_service, queue_service
    
    if not whatsapp_service:
        init_services()
    
    try:
        if not whatsapp_service:
            return jsonify({"error": "Servicio no disponible"}), 500
        
        data = request.json
        
        if not data:
            return jsonify({"error": "Se requiere un JSON con los datos del mensaje"}), 400
        
        # Validar que se proporcionen los recipients
        recipients = data.get('recipients', [])
        if not isinstance(recipients, list) or len(recipients) == 0:
            return jsonify({"error": "Se requiere el campo 'recipients' con un array de destinatarios"}), 400
        
        # Validar estructura de recipients
        for recipient in recipients:
            if not isinstance(recipient, dict):
                return jsonify({"error": "Cada recipient debe ser un objeto"}), 400
            
            phone = recipient.get('phone')
            body_text = recipient.get('body_text')
            
            if not phone:
                return jsonify({"error": "Cada recipient debe tener un 'phone'"}), 400
            
            if not body_text:
                return jsonify({"error": "Cada recipient debe tener un 'body_text'"}), 400
        
        # Extraer parámetros comunes del mensaje
        header_type = data.get('header_type')
        header_content = data.get('header_content')
        buttons = data.get('buttons', [])
        footer_text = data.get('footer_text')
        use_queue = data.get('use_queue', True)  # Por defecto usar cola para masivos
        
        # Validar botones comunes requeridos
        if not buttons or not isinstance(buttons, list) or len(buttons) == 0:
            return jsonify({"error": "Se requiere al menos un botón en el campo 'buttons'"}), 400
        
        if len(buttons) > 3:
            return jsonify({"error": "Máximo 3 botones permitidos"}), 400
        
        # Validar estructura de botones
        for i, button in enumerate(buttons):
            if not isinstance(button, dict):
                return jsonify({"error": f"Botón {i+1} debe ser un objeto"}), 400
            
            if not button.get('id'):
                return jsonify({"error": f"Botón {i+1} debe tener un 'id'"}), 400
            
            if not button.get('title'):
                return jsonify({"error": f"Botón {i+1} debe tener un 'title'"}), 400
            
            if len(button['title']) > 20:
                return jsonify({"error": f"Título del botón {i+1} debe tener máximo 20 caracteres"}), 400
        
        if use_queue and queue_service:
            # Enviar usando cola
            task = queue_service.send_bulk_button_messages_async(
                recipients, header_type, header_content, buttons, footer_text
            )
            return jsonify({
                "success": True,
                "message": "Envío masivo de botones enviado a cola",
                "task_id": task.id
            }), 200
        else:
            # Enviar directamente
            result = whatsapp_service.send_bulk_button_messages(
                recipients, header_type, header_content, buttons, footer_text
            )
            
            return jsonify({
                "success": True,
                "message": "Envío masivo de botones completado",
                "result": result
            }), 200
        
    except Exception as e:
        logger.error(f"Error en envío masivo de botones: {str(e)}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/send-broadcast-interactive', methods=['POST'])
def send_broadcast_interactive():
    """Endpoint para enviar el mismo mensaje interactivo a múltiples números"""
    global whatsapp_service, queue_service
    
    if not whatsapp_service:
        init_services()
    
    try:
        if not whatsapp_service:
            return jsonify({"error": "Servicio no disponible"}), 500
        
        data = request.json
        
        if not data:
            return jsonify({"error": "Se requiere un JSON con los datos del mensaje"}), 400
        
        # Validar que se proporcionen los números telefónicos
        phones = data.get('phones', [])
        if not isinstance(phones, list) or len(phones) == 0:
            return jsonify({"error": "Se requiere el campo 'phones' con un array de números telefónicos"}), 400
        
        # Validar que haya al menos body_text
        body_text = data.get('body_text')
        if not body_text:
            return jsonify({"error": "Se requiere el campo 'body_text'"}), 400
        
        # Extraer parámetros del mensaje
        header_type = data.get('header_type')
        header_content = data.get('header_content')
        button_text = data.get('button_text')
        button_url = data.get('button_url')
        footer_text = data.get('footer_text')
        use_queue = data.get('use_queue', True)  # Por defecto usar cola para masivos
        
        if use_queue and queue_service:
            # Enviar usando cola
            task = queue_service.send_broadcast_interactive_message_async(
                phones, header_type, header_content, body_text, 
                button_text, button_url, footer_text
            )
            return jsonify({
                "success": True,
                "message": "Mensaje broadcast enviado a cola",
                "task_id": task.id
            }), 200
        else:
            # Enviar directamente
            result = whatsapp_service.send_broadcast_interactive_message(
                phones, header_type, header_content, body_text, 
                button_text, button_url, footer_text
            )
            
            return jsonify({
                "success": True,
                "message": "Mensaje broadcast procesado",
                "result": result
            }), 200
        
    except Exception as e:
        logger.error(f"Error en broadcast interactive message: {str(e)}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/send-personalized-broadcast', methods=['POST'])
def send_personalized_broadcast():
    """Endpoint para enviar mensajes interactivos personalizados (broadcast personalizado)"""
    global whatsapp_service, queue_service
    
    if not whatsapp_service:
        init_services()
    
    try:
        if not whatsapp_service:
            return jsonify({"error": "Servicio no disponible"}), 500
        
        data = request.json
        
        if not data:
            return jsonify({"error": "Se requiere un JSON con los datos del mensaje"}), 400
        
        # Validar que se proporcionen los recipients
        recipients = data.get('recipients', [])
        if not isinstance(recipients, list) or len(recipients) == 0:
            return jsonify({"error": "Se requiere el campo 'recipients' con un array de destinatarios"}), 400
        
        # Validar estructura de recipients
        for recipient in recipients:
            if not isinstance(recipient, dict):
                return jsonify({"error": "Cada recipient debe ser un objeto"}), 400
            
            phone = recipient.get('phone')
            body_text = recipient.get('body_text')
            
            if not phone:
                return jsonify({"error": "Cada recipient debe tener un 'phone'"}), 400
            
            if not body_text:
                return jsonify({"error": "Cada recipient debe tener un 'body_text'"}), 400
        
        # Extraer parámetros comunes del mensaje
        header_type = data.get('header_type')
        header_content = data.get('header_content')
        button_text = data.get('button_text')
        button_url = data.get('button_url')
        footer_text = data.get('footer_text')
        use_queue = data.get('use_queue', True)  # Por defecto usar cola para masivos
        
        if use_queue and queue_service:
            # Enviar usando cola
            task = queue_service.send_personalized_broadcast_messages_async(
                recipients, header_type, header_content, button_text, button_url, footer_text
            )
            return jsonify({
                "success": True,
                "message": "Broadcast personalizado enviado a cola",
                "task_id": task.id
            }), 200
        else:
            # Enviar directamente
            result = whatsapp_service.send_personalized_broadcast_messages(
                recipients, header_type, header_content, button_text, button_url, footer_text
            )
            
            return jsonify({
                "success": True,
                "message": "Broadcast personalizado procesado",
                "result": result
            }), 200
        
    except Exception as e:
        logger.error(f"Error en broadcast personalizado: {str(e)}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/send-template-advanced', methods=['POST'])
def send_template_advanced():
    """Endpoint para enviar plantillas con soporte completo para componentes"""
    global whatsapp_service, queue_service
    
    if not whatsapp_service:
        init_services()
    
    try:
        if not whatsapp_service:
            return jsonify({"error": "Servicio no disponible"}), 500
        
        data = request.json
        phone = data.get('phone')
        template_name = data.get('template_name')
        language = data.get('language', 'es')
        components = data.get('components')
        parameters = data.get('parameters')  # Compatibilidad hacia atrás
        use_queue = data.get('use_queue', False)
        
        if not phone or not template_name:
            return jsonify({"error": "Faltan parámetros: phone y template_name son requeridos"}), 400
        
        if use_queue and queue_service:
            # Enviar usando cola
            task = queue_service.send_template_message_advanced_async(
                phone, template_name, language, components, parameters
            )
            return jsonify({
                "success": True,
                "message": "Plantilla avanzada enviada a cola",
                "task_id": task.id
            }), 200
        else:
            # Enviar directamente
            result = whatsapp_service.send_template_message_advanced(
                phone, template_name, language, components, parameters
            )
            
            if result['success']:
                return jsonify({
                    "success": True,
                    "message": "Plantilla avanzada enviada exitosamente",
                    "data": result['data']
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": result['error']
                }), 400
            
    except Exception as e:
        logger.error(f"Error enviando plantilla avanzada: {str(e)}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/send-bulk-template', methods=['POST'])
def send_bulk_template():
    """Endpoint para envío masivo de plantillas personalizadas"""
    global whatsapp_service, queue_service
    
    if not whatsapp_service:
        init_services()
    
    try:
        if not whatsapp_service:
            return jsonify({"error": "Servicio no disponible"}), 500
        
        data = request.json
        recipients = data.get('recipients', [])
        use_queue = data.get('use_queue', False)  # Forzar False para evitar error EntryPoints
        
        if not recipients:
            return jsonify({"error": "Falta parámetro: recipients es requerido"}), 400
        
        # Validar estructura de recipients
        for recipient in recipients:
            if not recipient.get('phone') or not recipient.get('template_name'):
                return jsonify({"error": "Cada recipient debe tener 'phone' y 'template_name'"}), 400
        
        # Temporalmente deshabilitado el uso de cola debido a error EntryPoints
        # if use_queue and queue_service:
        #     # Enviar usando cola
        #     task = queue_service.send_bulk_template_messages_async(recipients)
        #     return jsonify({
        #         "success": True,
        #         "message": "Envío masivo de plantillas enviado a cola",
        #         "task_id": task.id
        #     }), 200
        # else:
        # Enviar directamente
        result = whatsapp_service.send_bulk_template_messages(recipients)
        
        return jsonify({
            "success": True,
            "message": "Envío masivo de plantillas completado",
            "result": result
        }), 200
        
    except Exception as e:
        logger.error(f"Error en envío masivo de plantillas: {str(e)}")
        return jsonify({"error": str(e)}), 500

@messages_bp.route('/send-broadcast-template', methods=['POST'])
def send_broadcast_template():
    """Endpoint para enviar la misma plantilla a múltiples números"""
    global whatsapp_service, queue_service
    
    if not whatsapp_service:
        init_services()
    
    try:
        if not whatsapp_service:
            return jsonify({"error": "Servicio no disponible"}), 500
        
        data = request.json
        
        if not data:
            return jsonify({"error": "Se requiere un JSON con los datos del mensaje"}), 400
        
        # Validar que se proporcionen los números telefónicos
        phones = data.get('phones', [])
        if not isinstance(phones, list) or len(phones) == 0:
            return jsonify({"error": "Se requiere el campo 'phones' con un array de números telefónicos"}), 400
        
        # Validar que haya al least template_name
        template_name = data.get('template_name')
        if not template_name:
            return jsonify({"error": "Se requiere el campo 'template_name'"}), 400
        
        # Extraer parámetros de la plantilla
        language = data.get('language', 'es')
        components = data.get('components')
        parameters = data.get('parameters')  # Compatibilidad hacia atrás
        use_queue = data.get('use_queue', True)  # Por defecto usar cola para masivos
        
        if use_queue and queue_service:
            # Enviar usando cola
            task = queue_service.send_broadcast_template_message_async(
                phones, template_name, language, components, parameters
            )
            return jsonify({
                "success": True,
                "message": "Broadcast de plantilla enviado a cola",
                "task_id": task.id
            }), 200
        else:
            # Enviar directamente
            result = whatsapp_service.send_broadcast_template_message(
                phones, template_name, language, components, parameters
            )
            
            return jsonify({
                "success": True,
                "message": "Broadcast de plantilla procesado",
                "result": result
            }), 200
        
    except Exception as e:
        logger.error(f"Error en broadcast de plantilla: {str(e)}")
        return jsonify({"error": str(e)}), 500

