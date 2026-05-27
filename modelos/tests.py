from django.test import TestCase
from rest_framework.test import APIClient

from usuarios.models import Usuario
from empresas.models import Empresa, Profissional
from modelos.models import ModeloCartao, CampoCartao


class CampoCartaoPermissionsTest(TestCase):
    def setUp(self):
        # Company user and profile
        self.company_user = Usuario.objects.create_user(email='empresa@example.com', password='testpass')
        self.empresa = Empresa.objects.create(
            usuario=self.company_user,
            razao_social='ACME Ltda',
            nome_fantasia='ACME',
            cnpj='12.345.678/0001-99',
            url_personalizada='acme'
        )

        # Professional user and profile linked to same company
        self.prof_user = Usuario.objects.create_user(email='prof@example.com', password='testpass')
        self.profissional = Profissional.objects.create(
            usuario=self.prof_user,
            empresa=self.empresa,
            nome='Fulano',
            cpf='12345678901'
        )

        # Another company/user for negative test
        self.other_user = Usuario.objects.create_user(email='other@example.com', password='testpass')
        self.other_empresa = Empresa.objects.create(
            usuario=self.other_user,
            razao_social='Other Ltda',
            nome_fantasia='Other',
            cnpj='98.765.432/0001-11',
            url_personalizada='other'
        )

        # Create modelo and campos for empresa
        self.modelo = ModeloCartao.objects.create(
            empresa=self.empresa,
            nome='Cartao Teste'
        )

        # Campos: nome, foto, assinatura, idade
        CampoCartao.objects.create(modelo=self.modelo, nome_campo='Campo nome', tipo='texto_curto', obrigatorio=False, pergunta_formulario='Nome', ordem=1)
        CampoCartao.objects.create(modelo=self.modelo, nome_campo='FOTO', tipo='foto', obrigatorio=False, pergunta_formulario='Foto', ordem=2)
        CampoCartao.objects.create(modelo=self.modelo, nome_campo='ASSINATURA', tipo='assinatura', obrigatorio=False, pergunta_formulario='Assinatura', ordem=3)
        CampoCartao.objects.create(modelo=self.modelo, nome_campo='Idade', tipo='texto_curto', obrigatorio=False, pergunta_formulario='Idade', ordem=4)

        self.client = APIClient()

    def test_company_user_sees_campos(self):
        # authenticate as company user
        self.client.force_authenticate(user=self.company_user)
        resp = self.client.get(f'/api/v1/campos-cartao/?modelo_id={self.modelo.id}')
        self.assertEqual(resp.status_code, 200)
        data = resp.json().get('results', resp.json())
        # Expect 4 campos
        self.assertEqual(len(data), 4)

    def test_professional_user_sees_campos(self):
        self.client.force_authenticate(user=self.prof_user)
        resp = self.client.get(f'/api/v1/campos-cartao/?modelo_id={self.modelo.id}')
        self.assertEqual(resp.status_code, 200)
        data = resp.json().get('results', resp.json())
        self.assertEqual(len(data), 4)

    def test_other_company_user_does_not_see_campos(self):
        self.client.force_authenticate(user=self.other_user)
        resp = self.client.get(f'/api/v1/campos-cartao/?modelo_id={self.modelo.id}')
        self.assertEqual(resp.status_code, 200)
        data = resp.json().get('results', resp.json())
        # Other company should not see those campos
        self.assertEqual(len(data), 0)
"""
Testes para o app modelos
"""
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from usuarios.models import Usuario
from empresas.models import Empresa
from .models import ModeloCartao, CampoCartao


class ModeloCartaoModelTest(TestCase):
    """Testes para o modelo ModeloCartao"""
    
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
    
    def test_create_modelo_cartao(self):
        """Testa criação de modelo de cartão"""
        modelo = ModeloCartao.objects.create(
            empresa=self.empresa,
            nome='Modelo Padrão',
            descricao='Modelo padrão da empresa',
            largura_mm=85.6,
            altura_mm=54.0,
            dpi=300
        )
        self.assertEqual(modelo.nome, 'Modelo Padrão')
        self.assertEqual(modelo.largura_mm, 85.6)
        self.assertIn('Modelo Padrão', str(modelo))
    
    def test_modelo_cartao_default_dimensions(self):
        """Testa dimensões padrão do cartão"""
        modelo = ModeloCartao.objects.create(
            empresa=self.empresa,
            nome='Modelo Teste'
        )
        self.assertEqual(modelo.largura_mm, 85.6)
        self.assertEqual(modelo.altura_mm, 54.0)
        self.assertEqual(modelo.dpi, 300)


