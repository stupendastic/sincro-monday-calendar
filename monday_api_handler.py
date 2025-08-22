#!/usr/bin/env python3
"""
Monday.com API Handler - Sistema Unificado
Handler centralizado para todas las operaciones con la API de Monday.com

Características:
- Manejo de rate limits y complexity exceptions
- Reintentos automáticos con backoff exponencial
- Tipado correcto según tipo de columna
- Paginación automática
- Validaciones de entrada
- Logging detallado

Basado en: https://developer.monday.com/api-reference
Autor: Sistema Unificado Monday.com
Fecha: 2025-08-01
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ColumnInfo:
    id: str
    title: str
    type: str
    settings_str: str = ""
    description: str = ""

@dataclass
class ItemInfo:
    id: str
    name: str
    column_values: List[Dict] = None
    subitems: List[Dict] = None

class MondayAPIHandler:
    """Handler centralizado para Monday.com API con mejores prácticas"""
    
    def __init__(self, api_token: str, logger: Optional[logging.Logger] = None):
        self.API_TOKEN = api_token
        self.HEADERS = {
            'Authorization': self.API_TOKEN,
            'Content-Type': 'application/json'
        }
        self.API_URL = 'https://api.monday.com/v2/'
        
        # Configurar logger
        self.logger = logger or self._setup_default_logger()
        
        # Configuración de reintentos
        self.MAX_RETRIES = 3
        self.BASE_WAIT_TIME = 30
        self.COMPLEXITY_WAIT_TIME = 60
        
        # Tipos de columna soportados con sus configuraciones
        self.COLUMN_TYPES = {
            'text': {'api_name': 'text', 'mutation_type': 'simple'},
            'long_text': {'api_name': 'long_text', 'mutation_type': 'simple'},
            'numbers': {'api_name': 'numbers', 'mutation_type': 'simple'},
            'color': {'api_name': 'color', 'mutation_type': 'simple', 'requires_labels': True},
            'status': {'api_name': 'color', 'mutation_type': 'simple', 'requires_labels': True},  # STATUS = color
            'date': {'api_name': 'date', 'mutation_type': 'complex'},
            'timerange': {'api_name': 'timerange', 'mutation_type': 'complex'},
            'people': {'api_name': 'people', 'mutation_type': 'complex'},
            'board_relation': {'api_name': 'board_relation', 'mutation_type': 'complex', 'requires_target_board': True},
            'file': {'api_name': 'file', 'mutation_type': 'complex'},
            'link': {'api_name': 'link', 'mutation_type': 'complex'},
            'dropdown': {'api_name': 'dropdown', 'mutation_type': 'complex', 'requires_options': True},
            'formula': {'processable': False, 'note': 'Read-only, cannot sync via API'},
            'lookup': {'processable': False, 'note': 'Mirror column, create native column instead'}
        }
    
    def _setup_default_logger(self) -> logging.Logger:
        """Configurar logger por defecto"""
        logger = logging.getLogger('monday_api_handler')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _make_request(self, query: str, variables: Optional[Dict] = None, max_retries: Optional[int] = None) -> Optional[Dict]:
        """Realizar petición GraphQL con manejo de errores y reintentos"""
        max_retries = max_retries or self.MAX_RETRIES
        wait_time = self.BASE_WAIT_TIME
        
        for retry in range(max_retries + 1):
            try:
                payload = {'query': query}
                if variables:
                    payload['variables'] = variables
                
                response = requests.post(self.API_URL, json=payload, headers=self.HEADERS, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verificar errores GraphQL
                    if 'errors' in data:
                        error_msg = str(data['errors'])
                        
                        # Manejo específico de ComplexityException
                        if 'ComplexityException' in error_msg:
                            if retry < max_retries:
                                self.logger.warning(f"ComplexityException - Esperando {self.COMPLEXITY_WAIT_TIME}s (intento {retry + 1}/{max_retries + 1})")
                                time.sleep(self.COMPLEXITY_WAIT_TIME)
                                continue
                            else:
                                self.logger.error("ComplexityException - Max reintentos alcanzados")
                                return None
                        
                        # Otros errores GraphQL
                        self.logger.error(f"Error GraphQL: {error_msg}")
                        return None
                    
                    return data
                
                elif response.status_code == 429:  # Rate limit
                    if retry < max_retries:
                        self.logger.warning(f"Rate limit - Esperando {wait_time}s (intento {retry + 1}/{max_retries + 1})")
                        time.sleep(wait_time)
                        wait_time += 15
                        continue
                    else:
                        self.logger.error("Rate limit - Max reintentos alcanzados")
                        return None
                
                else:
                    self.logger.error(f"Error HTTP {response.status_code}: {response.text}")
                    return None
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout - Reintentando en {wait_time}s (intento {retry + 1}/{max_retries + 1})")
                if retry < max_retries:
                    time.sleep(wait_time)
                    wait_time += 10
                    continue
                return None
                
            except Exception as e:
                self.logger.error(f"Excepción en petición: {str(e)}")
                return None
        
        return None
    
    def get_board_columns(self, board_id: str) -> List[ColumnInfo]:
        """Obtener columnas de un tablero"""
        self.logger.info(f"Obteniendo columnas del tablero {board_id}")
        
        query = '''
        query($boardId: [ID!]!) {
            boards(ids: $boardId) {
                columns {
                    id
                    title
                    type
                    settings_str
                    description
                }
            }
        }
        '''
        
        variables = {'boardId': board_id}
        data = self._make_request(query, variables)
        
        if data and data.get('data', {}).get('boards') and data['data']['boards'][0]:
            columns_data = data['data']['boards'][0]['columns']
            columns = []
            
            for col_data in columns_data:
                columns.append(ColumnInfo(
                    id=col_data['id'],
                    title=col_data['title'],
                    type=col_data['type'],
                    settings_str=col_data.get('settings_str', ''),
                    description=col_data.get('description', '')
                ))
            
            self.logger.info(f"Obtenidas {len(columns)} columnas")
            return columns
        
        self.logger.error(f"No se pudieron obtener columnas del tablero {board_id}")
        return []
    
    def get_column_info(self, board_id: str, column_id: str) -> Optional[ColumnInfo]:
        """Obtener información específica de una columna"""
        self.logger.info(f"Analizando columna {column_id} del tablero {board_id}")
        
        query = '''
        query($boardId: [ID!]!, $columnId: [String!]!) {
            boards(ids: $boardId) {
                columns(ids: $columnId) {
                    id
                    title
                    type
                    settings_str
                    description
                }
            }
        }
        '''
        
        variables = {'boardId': board_id, 'columnId': column_id}
        data = self._make_request(query, variables)
        
        if data and data.get('data', {}).get('boards') and data['data']['boards'][0]['columns']:
            col_data = data['data']['boards'][0]['columns'][0]
            return ColumnInfo(
                id=col_data['id'],
                title=col_data['title'],
                type=col_data['type'],
                settings_str=col_data.get('settings_str', ''),
                description=col_data.get('description', '')
            )
        
        return None
    
    def get_column_details(self, board_id: str, column_id: str) -> Optional[Dict]:
        """Obtiene los detalles completos de una columna específica."""
        query = f'''
        query {{
            boards(ids: [{board_id}]) {{
                columns(ids: ["{column_id}"]) {{
                    id
                    title
                    type
                    settings_str
                }}
            }}
        }}
        '''
        data = self._make_request(query)
        if data and data.get('data', {}).get('boards') and data['data']['boards'][0]['columns']:
            return data['data']['boards'][0]['columns'][0]
        self.logger.error(f"No se pudo encontrar la columna {column_id} en el tablero {board_id}.")
        return None
    
    def create_column(self, board_id: str, title: str, column_type: str, 
                     description: str = "", settings_str: str = "", defaults: Optional[Dict] = None, 
                     settings: Optional[Dict] = None) -> Optional[str]:
        """Crear una nueva columna en un tablero con soporte para replicar configuración exacta vía settings_str"""
        self.logger.info(f"Creando columna '{title}' tipo {column_type} en tablero {board_id}")
        
        # Validar tipo de columna
        if column_type not in self.COLUMN_TYPES:
            self.logger.error(f"Tipo de columna no soportado: {column_type}")
            return None
        
        if not self.COLUMN_TYPES[column_type].get('processable', True):
            self.logger.error(f"Tipo de columna no procesable: {column_type}")
            return None
        
        # Construir mutación base
        mutation_parts = [
            f'board_id: {board_id}',
            f'title: "{title}"',
            f'column_type: {column_type}'
        ]
        
        if description:
            mutation_parts.append(f'description: "{description}"')
        
        # Prioridad: settings > defaults > settings_str
        if settings:
            settings_string = json.dumps(settings)
            escaped_settings_string = json.dumps(settings_string)
            mutation_parts.append(f'settings_str: {escaped_settings_string}')
        elif defaults:
            defaults_str = json.dumps(defaults)
            escaped_defaults = defaults_str.replace('\\', '\\\\').replace('"', '\\"')
            mutation_parts.append(f'defaults: "{escaped_defaults}"')
        elif settings_str and settings_str != '{}':
            escaped_settings = settings_str.replace('\\', '\\\\').replace('"', '\\"')
            mutation_parts.append(f'defaults: "{escaped_settings}"')
        
        mutation = f'''
        mutation {{
            create_column({", ".join(mutation_parts)}) {{
                id
                title
                type
            }}
        }}
        '''
        
        data = self._make_request(mutation)
        
        if data and 'data' in data and 'create_column' in data['data']:
            new_id = data['data']['create_column']['id']
            self.logger.info(f"Columna creada exitosamente: {title} → {new_id}")
            return new_id
        
        # Si falló y tenía configuración, reintentar sin ella
        if (settings or defaults or (settings_str and settings_str != '{}')):
            self.logger.info("Reintentando creación sin configuración personalizada...")
            
            simple_mutation = f'''
            mutation {{
                create_column(
                    board_id: {board_id},
                    title: "{title}",
                    column_type: {column_type}
                    {f'description: "{description}"' if description else ''}
                ) {{
                    id
                    title
                    type
                }}
            }}
            '''
            
            data = self._make_request(simple_mutation)
            if data and 'data' in data and 'create_column' in data['data']:
                new_id = data['data']['create_column']['id']
                self.logger.info(f"Columna creada sin configuración: {title} → {new_id}")
                return new_id
        
        self.logger.error(f"No se pudo crear la columna {title}")
        return None

    def update_column_labels(self, board_id: str, column_id: str, labels: dict) -> bool:
        """Actualizar labels y colores de una columna STATUS"""
        try:
            # Convertir labels a formato JSON para la mutación
            labels_json = json.dumps(labels)
            
            mutation = f'''
            mutation {{
                change_column_settings(
                    board_id: {board_id},
                    column_id: "{column_id}",
                    settings: "{labels_json}"
                ) {{
                    id
                }}
            }}
            '''
            
            data = self._make_request(mutation)
            
            if data and data.get('data', {}).get('change_column_settings'):
                self.logger.info(f"Labels actualizados para columna {column_id}")
                return True
            else:
                self.logger.error(f"Error actualizando labels para columna {column_id}")
                if data and data.get('errors'):
                    self.logger.error(f"Errores: {data['errors']}")
                return False
                
        except Exception as e:
            self.logger.error(f"Excepción actualizando labels: {e}")
            return False
    
    def get_board_items(self, board_id: str, column_ids: Optional[List[str]] = None, 
                       limit: int = 500) -> List[ItemInfo]:
        """Obtener elementos de un tablero con paginación automática"""
        self.logger.info(f"Obteniendo elementos del tablero {board_id}")
        
        column_filter = ""
        if column_ids:
            column_ids_str = '", "'.join(column_ids)
            column_filter = f'(ids: ["{column_ids_str}"])'
        
        query = f'''
        query($boardId: [ID!]!, $limit: Int!) {{
            boards(ids: $boardId) {{
                items_page(limit: $limit) {{
                    cursor
                    items {{
                        id
                        name
                        column_values{column_filter} {{
                            id
                            value
                            text
                            type
                        }}
                        subitems {{
                            id
                            name
                            column_values{column_filter} {{
                                id
                                value
                                text
                                type
                            }}
                        }}
                    }}
                }}
            }}
        }}
        '''
        
        variables = {'boardId': board_id, 'limit': limit}
        data = self._make_request(query, variables)
        
        if not data or not data.get('data', {}).get('boards'):
            self.logger.error(f"No se pudieron obtener elementos del tablero {board_id}")
            return []
        
        board_data = data['data']['boards'][0]
        if not board_data or not board_data.get('items_page'):
            self.logger.warning(f"No se encontraron elementos en el tablero {board_id}")
            return []
        
        items_data = board_data['items_page']['items']
        all_items = []
        
        for item_data in items_data:
            item = ItemInfo(
                id=item_data['id'],
                name=item_data['name'],
                column_values=item_data.get('column_values', []),
                subitems=item_data.get('subitems', [])
            )
            all_items.append(item)
        
        # TODO: Implementar paginación completa si es necesario
        cursor = board_data['items_page'].get('cursor')
        if cursor:
            self.logger.warning(f"Hay más elementos disponibles (cursor: {cursor[:20]}...)")
        
        self.logger.info(f"Obtenidos {len(all_items)} elementos")
        return all_items

    def get_items(self, board_id: str, column_ids: Optional[List[str]] = None, limit_per_page: int = 100) -> List[Dict]:
        """Obtiene todos los items, usando Fragmentos en Línea para leer datos de Conexión y Reflejo"""
        self.logger.info(f"Obteniendo items con fragmentos en línea del tablero {board_id}")
        
        column_ids = column_ids or []
        
        column_query = ''
        if column_ids:
            column_query = f'''
            column_values(ids: {json.dumps(column_ids)}) {{
                id
                text
                value
                type
                ... on BoardRelationValue {{
                    linked_item_ids
                }}
                ... on MirrorValue {{
                    display_value
                }}
            }}'''
        else:
            column_query = '''
            column_values {
                id
                text
                value
                type
                ... on BoardRelationValue {
                    linked_item_ids
                }
                ... on MirrorValue {
                    display_value
                }
            }'''
        
        query = f'''
        query($boardId: [ID!]!, $limit: Int!, $cursor: String) {{
            boards(ids: $boardId) {{
                items_page(limit: $limit, cursor: $cursor) {{
                    cursor
                    items {{
                        id
                        name
                        {column_query}
                    }}
                }}
            }}
        }}
        '''
        
        all_items = []
        cursor = None
        
        while True:
            variables = {'boardId': board_id, 'limit': limit_per_page}
            if cursor:
                variables['cursor'] = cursor
            
            data = self._make_request(query, variables)
            
            if not data or not data.get('data', {}).get('boards'):
                self.logger.error(f"No se pudieron obtener items del tablero {board_id}")
                break
            
            board_data = data['data']['boards'][0]
            if not board_data or not board_data.get('items_page'):
                self.logger.warning(f"No se encontraron items en el tablero {board_id}")
                break
            
            items_page = board_data['items_page']
            items_data = items_page['items']
            all_items.extend(items_data)
            
            # Obtener cursor para la siguiente página
            cursor = items_page.get('cursor')
            if not cursor:
                break
            
            self.logger.info(f"Obtenida página con {len(items_data)} items (total: {len(all_items)})")
        
        self.logger.info(f"Obtenidos {len(all_items)} items totales con fragmentos en línea")
        return all_items
    
    def update_column_value(self, item_id: str, board_id: str, column_id: str, 
                           value: Any, column_type: str) -> bool:
        """Actualizar valor de columna según su tipo con manejo robusto"""
        
        try:
            mutation = self._build_update_mutation(item_id, board_id, column_id, value, column_type)
            if not mutation:
                return False
            
            # Ejecutar con reintentos automáticos para complexity exceptions
            data = self._make_request(mutation, max_retries=self.MAX_RETRIES)
            
            if data and 'data' in data:
                self.logger.debug(f"Elemento {item_id} actualizado exitosamente")
                return True
            else:
                self.logger.error(f"No se pudo actualizar elemento {item_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Excepción actualizando elemento {item_id}: {str(e)}")
            return False
    
    def _build_update_mutation(self, item_id: str, board_id: str, column_id: str, 
                              value: Any, column_type: str) -> Optional[str]:
        """Construir mutación de actualización según el tipo de columna"""
        
        try:
            if column_type in ['color', 'status'] and value is not None:  # Status columns
                # Extraer index del status
                if isinstance(value, dict):
                    if 'label' in value and 'index' in value['label']:
                        status_value = str(value['label']['index'])
                    elif 'index' in value:
                        status_value = str(value['index'])
                    else:
                        status_value = str(value)
                elif isinstance(value, str):
                    # Si es string, intentar extraer el índice del formato Monday.com
                    import re
                    # Buscar patrones como "index:1" o "index:2"
                    match = re.search(r'index:(\d+)', value)
                    if match:
                        status_value = match.group(1)
                    else:
                        # Si no encuentra el patrón, intentar con el valor completo
                        status_value = value
                else:
                    status_value = str(value)
                
                # Limpiar el valor de caracteres no válidos y asegurar que sea solo el número
                status_value = status_value.replace('"', '').replace(',', '').strip()
                # Asegurar que solo contenga dígitos
                if not status_value.isdigit():
                    # Si no es solo dígitos, intentar extraer el número
                    import re
                    digit_match = re.search(r'(\d+)', status_value)
                    if digit_match:
                        status_value = digit_match.group(1)
                    else:
                        status_value = "1"  # Valor por defecto
                
                return f'''
                mutation {{
                    change_simple_column_value(
                        item_id: {item_id}, 
                        board_id: {board_id}, 
                        column_id: "{column_id}", 
                        value: "{status_value}"
                    ) {{
                        id
                    }}
                }}
                '''
            
            elif column_type in ['text', 'long_text']:
                # Texto simple o largo
                text_value = str(value) if value is not None else ""
                escaped_text = text_value.replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
                
                return f'''
                mutation {{
                    change_simple_column_value(
                        item_id: {item_id}, 
                        board_id: {board_id}, 
                        column_id: "{column_id}", 
                        value: "{escaped_text}"
                    ) {{
                        id
                    }}
                }}
                '''
            
            elif column_type == 'numbers':
                # Números - usar change_simple_column_value para números
                if value is None or value == '':
                    numeric_value = 0
                else:
                    try:
                        numeric_value = float(value)
                    except (ValueError, TypeError):
                        numeric_value = 0
                
                return f'''
                mutation {{
                    change_simple_column_value(
                        item_id: {item_id}, 
                        board_id: {board_id}, 
                        column_id: "{column_id}", 
                        value: "{numeric_value}"
                    ) {{
                        id
                    }}
                }}
                '''
            
            elif column_type == 'board_relation':
                # Conexiones entre tableros
                if isinstance(value, dict) and 'linked_item_ids' in value:
                    relation_value = {"item_ids": value['linked_item_ids']}
                elif isinstance(value, list):
                    relation_value = {"item_ids": value}
                else:
                    relation_value = {"item_ids": []}
                
                return f'''
                mutation {{
                    change_column_value(
                        item_id: {item_id}, 
                        board_id: {board_id}, 
                        column_id: "{column_id}", 
                        value: {json.dumps(json.dumps(relation_value))}
                    ) {{
                        id
                    }}
                }}
                '''
            
            elif value is None:
                # Limpiar valor
                return f'''
                mutation {{
                    change_simple_column_value(
                        item_id: {item_id}, 
                        board_id: {board_id}, 
                        column_id: "{column_id}", 
                        value: ""
                    ) {{
                        id
                    }}
                }}
                '''
            
            else:
                # Otros tipos complejos
                return f'''
                mutation {{
                    change_column_value(
                        item_id: {item_id}, 
                        board_id: {board_id}, 
                        column_id: "{column_id}", 
                        value: {json.dumps(json.dumps(value))}
                    ) {{
                        id
                    }}
                }}
                '''
                
        except Exception as e:
            self.logger.error(f"Error construyendo mutación para {column_type}: {str(e)}")
            return None
    
    def search_items_by_name(self, board_id: str, item_name: str, exact_match: bool = True) -> List[ItemInfo]:
        """Buscar elementos por nombre con matching exacto o parcial"""
        self.logger.info(f"Buscando elementos en tablero {board_id} con nombre: {item_name}")
        
        if exact_match:
            # Búsqueda exacta
            query = '''
            query($boardId: ID!, $itemName: String!) {
                items_page_by_column_values(
                    limit: 100, 
                    board_id: $boardId, 
                    columns: [{column_id: "name", column_values: [$itemName]}]
                ) {
                    cursor
                    items {
                        id
                        name
                        column_values {
                            id
                            value
                            text
                            type
                            ... on StatusValue {
                                label
                            }
                            ... on BoardRelationValue {
                                linked_item_ids
                                linked_items {
                                    id
                                    name
                                    board { id }
                                }
                            }
                        }
                        subitems {
                            id
                            name
                            column_values {
                                id
                                value
                                text
                                type
                            }
                        }
                    }
                }
            }
            '''
            variables = {'boardId': board_id, 'itemName': item_name}
        else:
            # Búsqueda con contains (para prefijos)
            query = '''
            query($boardId: ID!, $itemName: CompareValue!) {
                boards(ids: [$boardId]) {
                    items_page(
                        query_params: {
                            rules: [{
                                column_id: "name", 
                                compare_value: $itemName, 
                                operator: contains_text
                            }]
                        }
                    ) {
                        cursor
                        items {
                            id
                            name
                            column_values {
                                id
                                value
                                text
                                type
                            }
                            subitems {
                                id
                                name
                                column_values {
                                    id
                                    value
                                    text
                                    type
                                }
                            }
                        }
                    }
                }
            }
            '''
            variables = {'boardId': board_id, 'itemName': item_name}
        
        data = self._make_request(query, variables)
        
        if not data or not data.get('data'):
            return []
        
        # Extraer items según el tipo de query
        if exact_match:
            items_data = data['data'].get('items_page_by_column_values', {}).get('items', [])
        else:
            board_data = data['data'].get('boards', [])
            if not board_data:
                return []
            items_data = board_data[0].get('items_page', {}).get('items', [])
        
        items = []
        for item_data in items_data:
            item = ItemInfo(
                id=item_data['id'],
                name=item_data['name'],
                column_values=item_data.get('column_values', []),
                subitems=item_data.get('subitems', [])
            )
            items.append(item)
        
        self.logger.info(f"Encontrados {len(items)} elementos")
        return items
    
    def is_column_type_supported(self, column_type: str) -> bool:
        """Verificar si un tipo de columna es soportado para sincronización"""
        return column_type in self.COLUMN_TYPES and self.COLUMN_TYPES[column_type].get('processable', True)
    
    def get_column_type_info(self, column_type: str) -> Optional[Dict]:
        """Obtener información sobre un tipo de columna"""
        return self.COLUMN_TYPES.get(column_type)
