"""Recuperación combinada: texto, similitud de caracteres, y relaciones RDF.

Un modelo semántico adicional puede habilitarse explícitamente; la aplicación
funciona sin descargar modelos ni acceder a servicios externos.
"""
from __future__ import annotations
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from core.graph import HeritageGraph, normalize
from core.spanish import about_question, where_question
from config_graphrag import SEMANTIC_MODEL

FOLLOWUP = {'alli', 'ahi', 'ese', 'esa', 'esos', 'esas', 'ellos', 'su', 'sus', 'aquello'}


class Retriever:
    def __init__(self, store: HeritageGraph, use_semantic: bool = False):
        self.store = store
        self.ids = list(store.entities)
        self.docs = [self._document(eid) for eid in self.ids]
        self.word = TfidfVectorizer(strip_accents='unicode', lowercase=True,
                                     ngram_range=(1, 2), sublinear_tf=True)
        self.char = TfidfVectorizer(strip_accents='unicode', lowercase=True,
                                     analyzer='char_wb', ngram_range=(3, 5))
        self.word_vectors = self.word.fit_transform(self.docs)
        self.char_vectors = self.char.fit_transform(self.docs)
        self.semantic_model = None
        self.semantic_vectors = None
        if use_semantic:
            from sentence_transformers import SentenceTransformer
            self.semantic_model = SentenceTransformer(SEMANTIC_MODEL)
            self.semantic_vectors = self.semantic_model.encode(self.docs, normalize_embeddings=True)

    def _document(self, eid):
        e = self.store.entities[eid]
        parts = [e.label] * 4 + [e.eid] * 2 + e.kinds + [e.description]
        parts += [f['predicate_label'] + ' ' + f['value'] for f in e.literals]
        parts += [f['predicate_label'] + ' ' + f['value'] for f in e.outgoing]
        parts += [f['predicate_label'] + ' ' + f['subject_label'] for f in e.incoming]
        return ' '.join(parts)

    def search(self, query: str, top_k: int = 6, previous_eid: str | None = None) -> list[dict]:
        query = query.strip()
        if not query:
            return []
        qn = normalize(query)
        scores = (0.55 * (self.word_vectors @ self.word.transform([query]).T).toarray().ravel()
                  + 0.45 * (self.char_vectors @ self.char.transform([query]).T).toarray().ravel())
        if self.semantic_model is not None:
            emb = self.semantic_model.encode([query], normalize_embeddings=True)[0]
            similarities = np.clip(np.asarray(self.semantic_vectors) @ emb, 0, 1)
            scores = scores * 0.7 + similarities * 0.3
        words = set(qn.split())
        # Sinónimos de navegación (no añaden conocimiento factual).
        # Seleccionamos el individuo central cuando la pregunta es general.
        focus = None
        if 'qoyllur' in words and (('que' in words and 'es' in words)
                                  or 'festividad' in words or 'peregrinacion' in words):
            focus = 'FestividadQoylluriti'
        elif {'ukukus','ukukus','ukuku','ukumaris','ukumari'} & words:
            if {'vestimenta','traje','visten','ropa'} & words:
                focus = 'TrajeUkumari'
            elif {'danza','bailan'} & words:
                focus = 'DanzaUkumari'
            elif 'celda' not in words and 'misa' not in words:
                focus = 'Ukumaris_Paucartambo_2025'
        elif 'lomada' in words and {'dura','duracion','cuanto','horas','que'} & words:
            focus = 'Lomada_2025'
        if focus in self.ids:
            scores[self.ids.index(focus)] += 0.9
        anchor = (previous_eid in self.store.entities and
                  (bool(words & FOLLOWUP) or ('y' in words and len(words) <= 7)))
        for i, eid in enumerate(self.ids):
            e = self.store.entities[eid]
            label = normalize(e.label)
            slug = normalize(e.eid)
            if label and len(label) > 3 and label in qn:
                scores[i] += 0.65
            elif slug and len(slug) > 3 and slug in qn:
                scores[i] += 0.55
            if anchor and eid == previous_eid:
                scores[i] += 0.50
            elif anchor and eid in self.store.related_ids(previous_eid):
                scores[i] += 0.07
        order = np.argsort(-scores, kind='stable')
        results = []
        for idx in order:
            score = float(scores[idx])
            if score < 0.055:
                continue
            e = self.store.entities[self.ids[int(idx)]]
            results.append({'id': e.eid, 'label': e.label, 'score': round(score, 4)})
            if len(results) >= top_k:
                break
        return results

    def suggestions(self, eid: str, count: int = 3) -> list[str]:
        ent = self.store.entities.get(eid)
        if not ent:
            return []
        suggestions = []
        for linked in self.store.related_ids(eid):
            other = self.store.entities[linked]
            suggestions.append(about_question(other.label, other.kinds))
            if len(suggestions) >= count:
                break
        if len(suggestions) < count and ent.description:
            suggestions.append(where_question(ent.label, ent.kinds))
        return list(dict.fromkeys(suggestions))[:count]
