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
        self.assertIn('Ukumaris', a.text)
        self.assertNotIn('token', a.text)

    def test_structured_pdfs(self):
        for eid in ('Ausangate', 'Lomada_2025', 'Ukumaris_Paucartambo_2025'):
            data = create_pdf(self.graph.data_card(eid))
            self.assertTrue(data.startswith(b'%PDF-'))
            self.assertGreater(len(data), 1000)


if __name__ == '__main__':
    unittest.main()
