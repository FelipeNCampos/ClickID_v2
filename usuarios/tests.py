"""
Testes para o app usuarios
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Usuario, Gerente, LogAuditoria

User = get_user_model()


class UsuarioModelTest(TestCase):
    """Testes para o modelo Usuario"""
    
    def setUp(self):
        self.usuario_data = {
            'email': 'teste@example.com',
            'password': 'senha123',
            'tipo_usuario': 'gerente'
        }
    
    def test_create_user(self):
        """Testa criação de usuário"""
        usuario = Usuario.objects.create_user(**self.usuario_data)
        self.assertEqual(usuario.email, 'teste@example.com')
        self.assertEqual(usuario.tipo_usuario, 'gerente')
        self.assertTrue(usuario.check_password('senha123'))
        self.assertTrue(usuario.is_active)
        self.assertFalse(usuario.is_staff)
    
    def test_create_superuser(self):
        """Testa criação de superusuário"""
        superuser = Usuario.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_active)
    
    def test_user_email_required(self):
        """Testa que email é obrigatório"""
        with self.assertRaises(ValueError):
            Usuario.objects.create_user(email='', password='senha123')
    
    def test_user_string_representation(self):
        """Testa representação em string do usuário"""
        usuario = Usuario.objects.create_user(**self.usuario_data)
        self.assertEqual(str(usuario), 'teste@example.com (gerente)')


class GerenteModelTest(TestCase):
    """Testes para o modelo Gerente"""
    
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='gerente@example.com',
            password='senha123',
            tipo_usuario='gerente'
        )
    
    def test_create_gerente(self):
        """Testa criação de gerente"""
        gerente = Gerente.objects.create(
            usuario=self.usuario,
            nome='João Silva',
            cpf='12345678901',
            telefone='11999999999'
        )
        self.assertEqual(gerente.nome, 'João Silva')
        self.assertEqual(gerente.cpf, '12345678901')
        self.assertEqual(str(gerente), 'João Silva - gerente@example.com')


class LogAuditoriaModelTest(TestCase):
    """Testes para o modelo LogAuditoria"""
    
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='user@example.com',
            password='senha123'
        )
    
    def test_create_log(self):
        """Testa criação de log de auditoria"""
        log = LogAuditoria.objects.create(
            usuario=self.usuario,
            acao='login',
            descricao='Usuário fez login',
            ip_address='127.0.0.1'
        )
        self.assertEqual(log.acao, 'login')
        self.assertEqual(log.ip_address, '127.0.0.1')
        self.assertIsNotNone(log.timestamp)


class UsuarioAPITest(APITestCase):
    """Testes para API de usuários"""
    
    def setUp(self):
        self.client = APIClient()
        self.admin = Usuario.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.user = Usuario.objects.create_user(
            email='user@example.com',
            password='user123',
            tipo_usuario='empresa'
        )
    
    def test_login(self):
        """Testa endpoint de login"""
        url = '/api/v1/usuarios/login/'
        data = {
            'email': 'admin@example.com',
            'password': 'admin123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
    
    def test_login_invalid_credentials(self):
        """Testa login com credenciais inválidas"""
        url = '/api/v1/usuarios/login/'
        data = {
            'email': 'admin@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_current_user(self):
        """Testa endpoint de usuário atual"""
        self.client.force_authenticate(user=self.admin)
        url = '/api/v1/usuarios/me/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'admin@example.com')
    
    def test_change_password(self):
        """Testa alteração de senha"""
        self.client.force_authenticate(user=self.user)
        url = '/api/v1/usuarios/change_password/'
        data = {
            'old_password': 'user123',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar se senha foi alterada
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))
    
    def test_list_usuarios_requires_auth(self):
        """Testa que listagem de usuários requer autenticação"""
        url = '/api/v1/usuarios/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GerenteAPITest(APITestCase):
    """Testes para API de gerentes"""
    
    def setUp(self):
        self.client = APIClient()
        self.admin = Usuario.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.client.force_authenticate(user=self.admin)
    
    def test_create_gerente(self):
        """Testa criação de gerente via API"""
        url = '/api/v1/gerentes/'
        data = {
            'email': 'gerente@example.com',
            'password': 'senha123',
            'nome': 'Maria Silva',
            'cpf': '12345678901',
            'telefone': '11999999999'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Gerente.objects.count(), 1)
        gerente = Gerente.objects.first()
        self.assertEqual(gerente.nome, 'Maria Silva')
    
    def test_list_gerentes(self):
        """Testa listagem de gerentes"""
        usuario = Usuario.objects.create_user(
            email='gerente@example.com',
            password='senha123',
            tipo_usuario='gerente'
        )
        Gerente.objects.create(
            usuario=usuario,
            nome='João Silva',
            cpf='12345678901'
        )
        
        url = '/api/v1/gerentes/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

