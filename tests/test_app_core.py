"""Pruebas sin conexión a Internet ni credenciales Groq.

Ejecutar desde raíz: python -m unittest discover -s tests -v
"""
import unittest
from io import BytesIO
from types import SimpleNamespace
from config_graphrag import TTL_PATH
from core.graph import HeritageGraph
from core.retrieval import Retriever
from core.assistant import answer_question
from core.pdf import create_pdf
from core.spanish import about_question, where_question, polish_spanish, prep_phrase


class FakeClient:
    def __init__(self, answer='Respuesta elaborada solo con datos recuperados.', fail=False):
        self.answer = answer
        self.fail = fail
        self.params = None
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
    def create(self, **kwargs):
        self.params = kwargs
        if self.fail:
            raise RuntimeError('API indisponible; token no debe aparecer')
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self.answer))])


class TestGraph(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = HeritageGraph(TTL_PATH)
        cls.retriever = Retriever(cls.graph)

    def test_original_data_retained(self):
        self.assertEqual(len(self.graph.graph), 1060)
        self.assertEqual(len(self.graph.entities), 87)
        self.assertEqual(self.graph.stats()['geolocated'], 34)

    def test_ausangate_without_rdf_label_is_discoverable(self):
        self.assertEqual(self.graph.entities['Ausangate'].label, 'Ausangate')
        self.assertIn('Ausangate', [x.eid for x in self.graph.catalog('Ausangate')])

    def test_search_chooses_central_concepts(self):
        cases = {
            "¿Qué es Qoyllur Rit'i?": 'FestividadQoylluriti',
            '¿Qué hacen los ukukus?': 'Ukumaris_Paucartambo_2025',
            '¿Cuánto dura la lomada?': 'Lomada_2025',
            '¿Dónde se ubica Sinakara?': 'Sinakara',
            '¿Qué vestimenta usan los ukukus?': 'TrajeUkumari',
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                self.assertEqual(self.retriever.search(question)[0]['id'], expected)

    def test_followup_keeps_context(self):
        first = self.retriever.search('Cuéntame sobre Ausangate')[0]['id']
        second = self.retriever.search('¿Qué hay allí?', previous_eid=first)
        self.assertEqual(second[0]['id'], first)

    def test_returned_relations_have_real_uris(self):
        a = answer_question(self.graph, self.retriever, '¿Cuánto dura la lomada?')
        self.assertTrue(a.evidence)
        for f in a.evidence:
            self.assertIn((f['subject'], f['predicate'], f['object']),
                          {(str(s),str(p),str(o)) for s,p,o in self.graph.graph})

    def test_without_api_still_works(self):
        a = answer_question(self.graph, self.retriever, "¿Qué es Qoyllur Rit'i?")
        self.assertEqual(a.status, 'sin_api')
        self.assertIn('Peregrinación', a.text)

    def test_groq_model_and_no_reasoning_in_visible_answer(self):
        fake = FakeClient()
        a = answer_question(self.graph, self.retriever, '¿Qué sabemos de los ukukus?', client=fake)
        self.assertEqual(a.status, 'groq')
        self.assertTrue(a.generated)
        self.assertEqual(fake.params['model'], 'openai/gpt-oss-120b')
        self.assertFalse(fake.params['include_reasoning'])
        self.assertIn('DATOS_RDF', fake.params['messages'][1]['content'])

    def test_api_failure_local_fallback(self):
        a = answer_question(self.graph, self.retriever, '¿Qué sabemos de los ukukus?', client=FakeClient(fail=True))
        self.assertEqual(a.status, 'api_no_disponible')
        self.assertIn('ukumaris', a.text.lower())
        self.assertNotIn('token', a.text)

    def test_spanish_articles_in_suggestions(self):
        self.assertEqual(about_question('Sinakara'), '¿Qué sabemos sobre el Sinakara?')
        self.assertEqual(about_question('Glaciar Colque Punku'),
                         '¿Qué sabemos sobre el glaciar Colque Punku?')
        self.assertEqual(about_question('Ausangate'),
                         '¿Qué sabemos sobre el apu Ausangate?')
        self.assertEqual(where_question('Laguna Yanaqocha'),
                         '¿Dónde se encuentra la laguna Yanaqocha?')
        self.assertEqual(about_question('Paucartambo'),
                         '¿Qué sabemos sobre Paucartambo?')
        self.assertEqual(prep_phrase('de', 'Ausangate'), 'del apu Ausangate')
        self.assertEqual(prep_phrase('a', 'Sinakara'), 'al Sinakara')

    def test_suggestions_use_natural_spanish(self):
        questions = self.retriever.suggestions('Ausangate', count=10)
        self.assertIn('¿Qué sabemos sobre el glaciar Colque Punku?', questions)
        self.assertFalse(any('sobre Glaciar' in q for q in questions))

    def test_polish_generated_spanish_without_touching_rdf(self):
        cases = {
            'Sinakara es un espacio sagrado.': 'El Sinakara es un espacio sagrado.',
            'En Sinakara ocurre la ceremonia.': 'En el Sinakara ocurre la ceremonia.',
            'Se ubica en Glaciar Colque Punku.': 'Se ubica en el glaciar Colque Punku.',
            'La vista de Sinakara y de Glaciar Colque Punku.':
                'La vista del Sinakara y del glaciar Colque Punku.',
            'Visita el Glaciar Colque Punku.': 'Visita el glaciar Colque Punku.',
            'El nevado Ausangate es un referente.': 'El nevado Ausangate es un referente.',
            'Apu Ausangate es importante.': 'El apu Ausangate es importante.',
            'Está cerca de el Sinakara.': 'Está cerca del Sinakara.',
        }
        for original, expected in cases.items():
            with self.subTest(original=original):
                self.assertEqual(polish_spanish(original), expected)

    def test_generated_answer_is_polished(self):
        fake = FakeClient('Sinakara se sitúa cerca de Glaciar Colque Punku.')
        a = answer_question(self.graph, self.retriever, '¿Dónde está Sinakara?', client=fake)
        self.assertEqual(a.text, 'El Sinakara se sitúa cerca del glaciar Colque Punku.')

    def test_local_answer_uses_articles_and_agreement(self):
        a = answer_question(self.graph, self.retriever, '¿Qué hacen los ukukus?')
        self.assertIn('Los ukumaris de Paucartambo', a.text)
        self.assertIn('ejecutan la danza del Ukumari', a.text)
        self.assertNotIn('ejecutan de la danza', a.text)
        glacier = answer_question(self.graph, self.retriever,
                                  '¿Qué sabemos sobre el glaciar Colque Punku?')
        self.assertIn('Forma parte del apu Ausangate', glacier.text)
        self.assertNotIn('de el apu', glacier.text)

    def test_structured_pdfs(self):
        for eid in ('Ausangate', 'Lomada_2025', 'Ukumaris_Paucartambo_2025'):
            data = create_pdf(self.graph.data_card(eid))
            self.assertTrue(data.startswith(b'%PDF-'))
            self.assertGreater(len(data), 1000)


if __name__ == '__main__':
    unittest.main()
