from flask import Blueprint, request, jsonify
import logging
from services.simple_cache import get_number_cache

logger = logging.getLogger(__name__)

simple_cache_bp = Blueprint('simple_cache', __name__)

@simple_cache_bp.route('/numbers', methods=['GET'])
def get_numbers():
    """Obtiene todos los números"""
    try:
        cache = get_number_cache()
        numbers = cache.get_all_numbers()
        return jsonify({
            "success": True,
            "numbers": numbers,
            "total": len(numbers)
        }), 200
    except Exception as e:
        logger.error(f"Error getting numbers: {str(e)}")
        return jsonify({"error": str(e)}), 500

@simple_cache_bp.route('/numbers/<phone>', methods=['GET'])
def get_number(phone: str):
    """Obtiene información de un número específico"""
    try:
        cache = get_number_cache()
        number = cache.get_number(phone)
        
        if number:
            return jsonify({
                "success": True,
                "number": number
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Number not found"
            }), 404
    except Exception as e:
        logger.error(f"Error getting number: {str(e)}")
        return jsonify({"error": str(e)}), 500

@simple_cache_bp.route('/numbers/<phone>', methods=['PATCH'])
def update_number_cache(phone: str):
    """Actualiza los datos de un número en el cache"""
    try:
        cache = get_number_cache()
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        success = cache.update_number_data(phone, data)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Data for number {phone} updated successfully"
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Number not found"
            }), 404
    except Exception as e:
        logger.error(f"Error updating number: {str(e)}")
        return jsonify({"error": str(e)}), 500

@simple_cache_bp.route('/numbers/update', methods=['PATCH'])
def update_number_cache_body():
    """Actualiza los datos de un número en el cache (phone en el body)"""
    try:
        cache = get_number_cache()
        request_data = request.json
        
        if not request_data:
            return jsonify({"error": "No data provided"}), 400
        
        phone = request_data.get('phone')
        if not phone:
            return jsonify({"error": "Phone number is required"}), 400
        
        data = request_data.get('data')
        if not data:
            return jsonify({"error": "Data object is required"}), 400
        
        success = cache.update_number_data(phone, data)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Data for number {phone} updated successfully"
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Number not found"
            }), 404
    except Exception as e:
        logger.error(f"Error updating number: {str(e)}")
        return jsonify({"error": str(e)}), 500

@simple_cache_bp.route('/numbers/<phone>/exists', methods=['GET'])
def check_number_exists(phone: str):
    """Verifica si un número existe en el cache"""
    try:
        cache = get_number_cache()
        exists = cache.exists(phone)

        return jsonify({
            "success": True,
            "exists": exists,
            "phone": phone
        }), 200
    except Exception as e:
        logger.error(f"Error checking number existence: {str(e)}")
        return jsonify({"error": str(e)}), 500

@simple_cache_bp.route('/numbers/by-alert/<alert_id>', methods=['GET'])
def list_numbers_by_alert(alert_id: str):
    """Lista números con foco en una alerta. Query param manager_only=true filtra managers."""
    try:
        cache = get_number_cache()
        manager_only = (request.args.get('manager_only', 'false').lower() == 'true')
        numbers = cache.find_by_alert_id(alert_id=alert_id, manager_only=manager_only)
        return jsonify({
            "success": True,
            "alert_id": alert_id,
            "manager_only": manager_only,
            "count": len(numbers),
            "numbers": numbers
        }), 200
    except Exception as e:
        logger.error(f"Error finding numbers by alert: {str(e)}")
        return jsonify({"error": str(e)}), 500

