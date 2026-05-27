"""
Testes para o app coletas
"""
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from usuarios.models import Usuario
from empresas.models import Empresa, Profissional, Departamento
from modelos.models import ModeloCartao, CampoCartao
from .models import Coleta, ColetaProfissional, RespostaColeta, RespostaCampo, Foto, Assinatura


class ColetaModelTest(TestCase):
    """Testes para o modelo Coleta"""
    
    def setUp(self):
        usuario = Usuario.objects.create_user(
            email='empresa@example.com',
            password='senha123',
            tipo_usuario='empresa'
        )
        self.empresa = Empresa.objects.create(
            usuario=usuario,
            razao_social='Empresa Teste',
            cnpj='12345678000190'
        )
        self.modelo = ModeloCartao.objects.create(
            empresa=self.empresa,
            nome='Modelo Teste'
        )
    
    def test_create_coleta(self):
        """Testa criação de coleta"""
        coleta = Coleta.objects.create(
            empresa=self.empresa,
            modelo=self.modelo,
            nome='Coleta 2024',
            descricao='Coleta anual de dados'
        )
        self.assertEqual(coleta.status, 'rascunho')
        self.assertIn('Coleta 2024', str(coleta))
    
    def test_coleta_status_transitions(self):
        """Testa transições de status"""
        coleta = Coleta.objects.create(
            empresa=self.empresa,
            modelo=self.modelo,
            nome='Coleta Teste'
        )
        
        # Rascunho -> Em andamento
        coleta.status = 'em_andamento'
        coleta.save()
        self.assertEqual(coleta.status, 'em_andamento')
        
        # Em andamento -> Concluída
        coleta.status = 'concluida'
        coleta.save()
        self.assertEqual(coleta.status, 'concluida')


class ColetaProfissionalModelTest(TestCase):
    """Testes para o modelo ColetaProfissional"""
    
    def setUp(self):
        usuario = Usuario.objects.create_user(
            email='empresa@example.com',
            password='senha123',
            tipo_usuario='empresa'
        )
        empresa = Empresa.objects.create(
            usuario=usuario,
            razao_social='Empresa Teste',
            cnpj='12345678000190'
        )
        modelo = ModeloCartao.objects.create(
            empresa=empresa,
            nome='Modelo Teste'
        )
        self.coleta = Coleta.objects.create(
            empresa=empresa,
            modelo=modelo,
            nome='Coleta Teste'
        )
        usuario_prof = Usuario.objects.create_user(
            email='profissional_model@test.com',
            password='senha123',
            tipo_usuario='profissional'
        )
        self.profissional = Profissional.objects.create(
            usuario=usuario_prof,
            empresa=empresa,
            nome='João Silva',
            cpf='12345678901'
        )
    
    def test_create_coleta_profissional(self):
        """Testa criação de coleta profissional"""
        cp = ColetaProfissional.objects.create(
            coleta=self.coleta,
            profissional=self.profissional
        )
        self.assertEqual(cp.status, 'pendente')
        self.assertIsNone(cp.data_inicio)
    
    def test_gerar_token_acesso(self):
        """Testa geração de token de acesso"""
        cp = ColetaProfissional.objects.create(
            coleta=self.coleta,
            profissional=self.profissional
        )
        token = cp.gerar_token_acesso()
        self.assertIsNotNone(token)
        self.assertEqual(len(token), 64)


class RespostaColetaModelTest(TestCase):
    """Testes para o modelo RespostaColeta"""
    
    def setUp(self):
        usuario = Usuario.objects.create_user(
            email='empresa@example.com',
            password='senha123',
            tipo_usuario='empresa'
        )
        empresa = Empresa.objects.create(
            usuario=usuario,
            razao_social='Empresa Teste',
            cnpj='12345678000190'
        )
        modelo = ModeloCartao.objects.create(
            empresa=empresa,
            nome='Modelo Teste'
        )
        coleta = Coleta.objects.create(
            empresa=empresa,
            modelo=modelo,
            nome='Coleta Teste'
        )
        usuario_prof = Usuario.objects.create_user(
            email='resposta_model_prof@test.com',
            password='senha123',
            tipo_usuario='profissional'
        )
        profissional = Profissional.objects.create(
            usuario=usuario_prof,
            empresa=empresa,
            nome='João Silva',
            cpf='12345678901'
        )
        self.coleta_prof = ColetaProfissional.objects.create(
            coleta=coleta,
            profissional=profissional
        )
    
    def test_create_resposta_coleta(self):
        """Testa criação de resposta de coleta"""
        resposta = RespostaColeta.objects.create(
            coleta_profissional=self.coleta_prof
        )
        self.assertIsNotNone(resposta.created_at)
        self.assertIsNotNone(resposta.updated_at)


