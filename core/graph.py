"""Acceso de solo lectura al grafo de Qoyllur Rit'i y fichas estructuradas.

El RDF/Turtle original es la única fuente de hechos para la aplicación.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote
import re
import unicodedata
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS, OWL


def local(uri) -> str:
    s = str(uri)
    return unquote(s.rsplit('#', 1)[-1].rsplit('/', 1)[-1])


def humanize(raw: str) -> str:
    text = re.sub(r'(?<=[a-záéíóúñ])(?=[A-ZÁÉÍÓÚÑ])', ' ', raw)
    text = re.sub(r'[_-]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def normalize(raw: str) -> str:
    raw = unicodedata.normalize('NFKD', str(raw).casefold())
    raw = ''.join(ch for ch in raw if not unicodedata.combining(ch))
    return re.sub(r'[^a-z0-9]+', ' ', raw).strip()


@dataclass
class Entity:
    uri: str
    eid: str
    label: str
    kinds: list[str] = field(default_factory=list)
    description: str = ''
    literals: list[dict] = field(default_factory=list)
    outgoing: list[dict] = field(default_factory=list)
    incoming: list[dict] = field(default_factory=list)


class HeritageGraph:
    def __init__(self, ttl_path: str | Path):
        self.ttl_path = Path(ttl_path)
        self.graph = Graph()
        self.graph.parse(str(self.ttl_path), format='turtle')
        self.entities: dict[str, Entity] = {}
        uris = sorted(set(self.graph.subjects(RDF.type, OWL.NamedIndividual)), key=str)
        for uri in uris:
            eid = local(uri)
            label = self.label_of(uri)
            kinds = sorted({self.label_of(kind) for kind in self.graph.objects(uri, RDF.type)
                            if kind != OWL.NamedIndividual})
            descriptions = [str(x) for x in self.graph.objects(uri, RDFS.comment)
                            if isinstance(x, Literal)]
            self.entities[eid] = Entity(str(uri), eid, label, kinds,
                                        descriptions[0] if descriptions else '')
        self.by_uri = {e.uri: e for e in self.entities.values()}
        for entity in self.entities.values():
            subj = URIRef(entity.uri)
            for predicate, obj in self.graph.predicate_objects(subj):
                if predicate in (RDF.type, RDFS.label, RDFS.comment):
                    continue
                if isinstance(obj, Literal):
                    entity.literals.append(self._fact(subj, predicate, obj, 'literal'))
                elif isinstance(obj, URIRef):
                    fact = self._fact(subj, predicate, obj, 'outgoing')
                    entity.outgoing.append(fact)
                    target = self.by_uri.get(str(obj))
                    if target is not None:
                        target.incoming.append({**fact, 'direction': 'incoming'})
            entity.literals.sort(key=lambda f: (f['predicate'], f['value']))
            entity.outgoing.sort(key=lambda f: (f['predicate'], f['value']))
            entity.incoming.sort(key=lambda f: (f['predicate'], f['subject_label']))

    def label_of(self, uri: URIRef) -> str:
        vals = list(self.graph.objects(uri, RDFS.label))
        if vals:
            # Priorizar etiquetas españolas cuando haya varias.
            vals.sort(key=lambda x: (str(x.language or '').lower() not in ('es', 'es-pe'), str(x)))
            return str(vals[0])
        return humanize(local(uri))

    def _fact(self, subj, pred, obj, direction):
        obj_ent = self.by_uri.get(str(obj))
        return {
            'subject': str(subj),
            'subject_label': self.label_of(subj),
            'predicate': str(pred),
            'predicate_label': self.label_of(pred),
            'object': str(obj),
            'value': obj_ent.label if obj_ent else (str(obj) if isinstance(obj, Literal) else self.label_of(obj)),
            'direction': direction,
            'object_eid': obj_ent.eid if obj_ent else None,
            'datatype': str(obj.datatype) if isinstance(obj, Literal) and obj.datatype else None,
        }

    def stats(self):
        return {'triples': len(self.graph), 'individuals': len(self.entities),
                'types': len({kind for e in self.entities.values() for kind in e.kinds}),
                'geolocated': sum(bool({local(f['predicate']) for f in e.literals} & {'lat'})
                                    and bool({local(f['predicate']) for f in e.literals} & {'long'})
                                    for e in self.entities.values())}

    def types(self) -> list[str]:
        return sorted({k for e in self.entities.values() for k in e.kinds})

    def catalog(self, query='', kind='Todos') -> list[Entity]:
        term = normalize(query)
        words = term.split()
        result = [e for e in self.entities.values()
                  if (kind == 'Todos' or kind in e.kinds)
                  and (not words or all(w in normalize(' '.join([e.label, e.eid, e.description, ' '.join(e.kinds)]))
                                        for w in words))]
        return sorted(result, key=lambda e: normalize(e.label))

    def related_ids(self, eid: str) -> list[str]:
        ent = self.entities[eid]
        ids = [f['object_eid'] for f in ent.outgoing if f.get('object_eid')]
        ids.extend(local(f['subject']) for f in ent.incoming)
        return list(dict.fromkeys(x for x in ids if x in self.entities and x != eid))

    def facts(self, ids: list[str], limit: int = 24) -> list[dict]:
        """Hechos directos con la URI exacta que permite su inspección."""
        results = []
        seen = set()
        for eid in ids:
            ent = self.entities.get(eid)
            if not ent:
                continue
            for fact in ent.literals + ent.outgoing + ent.incoming:
                key = (fact['subject'], fact['predicate'], fact['object'])
                if key not in seen:
                    seen.add(key)
                    results.append(fact)
                if len(results) >= limit:
                    return results
        return results

    def data_card(self, eid: str) -> dict:
        ent = self.entities[eid]
        return {
            'id': ent.eid, 'uri': ent.uri, 'name': ent.label,
            'kinds': ent.kinds, 'description': ent.description,
            'properties': ent.literals, 'relations': ent.outgoing,
            'incoming': ent.incoming,
        }
