"""Presentación en español de etiquetas RDF, sin cambiar las etiquetas originales.

Los artículos son propios del texto visible; las URI y las etiquetas del grafo
siguen intactas para la búsqueda, la citación y la interoperabilidad.
"""
from __future__ import annotations
import re

# Sustantivos iniciales que permiten asignar un artículo con seguridad.
_FEMININE = {
    'laguna', 'nación', 'festividad', 'capilla', 'iglesia', 'gruta',
    'plaza', 'danza', 'caminata', 'bajada', 'subida', 'misa',
    'procesión', 'romería', 'visita', 'noche', 'ruta', 'camisa',
    'cruz', 'casa', 'celda', 'parada', 'veneración', 'ceremonia',
}
_MASCULINE = {
    'glaciar', 'santuario', 'traje', 'día', 'ritual', 'evento',
    'descanso', 'traslado', 'cementerio', 'paso', 'viaje', 'canto',
    'silbato', 'pellón', 'sorriago',
}
_ARTICLES = {'el', 'la', 'los', 'las', 'del', 'al', 'un', 'una', 'unos', 'unas',
             'este', 'esta', 'estos', 'estas', 'ese', 'esa', 'sus', 'su', 'nuestro', 'nuestra'}
_KIND_WORDS = {'nevado', 'apu', 'monte', 'montaña', 'cerro', 'glaciar',
               'santuario', 'río', 'laguna', 'región', 'distrito',
               'localidad', 'pueblo', 'sector', 'provincia', 'área'}


def entity_mention(label: str, kinds=()) -> str:
    """Forma nominal de una entidad cuando se menciona en una oración.

    Los nombres propios de localidades (Paucartambo, Ocongate) quedan sin
    artículo por defecto. Los nombres con sustantivo común lo reciben.
    """
    name = str(label).strip()
    if not name:
        return name
    if name == 'Sinakara':
        return 'el Sinakara'
    if name == 'Ausangate' or (name.startswith('Apu Ausangate')):
        return 'el apu Ausangate'
    if name.startswith('Lomada / Loman Pureq'):
        return 'la lomada (Loman Pureq, 2025)'
    if name.startswith('Ukumaris '):
        return 'los ukumaris' + name[len('Ukumaris'):]
    first, _, rest = name.partition(' ')
    lower = first.casefold()
    if lower in _FEMININE:
        # Nación Paucartambo conserva mayúscula por ser denominación propia.
        head = first if lower == 'nación' else first.lower()
        return 'la ' + head + (' ' + rest if rest else '')
    if lower in _MASCULINE:
        return 'el ' + first.lower() + (' ' + rest if rest else '')
    if lower in _ARTICLES:
        return name
    return name


def prep_phrase(preposition: str, label: str, kinds=()) -> str:
    """Forma sintagmas como «del glaciar» y «al Sinakara»."""
    mention = entity_mention(label, kinds)
    if mention.startswith('el ') and preposition in ('de', 'a'):
        return ('del ' if preposition == 'de' else 'al ') + mention[3:]
    return preposition + ' ' + mention



# Revisión de las denominaciones geográficas más frecuentes. Solamente se
# ajusta el texto de presentación, nunca los triples o identificadores RDF.
_MENTIONS = {
    'Santuario del Señor de Qoyllur Rit\'i': 'el santuario del Señor de Qoyllur Rit\'i',
    'Glaciar Colque Punku': 'el glaciar Colque Punku',
    'Apu Ausangate': 'el apu Ausangate',
    'Laguna Yanaqocha': 'la laguna Yanaqocha',
    'Nación Paucartambo': 'la Nación Paucartambo',
    'Sinakara': 'el Sinakara',
    'Ausangate': 'el apu Ausangate',
}
_RX = re.compile(r'(?<!\w)(' + '|'.join(re.escape(s) for s in sorted(_MENTIONS, key=len, reverse=True)) + r')(?!\w)', re.IGNORECASE)
_WORD_BEFORE = re.compile(r'([\wáéíóúñ]+)\s+$', flags=re.IGNORECASE)
_SENTENCE_START = re.compile(r'(?:^|[.!?]\s+|\n\s*)$', re.DOTALL)


def polish_spanish(text: str) -> str:
    """Normaliza artículos de topónimos conocidos en prosa del asistente.

    Corrige «de Sinakara» -> «del Sinakara» y
    «sobre Glaciar Colque Punku» -> «sobre el glaciar Colque Punku».
    No modifica los nombres en el RDF, y evita artículos duplicados.
    """
    if not text:
        return text
    # Contracciones explícitas incluso si el LLM escribió artículos completos.
    text = re.sub(r'(?i)\bde\s+el\s+(?=(?:sinakara|apu\s+ausangate|glaciar\s+colque\s+punku|santuario)\b)',
                  'del ', text)
    text = re.sub(r'(?i)\ba\s+el\s+(?=(?:sinakara|apu\s+ausangate|glaciar\s+colque\s+punku|santuario)\b)',
                  'al ', text)
    pieces = []
    cursor = 0
    for match in _RX.finditer(text):
        previous = text[cursor:match.start()]
        prefix = ''.join(pieces) + previous
        original = match.group()
        canonical = _MENTIONS.get(next((name for name in _MENTIONS if name.casefold() == original.casefold()), original), None)
        if canonical is None:
            canonical = original
        article, _, noun = canonical.partition(' ')
        earlier = _WORD_BEFORE.search(prefix)
        preceding = earlier.group(1).casefold() if earlier else ''
        if preceding == 'de' and article == 'el':
            previous = re.sub(r'(?i)\bde\s+$', lambda m: 'Del ' if m.group().startswith('De') and _SENTENCE_START.search(prefix[:m.start()]) else 'del ', previous)
            inserted = noun
        elif preceding == 'a' and article == 'el':
            previous = re.sub(r'(?i)\ba\s+$', 'al ', previous)
            inserted = noun
        elif preceding in _ARTICLES or preceding in _KIND_WORDS:
            inserted = noun if preceding in {'el','la','los','las','del','al','un','una'} else original
            # «al glaciar ...» debe llevar glaciar en minúscula.
            if preceding in {'el','la','los','las','del','al','un','una'}:
                inserted = noun
        else:
            at_start = bool(_SENTENCE_START.search(prefix))
            inserted = (article.capitalize() if at_start else article) + ' ' + noun
        pieces.extend((previous, inserted))
        cursor = match.end()
    pieces.append(text[cursor:])
    return ''.join(pieces)