class ColetaAPITest(APITestCase):
    """Testes para API de coletas"""
    
    def setUp(self):
        self.client = APIClient()
        usuario_empresa = Usuario.objects.create_user(
            email='empresa@example.com',
            password='senha123',
            tipo_usuario='empresa'
        )
        self.empresa = Empresa.objects.create(
            usuario=usuario_empresa,
            razao_social='Empresa Teste',
            cnpj='12345678000190'
        )
        self.modelo = ModeloCartao.objects.create(
            empresa=self.empresa,
            nome='Modelo Teste'
        )
        self.client.force_authenticate(user=usuario_empresa)
    
    def test_create_coleta(self):
        """Testa criação de coleta via API"""
        url = '/api/v1/coletas/'
        data = {
            'empresa': str(self.empresa.usuario.id),
            'modelo': str(self.modelo.id),
            'nome': 'Nova Coleta',
            'descricao': 'Descrição da coleta',
            'prazo': '2024-12-31T23:59:59Z'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_iniciar_coleta(self):
        """Testa iniciar coleta"""
        coleta = Coleta.objects.create(
            empresa=self.empresa,
            modelo=self.modelo,
            nome='Coleta Teste',
            status='rascunho'
        )
        
        url = f'/api/v1/coletas/{coleta.id}/iniciar/'
        response = self.client.post(url, {'todos_profissionais': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        coleta.refresh_from_db()
        self.assertEqual(coleta.status, 'em_andamento')
    
    def test_cancelar_coleta(self):
        """Testa cancelar coleta"""
        coleta = Coleta.objects.create(
            empresa=self.empresa,
            modelo=self.modelo,
            nome='Coleta Teste',
            status='em_andamento'
        )
        
        url = f'/api/v1/coletas/{coleta.id}/cancelar/'
        data = {'motivo': 'Coleta não é mais necessária'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        coleta.refresh_from_db()
        self.assertEqual(coleta.status, 'cancelada')
    
    def test_finalizar_coleta(self):
        """Testa finalizar coleta"""
        coleta = Coleta.objects.create(
            empresa=self.empresa,
            modelo=self.modelo,
            nome='Coleta Teste',
            status='em_andamento'
        )
        
        url = f'/api/v1/coletas/{coleta.id}/finalizar/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        coleta.refresh_from_db()
        self.assertEqual(coleta.status, 'concluida')
    
    def test_estatisticas_coleta(self):
        """Testa endpoint de estatísticas"""
        coleta = Coleta.objects.create(
            empresa=self.empresa,
            modelo=self.modelo,
            nome='Coleta Teste'
        )
        usuario_prof = Usuario.objects.create_user(
            email='estatistica_prof@test.com',
            password='senha123',
            tipo_usuario='profissional'
        )
        prof = Profissional.objects.create(
            usuario=usuario_prof,
            empresa=self.empresa,
            nome='João Silva',
            cpf='12345678901'
        )
        ColetaProfissional.objects.create(
            coleta=coleta,
            profissional=prof
        )
        
        url = f'/api/v1/coletas/{coleta.id}/estatisticas/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Serializer returns detailed keys; ensure one of the expected totals is present
        self.assertIn('total_profissionais', response.data)


class ColetaProfissionalAPITest(APITestCase):
    """Testes para API de coleta profissional"""
    
    def setUp(self):
        self.client = APIClient()
        usuario_empresa = Usuario.objects.create_user(
            email='empresa@example.com',
            password='senha123',
            tipo_usuario='empresa'
        )
        empresa = Empresa.objects.create(
            usuario=usuario_empresa,
            razao_social='Empresa Teste',
            cnpj='12345678000190'
        )
        modelo = ModeloCartao.objects.create(
            empresa=empresa,
            nome='Modelo Teste'
        )
        self.coleta = Coleta.objects.create(
            empresa=empresa,
            modelo=modelo,
            nome='Coleta Teste'
        )
        usuario_prof = Usuario.objects.create_user(
            email='profissional_apitest@test.com',
            password='senha123',
            tipo_usuario='profissional'
        )
        self.profissional = Profissional.objects.create(
            usuario=usuario_prof,
            empresa=empresa,
            nome='João Silva',
            cpf='12345678901'
        )
        self.client.force_authenticate(user=usuario_empresa)
    
    def test_adicionar_profissional(self):
        """Testa adicionar profissional à coleta"""
        url = '/api/v1/coletas-profissionais/'
        data = {
            'coleta': str(self.coleta.id),
            'profissional_id': str(self.profissional.usuario.id)
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_enviar_notificacao(self):
        """Testa envio de notificação"""
        cp = ColetaProfissional.objects.create(
            coleta=self.coleta,
            profissional=self.profissional
        )
        
        url = f'/api/v1/coletas-profissionais/{cp.id}/enviar_notificacao/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RespostaColetaAPITest(APITestCase):
    """Testes para API de respostas de coleta"""
    
    def setUp(self):
        self.client = APIClient()
        usuario_empresa = Usuario.objects.create_user(
            email='empresa@example.com',
            password='senha123',
            tipo_usuario='empresa'
        )
        empresa = Empresa.objects.create(
            usuario=usuario_empresa,
            razao_social='Empresa Teste',
            cnpj='12345678000190'
        )
        modelo = ModeloCartao.objects.create(
            empresa=empresa,
            nome='Modelo Teste'
        )
        self.campo = CampoCartao.objects.create(
            modelo=modelo,
            nome_campo='nome_completo',
            tipo='texto',
            ordem=1
        )
        coleta = Coleta.objects.create(
            empresa=empresa,
            modelo=modelo,
            nome='Coleta Teste'
        )
        usuario_prof = Usuario.objects.create_user(
            email='resposta_prof@test.com',
            password='senha123',
            tipo_usuario='profissional'
        )
        profissional = Profissional.objects.create(
            usuario=usuario_prof,
            empresa=empresa,
            nome='João Silva',
            cpf='12345678901'
        )
        self.coleta_prof = ColetaProfissional.objects.create(
            coleta=coleta,
            profissional=profissional
        )
        self.client.force_authenticate(user=usuario_empresa)
    
    def test_create_resposta(self):
        """Testa criação de resposta"""
        url = '/api/v1/respostas-coletas/'
        data = {
            'coleta_profissional_id': str(self.coleta_prof.id),
            'respostas': [
                {
                    'campo_id': str(self.campo.id),
                    'valor': 'João da Silva'
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_validar_resposta(self):
        """Testa validação de resposta"""
        resposta = RespostaColeta.objects.create(
            coleta_profissional=self.coleta_prof
        )
        
        url = f'/api/v1/respostas-coletas/{resposta.id}/validar/'
        data = {'aprovado': True}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ColetaViewSetTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()

        # Criar empresa e profissional
        empresa_user = self.user_model.objects.create_user(email="empresa@test.com", password="senha123", tipo_usuario="empresa")
        self.empresa = Empresa.objects.create(usuario=empresa_user, nome_fantasia="Empresa Teste", razao_social="Empresa Teste Ltda", cnpj='00000000000100')
        self.profissional_user = self.user_model.objects.create_user(email="profissional@test.com", password="1234", tipo_usuario="profissional")
        self.profissional = Profissional.objects.create(usuario=self.profissional_user, empresa=self.empresa)

        # Criar coleta vinculada à empresa
        self.coleta = Coleta.objects.create(nome="Coleta Teste", empresa=self.empresa)

    def test_profissional_can_view_coletas(self):
        # Autenticar como profissional
        self.client.force_authenticate(user=self.profissional_user)

        # Fazer requisição para listar coletas
        response = self.client.get("/api/v1/coletas/")

        # Verificar se a coleta da empresa está na resposta
        self.assertEqual(response.status_code, 200)
        resp_json = response.json()
        if isinstance(resp_json, dict):
            items = resp_json.get('results', [])
        else:
            items = resp_json
        self.assertIn(self.coleta.nome, [coleta["nome"] for coleta in items])

