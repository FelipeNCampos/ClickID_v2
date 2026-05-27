"""
Testes para o app empresas
"""
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from usuarios.models import Usuario
from .models import Empresa, Departamento, Profissional


class EmpresaModelTest(TestCase):
    """Testes para o modelo Empresa"""
    
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='empresa@example.com',
            password='senha123',
            tipo_usuario='empresa'
        )
    
    def test_create_empresa(self):
        """Testa criação de empresa"""
        empresa = Empresa.objects.create(
            usuario=self.usuario,
            razao_social='Empresa Teste LTDA',
            cnpj='12345678000190',
            url_personalizada='empresa-teste'
        )
        self.assertEqual(empresa.razao_social, 'Empresa Teste LTDA')
        self.assertEqual(empresa.cnpj, '12345678000190')
        self.assertIn('Empresa Teste LTDA', str(empresa))
    
    def test_empresa_slug_auto_generation(self):
        """Testa geração automática de slug"""
        empresa = Empresa.objects.create(
            usuario=self.usuario,
            razao_social='Nova Empresa',
            cnpj='12345678000191'
        )
        self.assertIsNotNone(empresa.url_personalizada)


class DepartamentoModelTest(TestCase):
    """Testes para o modelo Departamento"""
    
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
    
    def test_create_departamento(self):
        """Testa criação de departamento"""
        depto = Departamento.objects.create(
            empresa=self.empresa,
            nome='TI',
            descricao='Departamento de TI'
        )
        self.assertEqual(depto.nome, 'TI')
        self.assertEqual(str(depto), 'TI - Empresa Teste')
    
    def test_departamento_unique_per_empresa(self):
        """Testa que nome de departamento é único por empresa"""
        Departamento.objects.create(
            empresa=self.empresa,
            nome='RH'
        )
        with self.assertRaises(Exception):
            Departamento.objects.create(
                empresa=self.empresa,
                nome='RH'
            )


class ProfissionalModelTest(TestCase):
    """Testes para o modelo Profissional"""
    
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
        self.departamento = Departamento.objects.create(
            empresa=self.empresa,
            nome='TI'
        )
    
    def test_create_profissional(self):
        """Testa criação de profissional"""
        prof = Profissional.objects.create(
            empresa=self.empresa,
            departamento=self.departamento,
            nome='João Silva',
            cpf='12345678901',
            email='joao@example.com'
        )
        self.assertEqual(prof.nome, 'João Silva')
        self.assertEqual(prof.cpf, '12345678901')
    
    def test_gerar_senha_padrao(self):
        """Testa geração de senha padrão"""
        prof = Profissional.objects.create(
            empresa=self.empresa,
            nome='Maria Silva',
            cpf='98765432101'
        )
        senha_padrao = prof.gerar_senha_padrao()
        self.assertEqual(senha_padrao, '2101')  # Últimos 4 dígitos do CPF
    
    def test_precisa_alterar_senha(self):
        """Testa verificação de necessidade de alterar senha"""
        prof = Profissional.objects.create(
            empresa=self.empresa,
            nome='Pedro Silva',
            cpf='11122233344',
            senha_alterada=False
        )
        self.assertTrue(prof.precisa_alterar_senha())
        
        prof.senha_alterada = True
        prof.save()
        self.assertFalse(prof.precisa_alterar_senha())


class EmpresaAPITest(APITestCase):
    """Testes para API de empresas"""
    
    def setUp(self):
        self.client = APIClient()
        self.admin = Usuario.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.client.force_authenticate(user=self.admin)
    
    def test_create_empresa(self):
        """Testa criação de empresa via API"""
        url = '/api/v1/empresas/'
        data = {
            'email': 'empresa@example.com',
            'password': 'senha123',
            'razao_social': 'Nova Empresa LTDA',
            'cnpj': '12345678000190',
            'url_personalizada': 'nova-empresa',
            'telefone': '1133334444'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Empresa.objects.count(), 1)
    
    def test_list_empresas(self):
        """Testa listagem de empresas"""
        usuario = Usuario.objects.create_user(
            email='empresa@example.com',
            password='senha123',
            tipo_usuario='empresa'
        )
        Empresa.objects.create(
            usuario=usuario,
            razao_social='Empresa 1',
            cnpj='12345678000190'
        )
        
        url = '/api/v1/empresas/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class DepartamentoAPITest(APITestCase):
    """Testes para API de departamentos"""
    
    def setUp(self):
        self.client = APIClient()
        self.admin = Usuario.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
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
        self.client.force_authenticate(user=self.admin)
    
    def test_create_departamento(self):
        """Testa criação de departamento"""
        url = '/api/v1/departamentos/'
        data = {
            'empresa': str(self.empresa.usuario.id),
            'nome': 'TI',
            'descricao': 'Departamento de TI'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Departamento.objects.count(), 1)
    
    def test_list_departamentos_by_empresa(self):
        """Testa listagem de departamentos por empresa"""
        Departamento.objects.create(
            empresa=self.empresa,
            nome='RH'
        )
        
        url = f'/api/v1/departamentos/?empresa_id={self.empresa.usuario.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class ProfissionalAPITest(APITestCase):
    """Testes para API de profissionais"""
    
    def setUp(self):
        self.client = APIClient()
        self.admin = Usuario.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
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
        self.departamento = Departamento.objects.create(
            empresa=self.empresa,
            nome='TI'
        )
        self.client.force_authenticate(user=self.admin)
    
    def test_create_profissional(self):
        """Testa criação de profissional"""
        url = '/api/v1/profissionais/'
        data = {
            'empresa': str(self.empresa.usuario.id),
            'departamento': str(self.departamento.id),
            'nome': 'João Silva',
            'cpf': '12345678901',
            'email': 'joao@example.com',
            'telefone': '11999999999'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Profissional.objects.count(), 1)
    
    def test_resetar_senha_profissional(self):
        """Testa reset de senha do profissional"""
        prof = Profissional.objects.create(
            empresa=self.empresa,
            nome='Maria Silva',
            cpf='98765432101',
            senha_alterada=True
        )
        
        url = f'/api/v1/profissionais/{prof.id}/resetar_senha/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        prof.refresh_from_db()
        self.assertFalse(prof.senha_alterada)
    
    def test_bulk_create_profissionais(self):
        """Testa criação em lote de profissionais"""
        url = '/api/v1/profissionais/bulk_create/'
        data = {
            'profissionais': [
                {
                    'empresa': str(self.empresa.usuario.id),
                    'nome': 'Prof 1',
                    'cpf': '11111111111',
                    'email': 'prof1@example.com'
                },
                {
                    'empresa': str(self.empresa.usuario.id),
                    'nome': 'Prof 2',
                    'cpf': '22222222222',
                    'email': 'prof2@example.com'
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

