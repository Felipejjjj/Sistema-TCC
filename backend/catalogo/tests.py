from datetime import date
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from catalogo.models import Trabalho, Autor, Curso

PUBLICO = '/api/publico/v1/'
GESTAO = '/api/gestao/'


class CatalogoTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed', verbosity=0)

    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.get(username='coordenacao1')
        self.trabalho = Trabalho.objects.filter(situacao='publicado').first()

    def autenticar(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + Token.objects.get(user=self.user).key)

    def payload(self):
        t = self.trabalho
        return {'titulo': 'Novo trabalho para avaliação', 'resumo': 'Pesquisa sobre APIs.',
                'ano': timezone.localdate().year, 'situacao': 'em_andamento',
                'link_pdf': 'https://example.org/teste.pdf', 'curso': t.curso_id,
                'orientador': t.orientador_id, 'autores': list(t.autores.values_list('id', flat=True))}

    def test_publico_paginado_sem_dados_privados_e_ocultos(self):
        r = self.client.get(PUBLICO + 'trabalhos/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 30)
        self.assertEqual(len(r.data['results']), 6)
        for item in r.data['results']:
            self.assertIsInstance(item['curso'], str)
            self.assertIsInstance(item['orientador'], str)
            self.assertTrue(all(isinstance(a, str) for a in item['autores']))
            self.assertFalse({'nota', 'email', 'email_institucional', 'cadastrado_por', 'situacao'} & item.keys())
        oculto = Trabalho.objects.exclude(situacao='publicado').first()
        self.assertEqual(self.client.get(f'{PUBLICO}trabalhos/{oculto.pk}/').status_code, 404)
        detalhe = self.client.get(f'{PUBLICO}trabalhos/{self.trabalho.pk}/').data
        self.assertEqual(detalhe['resumo'], self.trabalho.resumo)
        self.assertTrue(detalhe['palavras_chave'])

    def test_busca_titulo_resumo_autor_orientador(self):
        t = self.trabalho
        for termo in [t.titulo, 'revisão bibliográfica', t.autores.first().nome, t.orientador.nome]:
            r = self.client.get(PUBLICO + 'trabalhos/', {'search': termo})
            self.assertEqual(r.status_code, 200)
            self.assertGreater(r.data['count'], 0)
            ids = [x['id'] for x in r.data['results']]
            self.assertEqual(len(ids), len(set(ids)))

    def test_filtros_combinados_ordenacao_vazio(self):
        t = self.trabalho
        r = self.client.get(PUBLICO + 'trabalhos/', {'ano': t.ano, 'curso': t.curso_id,
                            'palavra_chave': t.palavras_chave.first().termo, 'search': t.titulo})
        self.assertEqual(r.data['count'], 1)
        for ordering in ['ano', '-ano', 'titulo', '-titulo']:
            r = self.client.get(PUBLICO + 'trabalhos/', {'ordering': ordering})
            campo = ordering.lstrip('-')
            valores = [x[campo] for x in r.data['results']]
            self.assertEqual(valores, sorted(valores, reverse=ordering.startswith('-')))
        self.assertEqual(self.client.get(PUBLICO+'trabalhos/', {'search': 'naoexiste123456'}).data['count'], 0)

    def test_estatisticas_agregadas(self):
        r = self.client.get(PUBLICO + 'estatisticas/')
        self.assertEqual(r.status_code, 200)
        for grupo in ['por_ano', 'por_curso', 'orientadores']:
            self.assertEqual(sum(x['total'] for x in r.data[grupo]), 30)

    def test_token_e_permissao(self):
        self.assertEqual(self.client.post(GESTAO+'trabalhos/', self.payload(), format='json').status_code, 401)
        r = self.client.post(GESTAO+'token/', {'username': 'coordenacao1', 'password': 'CatalogoTCC@12026'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['token'], Token.objects.get(user=self.user).key)
        user = get_user_model().objects.create_user('visitante', password='senha')
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.assertEqual(self.client.get(GESTAO+'trabalhos/').status_code, 403)

    def test_criar_publicar_editar_excluir(self):
        self.autenticar()
        p = self.payload()
        p['cadastrado_por'] = get_user_model().objects.get(username='coordenacao2').pk
        r = self.client.post(GESTAO+'trabalhos/', p, format='json')
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data['cadastrado_por'], self.user.pk)
        url = f"{GESTAO}trabalhos/{r.data['id']}/"
        self.assertEqual(self.client.patch(url, {'situacao':'publicado'}, format='json').status_code, 400)
        self.assertEqual(self.client.patch(url, {'situacao':'publicado', 'nota':'9.00',
                         'data_defesa':str(date.today())}, format='json').status_code, 200)
        self.assertEqual(self.client.get(f"{PUBLICO}trabalhos/{r.data['id']}/").status_code, 200)
        self.assertEqual(self.client.patch(url, {'nota': None}, format='json').status_code, 400)
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_validacoes_ano_autores_duplicidade(self):
        self.autenticar()
        for alteracao in [{'ano': timezone.localdate().year+1}, {'autores': []},
                          {'autores': list(Autor.objects.values_list('id',flat=True)[:3])},
                          {'situacao':'publicado', 'nota':'8.00'},
                          {'titulo':self.trabalho.titulo, 'ano':self.trabalho.ano}]:
            p = self.payload(); p.update(alteracao)
            self.assertEqual(self.client.post(GESTAO+'trabalhos/', p, format='json').status_code, 400)
        self.assertEqual(self.client.patch(f'{GESTAO}trabalhos/{self.trabalho.pk}/',
                         {'autores':[]}, format='json').status_code, 400)

    def test_crud_apoio(self):
        self.autenticar()
        for recurso, dados, alteracao in [
            ('cursos', {'nome':'Teste', 'sigla':'TEST'}, {'nome':'Editado'}),
            ('autores', {'nome':'Teste', 'email':'teste@example.org'}, {'nome':'Editado'}),
            ('orientadores', {'nome':'Teste', 'titulacao':'Mestrado', 'email_institucional':'teste@ifpb.edu.br'}, {'nome':'Editado'}),
            ('palavras-chave', {'termo':'Teste'}, {'termo':'Editado'})]:
            r = self.client.post(GESTAO+recurso+'/', dados, format='json')
            self.assertEqual(r.status_code, 201, r.data)
            url = f"{GESTAO}{recurso}/{r.data['id']}/"
            self.assertEqual(self.client.get(url).status_code, 200)
            self.assertEqual(self.client.patch(url, alteracao, format='json').status_code, 200)
            self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.delete(f'{GESTAO}cursos/{self.trabalho.curso_id}/').status_code, 400)

    def test_limite_compartilhado(self):
        for _ in range(20):
            self.assertEqual(self.client.get(PUBLICO+'trabalhos/').status_code, 200)
        r = self.client.get(PUBLICO+'estatisticas/')
        self.assertEqual(r.status_code, 429)
        self.assertIn('Retry-After', r.headers)

    def test_cors_schema_documentacao(self):
        r = self.client.get(PUBLICO+'trabalhos/', HTTP_ORIGIN='http://localhost:5500')
        self.assertEqual(r.headers['Access-Control-Allow-Origin'], 'http://localhost:5500')
        self.assertEqual(self.client.get('/api/schema/').status_code, 200)
        self.assertEqual(self.client.get('/api/docs/').status_code, 200)