class CampoCartaoModelTest(TestCase):
    """Testes para o modelo CampoCartao"""
    
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
        self.modelo = ModeloCartao.objects.create(
            empresa=empresa,
            nome='Modelo Teste'
        )
    
    def test_create_campo_texto(self):
        """Testa criação de campo de texto"""
        campo = CampoCartao.objects.create(
            modelo=self.modelo,
            nome_campo='nome_completo',
            pergunta_formulario='Nome Completo',
            tipo='texto_curto',
            ordem=1,
            posicao_x=10.0,
            posicao_y=20.0
        )
        self.assertEqual(campo.tipo, 'texto_curto')
        self.assertEqual(campo.obrigatorio, True)
    
    def test_create_campo_foto(self):
        """Testa criação de campo de foto"""
        campo = CampoCartao.objects.create(
            modelo=self.modelo,
            nome_campo='foto',
            pergunta_formulario='Foto 3x4',
            tipo='foto',
            ordem=2,
            posicao_x=5.0,
            posicao_y=5.0,
            largura=25.0,
            altura=33.0
        )
        self.assertEqual(campo.tipo, 'foto')
        self.assertEqual(campo.largura, 25.0)
    
    def test_campo_ordering(self):
        """Testa ordenação de campos"""
        campo1 = CampoCartao.objects.create(
            modelo=self.modelo,
            nome_campo='campo1',
            tipo='texto_curto',
            ordem=2
        )
        campo2 = CampoCartao.objects.create(
            modelo=self.modelo,
            nome_campo='campo2',
            tipo='texto_curto',
            ordem=1
        )
        campos = list(self.modelo.campos.all())
        self.assertEqual(campos[0], campo2)
        self.assertEqual(campos[1], campo1)


class ModeloCartaoAPITest(APITestCase):
    """Testes para API de modelos de cartão"""
    
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
        self.client.force_authenticate(user=usuario_empresa)
    
    def test_create_modelo(self):
        """Testa criação de modelo via API"""
        url = '/api/v1/modelos-cartao/'
        data = {
            'empresa': str(self.empresa.usuario.id),
            'nome': 'Novo Modelo',
            'descricao': 'Descrição do modelo',
            'largura_mm': 85.6,
            'altura_mm': 54.0,
            'dpi': 300
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_list_modelos_empresa(self):
        """Testa listagem de modelos da empresa"""
        ModeloCartao.objects.create(
            empresa=self.empresa,
            nome='Modelo 1'
        )
        
        url = '/api/v1/modelos-cartao/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('results', response.data)), 1)
    
    def test_duplicar_modelo(self):
        """Testa duplicação de modelo"""
        modelo = ModeloCartao.objects.create(
            empresa=self.empresa,
            nome='Modelo Original'
        )
        CampoCartao.objects.create(
            modelo=modelo,
            nome_campo='nome',
            tipo='texto_curto',
            ordem=1
        )

        url = f'/api/v1/modelos-cartao/{modelo.id}/duplicate/'
        data = {'novo_nome': 'Modelo Duplicado', 'copiar_campos': True}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ModeloCartao.objects.count(), 2)
    
    def test_modelo_isolation_by_empresa(self):
        """Testa isolamento de modelos por empresa"""
        # Criar outra empresa
        outro_usuario = Usuario.objects.create_user(
            email='outra@example.com',
            password='senha123',
            tipo_usuario='empresa'
        )
        outra_empresa = Empresa.objects.create(
            usuario=outro_usuario,
            razao_social='Outra Empresa',
            cnpj='98765432000110'
        )
        
        # Criar modelo na outra empresa
        ModeloCartao.objects.create(
            empresa=outra_empresa,
            nome='Modelo Outra Empresa'
        )
        
        # Listar modelos - deve retornar apenas da empresa logada
        url = '/api/v1/modelos-cartao/'
        response = self.client.get(url)
        self.assertEqual(len(response.data.get('results', response.data)), 0)


class CampoCartaoAPITest(APITestCase):
    """Testes para API de campos de cartão"""
    
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
    
    def test_create_campo(self):
        """Testa criação de campo"""
        url = '/api/v1/campos-cartao/'
        data = {
            'modelo': str(self.modelo.id),
            'nome_campo': 'nome_completo',
            'pergunta_formulario': 'Nome Completo',
            'tipo': 'texto_curto',
            'ordem': 1,
            'posicao_x': 10.0,
            'posicao_y': 20.0
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_reordenar_campos(self):
        """Testa reordenação de campos"""
        campo1 = CampoCartao.objects.create(
            modelo=self.modelo,
            nome_campo='campo1',
            tipo='texto_curto',
            ordem=1
        )
        campo2 = CampoCartao.objects.create(
            modelo=self.modelo,
            nome_campo='campo2',
            tipo='texto_curto',
            ordem=2
        )

        url = '/api/v1/campos-cartao/reorder/'
        data = {'campos_ordem': [{'id': str(campo1.id), 'ordem': 2}, {'id': str(campo2.id), 'ordem': 1}]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_tipos_disponiveis(self):
        """Testa endpoint de tipos disponíveis"""
        url = '/api/v1/campos-cartao/tipos_disponiveis/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('texto_curto', [t['value'] for t in response.data])
        self.assertIn('foto', [t['value'] for t in response.data])

