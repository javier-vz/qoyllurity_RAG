#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GraphRAG v4.0 API - Versión Modular con Configuración Externa
==============================================================

Versión mejorada que usa:
- Configuración externa (config_graphrag.py)
- Prompts modulares
- Mapeos de relaciones actualizados
- Soporte completo para lugares sagrados
- EXPANSIÓN AUTOMÁTICA DE PARTES (tieneParte)
"""

import time
from typing import List, Dict, Tuple
from groq import Groq

# Importar GraphRAG v2.0 como base
from graphrag_v2 import GraphRAG_v2

# Importar configuración
from config_graphrag import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    mapear_relacion,
    Config
)


class GraphRAG_v4_API(GraphRAG_v2):
    """
    GraphRAG v4.0 con Groq API
    
    Arquitectura híbrida:
    - v2.0: Búsqueda local (embeddings + coincidencias léxicas)
    - API: Generación de lenguaje natural con Groq
    
    Características:
    - Prompts externos configurables
    - Mapeos de relaciones actualizados
    - Soporte para lugares sagrados y jerarquía geográfica
    - Expansión automática de objetos compuestos (tieneParte)
    """
    
    def __init__(
        self,
        ttl_path: str,
        groq_api_key: str,
        modelo: str = None,
        verbose: bool = False
    ):
        """
        Inicializa GraphRAG v4.0 API
        
        Args:
            ttl_path: Ruta al archivo TTL
            groq_api_key: API key de Groq
            modelo: Modelo a usar (por defecto usa Config.MODELO_GROQ)
            verbose: Mostrar mensajes de debug
        """
        # Inicializar GraphRAG v2.0 (herencia) - sin verbose
        super().__init__(ttl_path)
        
        # Guardar verbose para uso posterior
        self.verbose_mode = verbose
        
        # Configurar Groq client
        self.client = Groq(api_key=groq_api_key)
        self.groq_model = modelo or Config.MODELO_GROQ
        
        if verbose:
            print("\n" + "=" * 70)
            print("✅ Groq API configurada")
            print(f"   Modelo: {self.groq_model}")
            print(f"   Límite: 30 requests/min (gratis)")
            print("=" * 70)
            print()
    
    def expandir_partes(self, entidad: dict, max_partes: int = 10) -> str:
        """
        Expande las partes de un objeto compuesto
        
        Args:
            entidad: Diccionario de entidad
            max_partes: Máximo número de partes a incluir
            
        Returns:
            String con descripción de partes o vacío
        """
        relaciones = entidad.get('relaciones', {})
        
        if 'tieneParte' not in relaciones:
            return ""
        
        partes_info = []
        for parte_id in relaciones['tieneParte'][:max_partes]:
            parte = self.entidades.get(parte_id)
            if not parte:
                continue
            
            # Extraer nombre de la parte
            parte_labels = parte.get('labels', [])
            nombre = parte_labels[0] if parte_labels else parte_id
            
            # Extraer descripción de la parte
            parte_comments = parte.get('comments', [])
            desc = parte_comments[0][:100] if parte_comments else ""
            
            # Extraer material si existe
            material = None
            parte_props = parte.get('propiedades', {})
            if 'hechoDeRitual' in parte_props:
                # hechoDeRitual es una propiedad datatype (literal)
                material = parte_props['hechoDeRitual']
            
            # Construir descripción de parte
            if material and desc:
                partes_info.append(f"{nombre} ({desc}, hecho de {material})")
            elif desc:
                partes_info.append(f"{nombre} ({desc})")
            elif material:
                partes_info.append(f"{nombre} (hecho de {material})")
            else:
                partes_info.append(nombre)
        
        if partes_info:
            return f"\n  Partes: {'; '.join(partes_info)}"
        return ""
    
    def construir_contexto(
        self,
        entidades_ids: List[str],
        max_chars: int = None
    ) -> str:
        """
        Construye contexto para la API usando configuración externa
        CON EXPANSIÓN AUTOMÁTICA DE PARTES
        
        Args:
            entidades_ids: IDs de entidades relevantes
            max_chars: Límite de caracteres (usa Config si None)
            
        Returns:
            Contexto formateado en lenguaje natural
        """
        max_chars = max_chars or Config.MAX_CHARS_CONTEXTO
        partes = []
        chars_usados = 0
        
        # Limitar a TOP_K_CONTEXTO entidades
        for ent_id in entidades_ids[:Config.TOP_K_CONTEXTO]:
            if chars_usados > max_chars:
                break
            
            ent = self.entidades.get(ent_id, {})
            if not ent:
                continue
            
            # Extraer nombre con fallback seguro
            labels = ent.get('labels', [])
            nombre = labels[0] if labels else ent_id
            
            # Extraer descripción con fallback seguro
            comments = ent.get('comments', [])
            desc = comments[0] if comments else ""
            
            # Formatear info básica
            info = f"• {nombre}"
            if desc:
                # Limitar descripción según Config
                info += f"\n  {desc[:Config.MAX_CHARS_DESC]}"
            
            # Extraer relaciones en lenguaje natural
            relaciones = ent.get('relaciones', {})
            rels_naturales = []
            
            # Limitar según Config
            for rel_tipo, objetos in list(relaciones.items())[:Config.MAX_RELACIONES]:
                # Saltar 'tieneParte' porque se maneja con expandir_partes()
                if rel_tipo == 'tieneParte':
                    continue
                    
                for obj_id in objetos[:Config.MAX_OBJETOS_POR_REL]:
                    obj_ent = self.entidades.get(obj_id, {})
                    if obj_ent:
                        obj_labels = obj_ent.get('labels', [])
                        obj_nombre = obj_labels[0] if obj_labels else obj_id
                        
                        # Usar función de mapeo de config_graphrag.py
                        rel_natural = mapear_relacion(rel_tipo, obj_nombre)
                        rels_naturales.append(rel_natural)
            
            # Agregar relaciones al info
            if rels_naturales:
                # Limitar a 3 relaciones mostradas
                info += f"\n  {'; '.join(rels_naturales[:3])}"
            
            # === EXPANSIÓN AUTOMÁTICA DE PARTES ===
            partes_expansion = self.expandir_partes(ent)
            if partes_expansion:
                info += partes_expansion
            
            # Verificar si cabe en el límite
            parte_len = len(info)
            if chars_usados + parte_len < max_chars:
                partes.append(info)
                chars_usados += parte_len
        
        # Retornar contexto unido o mensaje de no encontrado
        if not partes:
            return "No se encontró información relevante en el grafo de conocimiento."
        
        return "\n\n".join(partes)
    
    def responder_con_api(
        self,
        pregunta: str,
        modo: str = "hibrido",
        verbose: bool = False
    ) -> str:
        """
        Responde usando búsqueda local + Groq API
        
        Args:
            pregunta: Pregunta del usuario
            modo: Modo de búsqueda ('semantico', 'lexico', 'hibrido')
            verbose: Mostrar info de debug
            
        Returns:
            Respuesta generada por el LLM
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"🔍 Procesando: '{pregunta}'")
            print(f"{'='*70}")
        
        # ====================================================================
        # FASE 1: BÚSQUEDA LOCAL (GraphRAG v2.0)
        # ====================================================================
        if verbose:
            print("\n📊 Fase 1: Búsqueda local (v2.0)")
        
        start_busqueda = time.time()
        
        # Seleccionar modo de búsqueda
        if modo == "semantico":
            resultados = self.buscar_semantico(pregunta, top_k=Config.TOP_K_BUSQUEDA)
        elif modo == "lexico":
            resultados = self.buscar_lexico(pregunta, top_k=Config.TOP_K_BUSQUEDA)
        else:
            resultados = self.buscar_hibrido(pregunta, top_k=Config.TOP_K_BUSQUEDA)
        
        t_busqueda = time.time() - start_busqueda
        
        if not resultados:
            return "No encontré información relacionada en el grafo."
        
        # ====================================================================
        # BOOST 1: Priorizar instancias específicas sobre clases generales
        # ====================================================================
        if any(palabra in pregunta.lower() for palabra in ['vestimenta', 'traje', 'ropa', 'viste', 'visten', 'porta']):
            # Buscar TrajeUkumari
            traje_id = None
            for ent_id, ent in self.entidades.items():
                if 'Traje de Ukumari' in ent.get('labels', []):
                    traje_id = ent_id
                    break
            
            # Si no está en top 2, forzarlo
            if traje_id and traje_id not in [r[0] for r in resultados[:2]]:
                resultados.insert(0, (traje_id, 0.98))  # Score alto
                if verbose:
                    print(f"   🎯 Boosted: TrajeUkumari insertado en posición #1")
        
        # ====================================================================
        # BOOST 2: Expandir con ubicaciones relacionadas (estaEn)
        # ====================================================================
        if any(palabra in pregunta.lower() for palabra in ['dónde', 'donde', 'ubicado', 'ubicación', 'está', 'esta']):
            # Para cada entidad en resultados, agregar su ubicación si no está ya
            entidades_con_ubicacion = []
            for ent_id, score in resultados[:5]:
                ent = self.entidades.get(ent_id, {})
                relaciones = ent.get('relaciones', {})
                
                # Si tiene estaEn, agregar esa entidad también
                if 'estaEn' in relaciones:
                    for ubicacion_id in relaciones['estaEn']:
                        if ubicacion_id not in [r[0] for r in resultados[:5]]:
                            entidades_con_ubicacion.append((ubicacion_id, score * 0.9))
            
            # Insertar ubicaciones después de las primeras 2
            if entidades_con_ubicacion:
                for i, (ent_id, score) in enumerate(entidades_con_ubicacion[:2], 2):
                    resultados.insert(i, (ent_id, score))
                if verbose:
                    print(f"   🎯 Boosted: {len(entidades_con_ubicacion[:2])} ubicaciones expandidas")
        
        # Extraer IDs de las top entidades
        entidades_ids = [ent_id for ent_id, _ in resultados[:Config.TOP_K_CONTEXTO]]
        
        if verbose:
            print(f"   ✅ {len(resultados)} entidades en {t_busqueda*1000:.0f}ms")
            for i, (ent_id, score) in enumerate(resultados[:3], 1):
                ent = self.entidades[ent_id]
                nombre = ent['labels'][0] if ent['labels'] else ent_id
                print(f"      {i}. {nombre} ({score:.3f})")
        
        # ====================================================================
        # FASE 2: CONSTRUCCIÓN DE CONTEXTO (con expansión de partes)
        # ====================================================================
        if verbose:
            print("\n🏗️  Fase 2: Construcción de contexto")
        
        contexto = self.construir_contexto(entidades_ids)
        
        if verbose:
            print(f"   ✅ Contexto: {len(contexto)} chars")
            # Verificar si se expandieron partes
            if "Partes:" in contexto:
                print(f"   🔧 Partes expandidas automáticamente")
        
        # ====================================================================
        # FASE 3: GENERACIÓN CON GROQ API
        # ====================================================================
        if verbose:
            print("\n🌐 Fase 3: Generación con Groq API")
        
        start_api = time.time()
        
        try:
            # Usar prompts de config_graphrag.py
            response = self.client.chat.completions.create(
                model=self.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": USER_PROMPT_TEMPLATE.format(
                            contexto=contexto,
                            pregunta=pregunta
                        )
                    }
                ],
                max_tokens=Config.MAX_TOKENS,
                temperature=Config.TEMPERATURE,
                top_p=Config.TOP_P,
                reasoning_effort=Config.REASONING_EFFORT,
                include_reasoning=False
            )
            
            respuesta = (response.choices[0].message.content or "").strip()
            if not respuesta:
                raise RuntimeError("Groq devolvió una respuesta vacía. Intenta nuevamente.")
            t_api = time.time() - start_api
            
            # ================================================================
            # VALIDACIÓN: Detectar frases prohibidas
            # ================================================================
            advertencia = False
            for frase in Config.FRASES_PROHIBIDAS:
                if frase.lower() in respuesta.lower():
                    advertencia = True
                    if verbose:
                        print(f"   ⚠️  ADVERTENCIA: Posible interpretación detectada: '{frase}'")
            
            if advertencia and verbose:
                print("   ⚠️  La respuesta puede contener interpretaciones no basadas en el contexto")
            
            if verbose:
                print(f"   ✅ Generado en {t_api:.2f}s")
                print(f"   📝 {len(respuesta)} caracteres")
            
            return respuesta
        
        except Exception as e:
            # Mantener el error como excepción para que Streamlit pueda advertir
            # al usuario y no lo almacene como si fuera una respuesta del grafo.
            if getattr(e, "status_code", None) == 404:
                raise RuntimeError(
                    f"Groq no encontró el modelo '{self.groq_model}'. "
                    "Revisa el modelo disponible para tu cuenta en GroqCloud."
                ) from e
            raise RuntimeError(f"La consulta a Groq falló: {e}") from e
    
    def responder(
        self,
        pregunta: str,
        use_api: bool = True,
        modo: str = "hibrido",
        verbose: bool = False
    ) -> str:
        """
        Responde a una pregunta (wrapper dual mode)
        
        Args:
            pregunta: Pregunta del usuario
            use_api: True para usar API, False para v2.0 puro
            modo: Modo de búsqueda
            verbose: Mostrar info de debug
            
        Returns:
            Respuesta generada
        """
        if use_api:
            return self.responder_con_api(pregunta, modo, verbose)
        else:
            # Usar v2.0 puro (sin API)
            return super().responder(pregunta, modo, verbose)