@simple_cache_bp.route('/numbers', methods=['POST'])
def add_number():
    """Agrega un número. Si ya existía, elimina el anterior y crea uno nuevo"""
    try:
        data = request.json
        phone = data.get('phone')
        name = data.get('name')
        number_data = data.get('data', {})
        
        if not phone:
            return jsonify({"error": "Phone number is required"}), 400
        
        cache = get_number_cache()
        
        # Verificar si el número ya existe antes de agregarlo
        existed_before = cache.exists(phone)
        success = cache.add_number(phone, name, number_data)
        
        if success:
            if existed_before:
                message = f"Number {phone} existed before, old record deleted and new one created"
                action = "recreated"
            else:
                message = f"Number {phone} created successfully"
                action = "created"
            
            return jsonify({
                "success": True,
                "action": action,
                "message": message,
                "existed_before": existed_before
            }), 201  # Siempre 201 porque siempre se crea un registro nuevo
        else:
            return jsonify({
                "success": False,
                "error": "Failed to add number"
            }), 500
    except Exception as e:
        logger.error(f"Error adding number: {str(e)}")
        return jsonify({"error": str(e)}), 500

@simple_cache_bp.route('/numbers/<phone>', methods=['DELETE'])
def delete_number(phone: str):
    """Elimina un número"""
    try:
        cache = get_number_cache()
        success = cache.delete_number(phone)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Number {phone} deleted successfully"
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Number not found"
            }), 404
    except Exception as e:
        logger.error(f"Error deleting number: {str(e)}")
        return jsonify({"error": str(e)}), 500

@simple_cache_bp.route('/numbers/bulk-update', methods=['PATCH'])
def bulk_update_numbers():
    """Actualiza los datos de múltiples números en el cache de manera simultánea"""
    try:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import os
        
        cache = get_number_cache()
        request_data = request.json
        
        if not request_data:
            return jsonify({"error": "No data provided"}), 400
        
        phones = request_data.get('phones')
        if not phones or not isinstance(phones, list):
            return jsonify({"error": "phones list is required"}), 400
        
        data = request_data.get('data')
        if not data:
            return jsonify({"error": "Data object is required"}), 400
        
        # Función para actualizar un solo número
        def update_single_number(phone):
            try:
                success = cache.update_number_data(phone, data)
                return {
                    "phone": phone,
                    "success": success,
                    "error": None if success else "Number not found"
                }
            except Exception as e:
                return {
                    "phone": phone,
                    "success": False,
                    "error": str(e)
                }
        
        # Resultados de la operación bulk
        results = {
            "total": len(phones),
            "successful": 0,
            "failed": 0,
            "details": []
        }
        
        # Obtener número máximo de workers desde variable de entorno
        max_workers = int(os.getenv('BULK_MAX_WORKERS', 10))
        
        # Procesar actualizaciones simultáneamente usando ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(len(phones), max_workers)) as executor:
            # Enviar todas las tareas al pool de threads
            future_to_phone = {executor.submit(update_single_number, phone): phone for phone in phones}
            
            # Procesar resultados conforme se completan
            for future in as_completed(future_to_phone):
                try:
                    result = future.result()
                    results["details"].append(result)
                    
                    if result["success"]:
                        results["successful"] += 1
                    else:
                        results["failed"] += 1
                        
                except Exception as exc:
                    phone = future_to_phone[future]
                    results["details"].append({
                        "phone": phone,
                        "success": False,
                        "error": f"Exception: {str(exc)}"
                    })
                    results["failed"] += 1
        
        return jsonify({
            "success": True,
            "message": f"Bulk update completed: {results['successful']} successful, {results['failed']} failed",
            "results": results
        }), 200
        
    except Exception as e:
        logger.error(f"Error in bulk update: {str(e)}")
        return jsonify({"error": str(e)}), 500

@simple_cache_bp.route('/numbers/clear', methods=['POST'])
def clear_numbers():
    """Limpia todos los números"""
    try:
        cache = get_number_cache()
        deleted = cache.clear_all()
        
        return jsonify({
            "success": True,
            "deleted": deleted,
            "message": f"Deleted {deleted} numbers"
        }), 200
    except Exception as e:
        logger.error(f"Error clearing numbers: {str(e)}")
        return jsonify({"error": str(e)}), 500
