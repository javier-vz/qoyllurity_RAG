#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GraphRAG v2.0 - Embeddings Semánticos
Optimizado para Raspberry Pi 5 (8GB)
"""

import sys
import re
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
import pickle
import time

from rdflib import Graph, Literal
from rdflib.namespace import RDFS
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class GraphRAG_v2:
    """
    GraphRAG v2.0 - Búsqueda semántica con embeddings
    
    Mejoras sobre v1.5:
    - Búsqueda semántica (no solo léxica)
    - Comprende sinónimos y paráfrasis
    - Ranking por similitud semántica
    - Caché de embeddings
    """
    
    def __init__(self, ttl_path: str, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Inicializa el sistema GraphRAG v2.0
        
        Args:
            ttl_path: Ruta al archivo TTL
            model_name: Modelo de embeddings (recomendado para español)
        """
        print("=" * 70)
        print("🚀 GraphRAG v2.0 - Embeddings Semánticos")
        print("=" * 70)
        
        # Cargar grafo RDF
        print("\n📚 Cargando grafo RDF...")
        self.g = Graph()
        try:
            self.g.parse(ttl_path, format='turtle')
            print(f"   ✅ Grafo cargado: {len(self.g)} tripletas")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            sys.exit(1)
        
        # Cargar modelo de embeddings
        print(f"\n🤖 Cargando modelo de embeddings: {model_name}")
        print("   (Primera vez puede tardar, se descarga ~80-120MB)")
        start_time = time.time()
        self.model = SentenceTransformer(model_name)
        print(f"   ✅ Modelo cargado en {time.time() - start_time:.2f}s")
        
        # Estructuras de datos
        self.entidades = {}
        self.entity_texts = []  # Textos para embeddings
        self.entity_ids = []    # IDs correspondientes
        self.embeddings = None  # Embeddings precalculados
        
        # Índices léxicos (mantener para fallback)
        self.index_palabras = defaultdict(list)
        self.index_propiedades = defaultdict(list)
        
        # Stemming (heredado de v1.5)
        self.stem_rules = [
            (r'es$', ''),
            (r's$', ''),
            (r'ón$', 'on'),
            (r'í$', 'i'),
        ]
        
        # Construir índices
        print("\n🔨 Construyendo índices...")
        self._build_index()
        
        # Computar embeddings
        print("\n🧮 Computando embeddings...")
        self._compute_embeddings()
        
        print("\n" + "=" * 70)
        print("✅ Sistema listo para consultas")
        print("=" * 70)
        print(f"📊 Estadísticas:")
        print(f"   - Entidades: {len(self.entidades)}")
        print(f"   - Términos indexados: {len(self.index_palabras)}")
        print(f"   - Dimensiones embedding: {self.embeddings.shape[1] if self.embeddings is not None else 0}")
        print("=" * 70 + "\n")
    
    def _stem(self, word: str) -> str:
        """Stemming básico en español"""
        word = word.lower()
        for pattern, replacement in self.stem_rules:
            word = re.sub(pattern, replacement, word)
        return word
    
    def _normalize(self, text: str) -> str:
        """Normalización con stemming"""
        if not isinstance(text, str):
            return ""
        text = text.lower()
        text = re.sub(r'[^\w\sáéíóúüñ]', ' ', text)
        replacements = {'á':'a', 'é':'e', 'í':'i', 'ó':'o', 'ú':'u', 'ü':'u', 'ñ':'n'}
        for a, b in replacements.items():
            text = text.replace(a, b)
        words = text.split()
        words = [self._stem(w) for w in words if len(w) > 2]
        return ' '.join(words)
    
    def _index_text(self, text: str, entidad_id: str):
        """Indexa texto para búsqueda léxica"""
        palabras = set(self._normalize(text).split())
        for palabra in palabras:
            if len(palabra) > 2:
                self.index_palabras[palabra].append(entidad_id)
    
    def _build_index(self):
        """Construye índices del grafo"""
        for s, p, o in self.g:
            sujeto_uri = str(s)
            sujeto_id = sujeto_uri.split('#')[-1] if '#' in sujeto_uri else sujeto_uri
            
            # Inicializar entidad
            if sujeto_id not in self.entidades:
                self.entidades[sujeto_id] = {
                    'uri': sujeto_uri,
                    'labels': [],
                    'descriptions': [],
                    'comments': [],
                    'type': None,
                    'propiedades': {},
                    'relaciones': defaultdict(list),
                    'relaciones_inversas': defaultdict(list)
                }
            
            ent = self.entidades[sujeto_id]
            
            # Extraer información
            if p == RDFS.label and isinstance(o, Literal) and (o.language == 'es' or not o.language):
                texto = str(o)
                ent['labels'].append(texto)
                self._index_text(texto, sujeto_id)
            
            elif p == RDFS.comment and isinstance(o, Literal) and (o.language == 'es' or not o.language):
                texto = str(o)
                ent['comments'].append(texto)
                self._index_text(texto, sujeto_id)
            
            elif str(p).endswith('type'):
                tipo = str(o).split('#')[-1] if '#' in str(o) else str(o)
                ent['type'] = tipo
            
            else:
                prop = str(p).split('#')[-1] if '#' in str(p) else str(p)
                if isinstance(o, Literal):
                    valor = str(o)
                    ent['propiedades'][prop] = valor
                    if prop in ['tieneOrden', 'tieneOrdenEvento', 'tieneFecha']:
                        clave_index = f"{prop}:{valor}"
                        self.index_propiedades[clave_index].append(sujeto_id)
                else:
                    obj_id = str(o).split('#')[-1] if '#' in str(o) else str(o)
                    ent['relaciones'][prop].append(obj_id)
        
        # Construir relaciones inversas
        for ent_id, ent_data in self.entidades.items():
            for prop, objetos in ent_data['relaciones'].items():
                for obj_id in objetos:
                    if obj_id in self.entidades:
                        self.entidades[obj_id]['relaciones_inversas'][prop].append(ent_id)
    
    def _build_entity_text(self, ent_id: str) -> str:
        """
        Construye texto representativo de una entidad para embedding
        Combina: labels + comments + tipo + propiedades clave
        """
        ent = self.entidades[ent_id]
        
        parts = []
        
        # Labels (peso alto)
        if ent['labels']:
            parts.extend(ent['labels'])
        
        # Tipo
        if ent['type']:
            parts.append(ent['type'])
        
        # Comments (descripción detallada)
        if ent['comments']:
            parts.extend(ent['comments'])
        
        # Propiedades importantes
        for prop, val in ent['propiedades'].items():
            if prop in ['tieneFecha', 'tieneOrden', 'tieneOrdenEvento']:
                parts.append(f"{prop} {val}")
        
        # Relaciones (mencionar las más importantes)
        for rel, objetos in list(ent['relaciones'].items())[:3]:
            for obj_id in objetos[:2]:  # Máximo 2 objetos por relación
                if obj_id in self.entidades and self.entidades[obj_id]['labels']:
                    obj_name = self.entidades[obj_id]['labels'][0]
                    parts.append(f"{rel} {obj_name}")
        
        return " ".join(parts)
    
    def _compute_embeddings(self):
        """Precomputa embeddings de todas las entidades"""
        print("   Construyendo textos de entidades...")
        
        for ent_id in self.entidades.keys():
            text = self._build_entity_text(ent_id)
            self.entity_texts.append(text)
            self.entity_ids.append(ent_id)
        
        print(f"   Generando {len(self.entity_texts)} embeddings...")
        start_time = time.time()
        
        # Computar en batch para eficiencia
        embeddings = self.model.encode(
            self.entity_texts,
            batch_size=32,
            show_progress_bar=True
        )
        
        # Convertir a numpy si es necesario
        if not isinstance(embeddings, np.ndarray):
            embeddings = np.array(embeddings)
        
        self.embeddings = embeddings
        
        elapsed = time.time() - start_time
        print(f"   ✅ Embeddings generados en {elapsed:.2f}s")
        print(f"   📊 Shape: {self.embeddings.shape}")
    
    def buscar_semantico(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Búsqueda semántica usando embeddings
        
        Args:
            query: Pregunta del usuario
            top_k: Número de resultados a retornar
            
        Returns:
            Lista de (entity_id, score) ordenada por relevancia
        """
        # Generar embedding de la query
        # Versión simple compatible con sentence-transformers 5.2.2
        query_text = str(query)
        
        # Encode simple - retorna numpy array
        embedding_result = self.model.encode([query_text])
        
        # Asegurar formato numpy (1, 384)
        query_embedding = np.asarray(embedding_result)
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Calcular similitud coseno
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Obtener top-k índices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Construir resultados
        results = [
            (self.entity_ids[idx], float(similarities[idx]))
            for idx in top_indices
        ]
        
        return results
    
    def buscar_lexico(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Búsqueda léxica mejorada (fallback de v1.5)
        
        Args:
            query: Pregunta del usuario
            top_k: Número de resultados
            
        Returns:
            Lista de (entity_id, score) ordenada por relevancia
        """
        palabras = self._normalize(query).split()
        if not palabras:
            return []
        
        scores = defaultdict(int)
        
        # Búsqueda en índice de palabras
        for palabra in palabras:
            if palabra in self.index_palabras:
                for ent_id in self.index_palabras[palabra]:
                    scores[ent_id] += 1
        
        # Bonus por coincidencia exacta en labels
        for ent_id, ent in self.entidades.items():
            for label in ent['labels']:
                label_lower = label.lower()
                
                # Bonus grande si label completo contiene la query
                if query.lower() in label_lower:
                    scores[ent_id] += 5
                
                # Bonus por cada palabra que coincida
                for palabra in palabras:
                    if len(palabra) > 3 and palabra in self._normalize(label):
                        scores[ent_id] += 2
        
        # NUEVO: Bonus si el ID de la entidad contiene palabras clave
        for palabra in palabras:
            if len(palabra) > 3:
                for ent_id in self.entidades.keys():
                    if palabra in ent_id.lower():
                        scores[ent_id] += 3  # Bonus importante
        
        # Normalizar scores
        max_score = max(scores.values()) if scores else 1
        results = [
            (ent_id, score / max_score)
            for ent_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        ]
        
        return results
    
    def buscar_hibrido(self, query: str, top_k: int = 10, alpha: float = 0.6) -> List[Tuple[str, float]]:
        """
        Búsqueda híbrida mejorada: combina semántica y léxica con boosting inteligente
        
        Args:
            query: Pregunta
            top_k: Resultados a retornar
            alpha: Peso de búsqueda semántica (default 0.6, más bajo = más peso a léxico)
            
        Returns:
            Lista combinada y reordenada
        """
        # Búsquedas independientes
        sem_results = self.buscar_semantico(query, top_k=top_k*3)  # Más candidatos
        lex_results = self.buscar_lexico(query, top_k=top_k*3)
        
        # Combinar scores
        combined_scores = {}
        
        for ent_id, score in sem_results:
            combined_scores[ent_id] = alpha * score
        
        for ent_id, score in lex_results:
            if ent_id in combined_scores:
                combined_scores[ent_id] += (1 - alpha) * score
            else:
                combined_scores[ent_id] = (1 - alpha) * score
        
        # BOOST MEJORADO: Términos clave exactos
        query_lower = query.lower()
        palabras_clave = self._normalize(query).split()
        
        # Extraer palabras importantes (más de 3 letras, no stopwords)
        stopwords = {'que', 'quien', 'donde', 'cuando', 'como', 'cual', 'son', 'esta', 'hay'}
        palabras_importantes = [p for p in palabras_clave if len(p) > 3 and p not in stopwords]
        
        for ent_id in combined_scores:
            ent = self.entidades[ent_id]
            boost = 0.0
            
            # Boost FUERTE si el label contiene palabra clave exacta
            for label in ent.get('labels', []):
                label_lower = label.lower()
                label_norm = self._normalize(label)
                
                # Cada palabra importante que coincida
                for palabra in palabras_importantes:
                    if palabra in label_norm:
                        boost += 0.5  # Aumentado de 0.1 a 0.5
                    
                    # Boost EXTRA si está en el ID de la entidad
                    if palabra in ent_id.lower():
                        boost += 0.3  # Aumentado de 0.05 a 0.3
            
            # Boost especial para números (días)
            import re
            numeros_query = re.findall(r'\d+', query)
            for num in numeros_query:
                # Buscar "Dia{num}" o "día {num}"
                if f'dia{num}' in ent_id.lower():
                    boost += 0.8  # GRAN boost para días
                for label in ent.get('labels', []):
                    if f'día {num}' in label.lower() or f'dia {num}' in label.lower():
                        boost += 0.8
            
            combined_scores[ent_id] += boost
        
        # Ordenar y retornar top-k
        results = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        return results
    
    def responder_que_eventos(self, pregunta: str, entidad_principal: str) -> Optional[str]:
        """Plantilla mejorada para preguntas sobre eventos de un día"""
        # Detectar número de día de múltiples formas
        dias_map = {
            '1': ['Dia1_SabadoPreparacion', 'dia1', 'día 1', 'dia 1'],
            '2': ['Dia2_DomingoPartida', 'dia2', 'día 2', 'dia 2'],
            '3': ['Dia3_LunesAscenso', 'dia3', 'día 3', 'dia 3'],
            '4': ['Dia4_MartesDescensoYLomada', 'dia4', 'día 4', 'dia 4'],
            '5': ['Dia5_MiercolesAlba', 'dia5', 'día 5', 'dia 5'],
        }
        
        p = pregunta.lower()
        dia_num = None
        dia_id = None
        
        # Buscar en la pregunta
        for num, variantes in dias_map.items():
            dia_id_candidato = variantes[0]
            for variante in variantes[1:]:
                if variante in p:
                    dia_num = num
                    dia_id = dia_id_candidato
                    break
            if dia_id:
                break
        
        # Si no encontró en la pregunta, ver si la entidad principal es un día
        if not dia_id:
            for num, variantes in dias_map.items():
                if variantes[0] == entidad_principal or entidad_principal in variantes:
                    dia_num = num
                    dia_id = variantes[0]
                    break
        
        # Si encontró el día, buscar sus eventos
        if dia_id and dia_id in self.entidades:
            dia_ent = self.entidades[dia_id]
            eventos_def = dia_ent.get('relaciones', {}).get('defineMarcoTemporal', [])
            
            if eventos_def:
                # Recopilar eventos con su orden
                eventos_lista = []
                for ev_id in eventos_def:
                    if ev_id in self.entidades:
                        ev_ent = self.entidades[ev_id]
                        nombre = ev_ent['labels'][0] if ev_ent['labels'] else ev_id
                        orden = ev_ent['propiedades'].get('tieneOrdenEvento', 999)
                        try:
                            orden_num = int(orden)
                        except:
                            orden_num = 999
                        eventos_lista.append((orden_num, nombre))
                
                if eventos_lista:
                    # Ordenar por número de orden
                    eventos_lista.sort(key=lambda x: x[0])
                    
                    dia_nombre = dia_ent['labels'][0] if dia_ent['labels'] else f"Día {dia_num}"
                    
                    # Formatear respuesta
                    eventos_texto = '\n'.join([
                        f"   • **{nombre}** (evento #{orden})" 
                        for orden, nombre in eventos_lista
                    ])
                    
                    return f"📅 **{dia_nombre}** incluye estos eventos:\n\n{eventos_texto}"
        
        return None
    
    def identificar_intencion(self, pregunta: str) -> str:
        """Detecta tipo de pregunta (heredado de v1.5 con mejoras)"""
        p = pregunta.lower()
        
        # Detección específica de "día X"
        if any(x in p for x in ['día 1', 'día 2', 'día 3', 'día 4', 'día 5', 
                                 'dia 1', 'dia 2', 'dia 3', 'dia 4', 'dia 5',
                                 'dia1', 'dia2', 'dia3', 'dia4', 'dia5']):
            if any(w in p for w in ['qué', 'que', 'cuales', 'cuáles', 'eventos', 'actividades']):
                return 'que_eventos'
        
        if any(w in p for w in ['dónde', 'donde', 'lugar', 'ubicación', 'sitio', 'está', 'esta']):
            return 'donde'
        elif any(w in p for w in ['cuándo', 'cuando', 'fecha', 'día', 'hora']):
            return 'cuando'
        elif any(w in p for w in ['quién', 'quien', 'quiénes', 'quienes', 'participa', 'realiza']):
            return 'quien'
        elif any(w in p for w in ['qué', 'que', 'cómo', 'como', 'cuál', 'cual']):
            if 'evento' in p or 'actividad' in p or 'hito' in p:
                return 'que_eventos'
            elif 'danza' in p or 'baile' in p:
                return 'que_danzas'
            else:
                return 'que'
        elif 'cuántos' in p or 'cuantos' in p or 'número' in p or 'cantidad' in p:
            return 'cuantos'
        else:
            return 'general'
    
    def responder_donde(self, pregunta: str, entidad_principal: str) -> Optional[str]:
        """Plantilla para preguntas de ubicación"""
        ent = self.entidades.get(entidad_principal, {})
        if not ent:
            return None
        
        nombre = ent['labels'][0] if ent['labels'] else entidad_principal
        
        # Buscar ocurreEnLugar
        lugares = ent['relaciones'].get('ocurreEnLugar', [])
        if lugares:
            lugar_ids = lugares
            lugar_nombres = []
            for lid in lugar_ids:
                if lid in self.entidades and self.entidades[lid]['labels']:
                    lugar_nombres.append(self.entidades[lid]['labels'][0])
            
            if len(lugar_nombres) == 1:
                return f"📍 **{nombre}** ocurre en **{lugar_nombres[0]}**."
            else:
                return f"📍 **{nombre}** ocurre en: {', '.join(lugar_nombres)}."
        
        # Buscar estaEn
        esta_en = ent['relaciones'].get('estaEn', [])
        if esta_en:
            lugar_id = esta_en[0]
            if lugar_id in self.entidades:
                lugar_ent = self.entidades[lugar_id]
                lugar_nombre = lugar_ent['labels'][0] if lugar_ent['labels'] else lugar_id
                return f"📍 **{nombre}** está en **{lugar_nombre}**."
        
        return None
    
    def responder_cuando(self, pregunta: str, entidad_principal: str) -> Optional[str]:
        """Plantilla para preguntas temporales"""
        ent = self.entidades.get(entidad_principal, {})
        if not ent:
            return None
        
        nombre = ent['labels'][0] if ent['labels'] else entidad_principal
        props = ent['propiedades']
        
        fecha = props.get('tieneFecha')
        orden = props.get('tieneOrden')
        orden_evento = props.get('tieneOrdenEvento')
        
        respuestas = []
        if fecha:
            respuestas.append(f"📅 **{nombre}** ocurre el {fecha}.")
        if orden:
            respuestas.append(f"📋 Es el día {orden} de la festividad.")
        if orden_evento:
            respuestas.append(f"🔢 Es el evento #{orden_evento} en su día.")
        
        return ' '.join(respuestas) if respuestas else None
    
    def responder_quien(self, pregunta: str, entidad_principal: str) -> Optional[str]:
        """Plantilla para preguntas sobre participantes"""
        ent = self.entidades.get(entidad_principal, {})
        if not ent:
            return None
        
        nombre = ent['labels'][0] if ent['labels'] else entidad_principal
        
        # Buscar realizadoPor (quien lo hace)
        realizadores = ent['relaciones'].get('realizadoPor', [])
        if realizadores:
            parts = []
            for pid in realizadores:
                pent = self.entidades.get(pid, {})
                pname = pent['labels'][0] if pent['labels'] else pid
                parts.append(pname)
            
            if len(parts) == 1:
                return f"👥 **{nombre}** es realizado por **{parts[0]}**."
            else:
                return f"👥 **{nombre}** es realizado por: {', '.join(parts)}."
        
        # Buscar realizadoPor inverso (qué hace esta entidad)
        realiza = ent.get('relaciones_inversas', {}).get('realizadoPor', [])
        if realiza:
            eventos = []
            for eid in realiza[:5]:
                eent = self.entidades.get(eid, {})
                ename = eent['labels'][0] if eent['labels'] else eid
                eventos.append(ename)
            
            if len(eventos) == 1:
                return f"👥 **{nombre}** realiza: **{eventos[0]}**."
            else:
                return f"👥 **{nombre}** realiza: {', '.join(eventos)}."
        
        # Buscar participaEn inverso
        participantes = ent.get('relaciones_inversas', {}).get('participaEn', [])
        if participantes:
            parts = []
            for pid in participantes[:3]:
                pent = self.entidades.get(pid, {})
                pname = pent['labels'][0] if pent['labels'] else pid
                parts.append(pname)
            
            return f"👥 **{nombre}** tiene la participación de: {', '.join(parts)}."
        
        return None
    
    def responder(self, pregunta: str, modo: str = "hibrido", verbose: bool = False) -> str:
        """
        Responde una pregunta usando búsqueda semántica + plantillas
        
        Args:
            pregunta: Pregunta del usuario
            modo: 'semantico', 'lexico', o 'hibrido' (recomendado)
            verbose: Mostrar información de debug
            
        Returns:
            Respuesta generada
        """
        if verbose:
            print(f"\n🔍 Procesando: '{pregunta}'")
            print(f"   Modo: {modo}")
        
        # 1. Identificar tipo de pregunta PRIMERO
        intencion = self.identificar_intencion(pregunta)
        
        if verbose:
            print(f"   🎯 Intención detectada: {intencion}")
        
        # 2. Búsqueda según modo
        if modo == "semantico":
            resultados = self.buscar_semantico(pregunta, top_k=10)
        elif modo == "lexico":
            resultados = self.buscar_lexico(pregunta, top_k=10)
        else:  # hibrido
            resultados = self.buscar_hibrido(pregunta, top_k=10)
        
        if verbose:
            print(f"\n   📊 Top resultados:")
            for i, (ent_id, score) in enumerate(resultados[:5], 1):
                ent = self.entidades[ent_id]
                nombre = ent['labels'][0] if ent['labels'] else ent_id
                print(f"      {i}. {nombre} (score: {score:.3f})")
        
        if not resultados:
            return "Lo siento, no encontré información relacionada con tu pregunta."
        
        # 3. Seleccionar mejor entidad según intención
        mejor_id = None
        mejor_score = 0
        
        # Palabras clave de la query (sin stopwords)
        palabras_query = self._normalize(pregunta).split()
        stopwords = {'quien', 'quién', 'que', 'qué', 'donde', 'dónde', 'cuando', 'cuándo',
                     'realiza', 'hace', 'ejecuta', 'participa', 'hay', 'esta', 'está',
                     'son', 'como', 'cómo', 'cual', 'cuál', 'eventos', 'día', 'dia'}
        palabras_importantes = [p for p in palabras_query if p not in stopwords and len(p) > 3]
        
        # Filtrar por tipo según intención
        if intencion == 'que_eventos':
            # Preferir entidades que contengan "Dia" o sean EventoRitual
            for ent_id, score in resultados[:5]:
                ent = self.entidades[ent_id]
                es_dia = 'dia' in ent_id.lower() or any('día' in l.lower() for l in ent.get('labels', []))
                
                if es_dia:
                    mejor_id = ent_id
                    mejor_score = score
                    break  # Tomar el primero que sea un día
        
        elif intencion == 'quien':
            # Para "quien realiza X", buscar X específicamente en top-5
            # Priorizar entidad cuyo NOMBRE PRINCIPAL sea X, no solo menciones
            
            candidatos = []
            for ent_id, score in resultados[:5]:
                ent = self.entidades[ent_id]
                puntuacion = 0
                
                # MÁXIMA prioridad: palabra clave en el ID de la entidad
                for palabra in palabras_importantes:
                    if palabra in ent_id.lower():
                        puntuacion += 10
                
                # ALTA prioridad: palabra clave en el PRIMER label (nombre principal)
                if ent.get('labels'):
                    primer_label = ent['labels'][0].lower()
                    for palabra in palabras_importantes:
                        # Coincidencia como palabra completa en el nombre
                        if palabra in self._normalize(primer_label):
                            # Bonus extra si está al inicio del nombre
                            if primer_label.startswith(palabra):
                                puntuacion += 8
                            else:
                                puntuacion += 5
                
                # Bonus si tiene relación realizadoPor
                if ent.get('relaciones', {}).get('realizadoPor'):
                    puntuacion += 3
                
                # Penalización si es un "Día" (probablemente marco temporal, no el evento)
                if 'dia' in ent_id.lower() and ent_id.lower().startswith('dia'):
                    puntuacion -= 5
                
                if puntuacion > 0:
                    candidatos.append((ent_id, score, puntuacion))
            
            # Ordenar por puntuación (más puntos = mejor match)
            if candidatos:
                candidatos.sort(key=lambda x: x[2], reverse=True)
                mejor_id = candidatos[0][0]
                mejor_score = candidatos[0][1]
        
        # Si no se encontró una entidad específica, usar la primera
        if not mejor_id:
            mejor_id, mejor_score = resultados[0]
        
        if verbose:
            ent_selec = self.entidades[mejor_id]
            nombre_selec = ent_selec['labels'][0] if ent_selec['labels'] else mejor_id
            print(f"\n   🎯 Entidad seleccionada: {nombre_selec} (score: {mejor_score:.3f})")
        
        # 4. Aplicar plantilla según intención
        respuesta = None
        if intencion == 'donde':
            respuesta = self.responder_donde(pregunta, mejor_id)
        elif intencion == 'cuando':
            respuesta = self.responder_cuando(pregunta, mejor_id)
        elif intencion == 'quien':
            respuesta = self.responder_quien(pregunta, mejor_id)
        elif intencion == 'que_eventos':
            respuesta = self.responder_que_eventos(pregunta, mejor_id)
        
        # 5. Si hay respuesta de plantilla, usarla
        if respuesta:
            return respuesta
        
        # 6. Fallback: respuesta genérica con contexto
        ent = self.entidades.get(mejor_id, {})
        nombre = ent['labels'][0] if ent['labels'] else mejor_id
        
        lines = [f"**{nombre}**"]
        
        if ent['comments']:
            lines.append(f"\n{ent['comments'][0]}")
        
        # Añadir propiedades clave
        props = []
        if 'tieneFecha' in ent['propiedades']:
            props.append(f"📅 Fecha: {ent['propiedades']['tieneFecha']}")
        if 'tieneOrden' in ent['propiedades']:
            props.append(f"📋 Orden día: {ent['propiedades']['tieneOrden']}")
        if 'tieneOrdenEvento' in ent['propiedades']:
            props.append(f"🔢 Orden evento: {ent['propiedades']['tieneOrdenEvento']}")
        
        if props:
            lines.append("\n" + " | ".join(props))
        
        # Mencionar otras entidades relevantes
        if len(resultados) > 1 and mejor_score > 0.3:
            otros = []
            for eid, s in resultados[1:3]:
                if s > 0.2 and eid != mejor_id:
                    e = self.entidades.get(eid, {})
                    ename = e['labels'][0] if e['labels'] else eid
                    otros.append(f"**{ename}**")
            if otros:
                lines.append(f"\n\n💡 También relacionado: {', '.join(otros)}")
        
        return "\n".join(lines)
    
    def guardar_cache(self, filepath: str = "cache_embeddings_v2.pkl"):
        """Guarda embeddings en caché para carga rápida"""
        cache_data = {
            'embeddings': self.embeddings,
            'entity_ids': self.entity_ids,
            'entity_texts': self.entity_texts,
            'entidades': self.entidades,
            'model_name': self.model.get_sentence_embedding_dimension()
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(cache_data, f)
        
        print(f"💾 Caché guardado en: {filepath}")
    
    def cargar_cache(self, filepath: str = "cache_embeddings_v2.pkl") -> bool:
        """Carga embeddings desde caché"""
        try:
            with open(filepath, 'rb') as f:
                cache_data = pickle.load(f)
            
            self.embeddings = cache_data['embeddings']
            self.entity_ids = cache_data['entity_ids']
            self.entity_texts = cache_data['entity_texts']
            self.entidades = cache_data['entidades']
            
            print(f"✅ Caché cargado desde: {filepath}")
            return True
        except FileNotFoundError:
            print(f"⚠️  No se encontró caché en: {filepath}")
            return False


def benchmark(rag: GraphRAG_v2, queries: List[str]):
    """
    Benchmark de rendimiento
    
    Args:
        rag: Instancia de GraphRAG_v2
        queries: Lista de queries de prueba
    """
    print("\n" + "=" * 70)
    print("📊 BENCHMARK DE RENDIMIENTO")
    print("=" * 70)
    
    modos = ["semantico", "lexico", "hibrido"]
    
    for modo in modos:
        print(f"\n🔬 Modo: {modo.upper()}")
        tiempos = []
        
        for query in queries:
            start = time.time()
            respuesta = rag.responder(query, modo=modo, verbose=False)
            elapsed = time.time() - start
            tiempos.append(elapsed)
            
            print(f"   • {query[:50]}... → {elapsed*1000:.1f}ms")
        
        avg_time = np.mean(tiempos)
        std_time = np.std(tiempos)
        print(f"\n   📈 Promedio: {avg_time*1000:.1f}ms (±{std_time*1000:.1f}ms)")
    
    print("\n" + "=" * 70)


def main():
    """Función principal de demostración"""
    print("\n" + "=" * 70)
    print("🌟 GraphRAG v2.0 - Demo Interactivo")
    print("=" * 70)
    
    # Configuración
    ttl_file = "/mnt/user-data/uploads/qoyllurity.ttl"
    
    if not Path(ttl_file).exists():
        print(f"❌ No se encontró: {ttl_file}")
        ttl_file = input("Ingresa ruta al archivo TTL: ").strip()
    
    # Inicializar sistema
    rag = GraphRAG_v2(ttl_file)
    
    # Queries de prueba
    test_queries = [
        "¿Qué es Qoyllur Rit'i?",
        "¿Dónde está el santuario?",
        "¿Qué hacen los ukukus?",
        "¿Cuándo es la bajada del glaciar?",
        "¿Quién realiza la lomada?",
    ]
    
    # Ejecutar benchmark
    print("\n¿Ejecutar benchmark? (s/n): ", end="")
    if input().lower() == 's':
        benchmark(rag, test_queries)
    
    # Modo interactivo
    print("\n" + "=" * 70)
    print("💬 MODO INTERACTIVO")
    print("=" * 70)
    print("Comandos especiales:")
    print("  - 'benchmark' → Ejecutar benchmark")
    print("  - 'cache' → Guardar caché de embeddings")
    print("  - 'stats' → Mostrar estadísticas")
    print("  - 'salir' → Terminar")
    print("=" * 70 + "\n")
    
    while True:
        try:
            query = input("❓ Tu pregunta: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['salir', 'exit', 'quit']:
                print("\n👋 ¡Hasta luego!")
                break
            
            if query.lower() == 'benchmark':
                benchmark(rag, test_queries)
                continue
            
            if query.lower() == 'cache':
                rag.guardar_cache()
                continue
            
            if query.lower() == 'stats':
                print(f"\n📊 Estadísticas:")
                print(f"   Entidades: {len(rag.entidades)}")
                print(f"   Embeddings: {rag.embeddings.shape}")
                print(f"   Dimensiones: {rag.embeddings.shape[1]}")
                print(f"   Términos indexados: {len(rag.index_palabras)}\n")
                continue
            
            # Responder con modo híbrido y verbose
            print()
            respuesta = rag.responder(query, modo="hibrido", verbose=True)
            print(f"\n💬 Respuesta:\n{respuesta}\n")
            print("-" * 70)
        
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
