import sqlite3
import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict, List
from threading import Lock

logger = logging.getLogger(__name__)

class NumberCache:
    def __init__(self, db_path: str = None):
        # Usar variable de entorno o default
        if db_path is None:
            db_path = os.getenv('CACHE_DB_PATH', '/app/data/cache.db')
        
        self.db_path = db_path
        self.lock = Lock()
        
        # CREAR DIRECTORIO PADRE AUTOMÁTICAMENTE
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"✅ Directorio creado: {db_dir}")
            except Exception as e:
                logger.error(f"❌ Error creando directorio {db_dir}: {e}")
        
        logger.info(f"🗄️ Inicializando cache en: {self.db_path}")
        self._init_db()
    
    def _init_db(self):
        """Inicializa la base de datos"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Tabla simple para números
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS numbers (
                        phone TEXT PRIMARY KEY,
                        name TEXT,
                        data TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                ''')
                
                conn.commit()
                conn.close()
                
                # Verificar que se creó correctamente
                if os.path.exists(self.db_path):
                    logger.info(f"✅ Base de datos cache inicializada: {self.db_path}")
                else:
                    logger.error(f"❌ Base de datos NO se creó: {self.db_path}")
                    
            except Exception as e:
                logger.error(f"❌ Error inicializando base de datos: {e}")
                raise
    
    def add_number(self, phone: str, name: str = None, data: Dict = None) -> bool:
        """Agrega un número. Si ya existe, elimina el registro anterior y crea uno nuevo"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Verificar si el número ya existe
                cursor.execute('SELECT phone FROM numbers WHERE phone = ?', (phone,))
                existing = cursor.fetchone()
                
                if existing:
                    # El número ya existe, eliminarlo primero
                    logger.info(f"Número {phone} ya existe en cache, eliminando registro anterior")
                    cursor.execute('DELETE FROM numbers WHERE phone = ?', (phone,))
                    logger.info(f"Registro anterior de {phone} eliminado")
                
                # Crear nuevo registro (siempre con timestamp actual)
                now = datetime.now().isoformat()
                data_str = json.dumps(data) if data else None
                
                logger.info(f"Creando nuevo registro para {phone}")
                cursor.execute('''
                    INSERT INTO numbers 
                    (phone, name, data, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (phone, name, data_str, now, now))
                
                conn.commit()
                conn.close()
                return True
                
        except Exception as e:
            logger.error(f"Error adding number {phone}: {str(e)}")
            return False
    
    def exists(self, phone: str) -> bool:
        """Verifica si un número existe en el cache"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('SELECT 1 FROM numbers WHERE phone = ? LIMIT 1', (phone,))
                exists = cursor.fetchone() is not None
                conn.close()
                
                return exists
                
        except Exception as e:
            logger.error(f"Error checking if number {phone} exists: {str(e)}")
            return False
    
    def get_number(self, phone: str) -> Optional[Dict]:
        """Obtiene información de un número"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM numbers WHERE phone = ?', (phone,))
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    result = dict(row)
                    if result['data']:
                        result['data'] = json.loads(result['data'])
                    return result
                return None
                
        except Exception as e:
            logger.error(f"Error getting number {phone}: {str(e)}")
            return None
    
    def get_all_numbers(self) -> List[Dict]:
        """Obtiene todos los números"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM numbers ORDER BY updated_at DESC')
                rows = cursor.fetchall()
                conn.close()

                results = []
                for row in rows:
                    result = dict(row)
                    if result['data']:
                        result['data'] = json.loads(result['data'])
                    results.append(result)

                return results

        except Exception as e:
            logger.error(f"Error getting all numbers: {str(e)}")
            return []

    def find_by_alert_id(self, alert_id: str, manager_only: bool = False) -> List[Dict]:
        """Devuelve los números cuyo cache referencia alert_id en info_alert.alert_id.

        Si manager_only=True, filtra solo los que tienen rol.is_alert_manager True.
        """
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM numbers')
                rows = cursor.fetchall()
                conn.close()

            matches: List[Dict] = []
            for row in rows:
                raw_data = row['data']
                if not raw_data:
                    continue
                try:
                    parsed = json.loads(raw_data)
                except Exception:
                    continue
                info_alert = parsed.get('info_alert') if isinstance(parsed, dict) else None
                if not isinstance(info_alert, dict):
                    continue
                if str(info_alert.get('alert_id', '')) != str(alert_id):
                    continue
                if manager_only:
                    rol = parsed.get('rol') if isinstance(parsed, dict) else None
                    if not isinstance(rol, dict) or not rol.get('is_alert_manager'):
                        continue
                matches.append({
                    'phone': row['phone'],
                    'name': row['name'],
                    'data': parsed
                })
            return matches
        except Exception as e:
            logger.error(f"Error finding numbers by alert_id {alert_id}: {str(e)}")
            return []
    
    def delete_number(self, phone: str) -> bool:
        """Elimina un número"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM numbers WHERE phone = ?', (phone,))
                conn.commit()
                deleted = cursor.rowcount > 0
                conn.close()
                return deleted
                
        except Exception as e:
            logger.error(f"Error deleting number {phone}: {str(e)}")
            return False
    
    def clear_all(self) -> int:
        """Limpia todos los números"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM numbers')
                conn.commit()
                deleted = cursor.rowcount
                conn.close()
                return deleted
                
        except Exception as e:
            logger.error(f"Error clearing all numbers: {str(e)}")
            return 0
    
    def update_number_data(self, phone: str, data_content: Dict) -> bool:
        """Actualiza los datos de un número existente. Si una llave existe, la edita; si no existe, la agrega. Si el valor es '__DELETE__', elimina la llave"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Obtener los datos actuales
                cursor.execute('SELECT data FROM numbers WHERE phone = ?', (phone,))
                row = cursor.fetchone()
                
                if not row:
                    # El número no existe
                    conn.close()
                    return False
                
                # Parsear los datos existentes
                current_data = {}
                if row[0]:
                    current_data = json.loads(row[0])
                
                # Procesar los nuevos datos (contenido extraído de data)
                updated_data = current_data.copy()
                
                for key, value in data_content.items():
                    if value == '__DELETE__':
                        # Eliminar la llave si existe
                        if key in updated_data:
                            del updated_data[key]
                            logger.info(f"Llave '{key}' eliminada del número {phone}")
                    else:
                        # Actualizar o agregar la llave directamente
                        updated_data[key] = value
                
                # Actualizar en la base de datos
                now = datetime.now().isoformat()
                data_str = json.dumps(updated_data)
                
                cursor.execute('''
                    UPDATE numbers 
                    SET data = ?, updated_at = ?
                    WHERE phone = ?
                ''', (data_str, now, phone))
                
                conn.commit()
                success = cursor.rowcount > 0
                conn.close()
                
                if success:
                    logger.info(f"Datos actualizados para número {phone}")
                
                return success
                
        except Exception as e:
            logger.error(f"Error updating number data {phone}: {str(e)}")
            return False

# Instancia global
_cache_instance = None

def get_number_cache() -> NumberCache:
    """Obtiene la instancia del cache de números"""
    global _cache_instance
    if _cache_instance is None:
        try:
            db_path = os.getenv('CACHE_DB_PATH', '/app/data/cache.db')
            logger.info(f"🎯 Creando cache singleton en: {db_path}")
            _cache_instance = NumberCache(db_path)
            logger.info("✅ Cache singleton creado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error creando cache singleton: {e}")
            raise
    return _cache_instance