"""
Testes para o app dashboard
"""
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from usuarios.models import Usuario
from empresas.models import Empresa
from .models import Dashboard, Relatorio, Estatistica, Alerta


class DashboardModelTest(TestCase):
    """Testes para o modelo Dashboard"""
    
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
    
    def test_create_dashboard(self):
        """Testa criação de dashboard"""
        dashboard = Dashboard.objects.create(
            empresa=self.empresa,
            nome='Dashboard Principal',
            descricao='Dashboard de análise de coletas'
        )
        self.assertEqual(dashboard.nome, 'Dashboard Principal')
        self.assertIn('Dashboard Principal', str(dashboard))
    
    def test_dashboard_widgets(self):
        """Testa configuração de widgets"""
        dashboard = Dashboard.objects.create(
            empresa=self.empresa,
            nome='Dashboard Teste',
            widgets={
                'total_coletas': True,
                'taxa_conclusao': True,
                'grafico_tempo': False
            }
        )
        self.assertTrue(dashboard.widgets['total_coletas'])
        self.assertFalse(dashboard.widgets['grafico_tempo'])


class RelatorioModelTest(TestCase):
    """Testes para o modelo Relatorio"""
    
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
        self.dashboard = Dashboard.objects.create(
            empresa=self.empresa,
            nome='Dashboard Teste'
        )
    
    def test_create_relatorio(self):
        """Testa criação de relatório"""
        relatorio = Relatorio.objects.create(
            dashboard=self.dashboard,
            titulo='Relatório Mensal',
            tipo='coletas',
            formato='pdf'
        )
        self.assertEqual(relatorio.status, 'pendente')
        self.assertEqual(relatorio.formato, 'pdf')
    
    def test_relatorio_status_transitions(self):
        """Testa transições de status do relatório"""
        relatorio = Relatorio.objects.create(
            dashboard=self.dashboard,
            titulo='Relatório Teste',
            tipo='profissionais'
        )
        
        relatorio.status = 'gerando'
        relatorio.save()
        self.assertEqual(relatorio.status, 'gerando')
        
        relatorio.status = 'concluido'
        relatorio.save()
        self.assertEqual(relatorio.status, 'concluido')


class EstatisticaModelTest(TestCase):
    """Testes para o modelo Estatistica"""
    
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
        self.dashboard = Dashboard.objects.create(
            empresa=empresa,
            nome='Dashboard Teste'
        )
    
    def test_create_estatistica(self):
        """Testa criação de estatística"""
        estatistica = Estatistica.objects.create(
            dashboard=self.dashboard,
            nome='Taxa de Conclusão',
            tipo='percentual',
            valor=75.5
        )
        self.assertEqual(estatistica.valor, 75.5)
        self.assertEqual(estatistica.tipo, 'percentual')
    
    def test_estatistica_metadata(self):
        """Testa metadata da estatística"""
        estatistica = Estatistica.objects.create(
            dashboard=self.dashboard,
            nome='Total Coletas',
            tipo='contador',
            valor=150,
            metadata={
                'periodo': 'mensal',
                'ano': 2024,
                'mes': 12
            }
        )
        self.assertEqual(estatistica.metadata['periodo'], 'mensal')


class AlertaModelTest(TestCase):
    """Testes para o modelo Alerta"""
    
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
        self.dashboard = Dashboard.objects.create(
            empresa=empresa,
            nome='Dashboard Teste'
        )
    
    def test_create_alerta(self):
        """Testa criação de alerta"""
        alerta = Alerta.objects.create(
            dashboard=self.dashboard,
            titulo='Prazo próximo ao vencimento',
            mensagem='A coleta X vence em 2 dias',
            tipo='warning'
        )
        self.assertFalse(alerta.lido)
        self.assertEqual(alerta.tipo, 'warning')
    
    def test_marcar_alerta_como_lido(self):
        """Testa marcar alerta como lido"""
        alerta = Alerta.objects.create(
            dashboard=self.dashboard,
            titulo='Alerta Teste',
            mensagem='Mensagem de teste'
        )
        
        alerta.lido = True
        alerta.save()
        self.assertTrue(alerta.lido)


class DashboardAPITest(APITestCase):
    """Testes para API de dashboard"""
    
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
    
    def test_create_dashboard(self):
        """Testa criação de dashboard via API"""
        url = '/api/v1/dashboards/'
        data = {
            'empresa': str(self.empresa.usuario.id),
            'nome': 'Novo Dashboard',
            'descricao': 'Dashboard de análise'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_get_estatisticas(self):
        """Testa endpoint de estatísticas"""
        dashboard = Dashboard.objects.create(
            empresa=self.empresa,
            nome='Dashboard Teste'
        )
        Estatistica.objects.create(
            dashboard=dashboard,
            nome='Total',
            tipo='contador',
            valor=100
        )
        
        url = f'/api/v1/dashboards/{dashboard.id}/estatisticas/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class RelatorioAPITest(APITestCase):
    """Testes para API de relatórios"""
    
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
        self.dashboard = Dashboard.objects.create(
            empresa=empresa,
            nome='Dashboard Teste'
        )
        self.client.force_authenticate(user=usuario_empresa)
    
    def test_create_relatorio(self):
        """Testa criação de relatório"""
        url = '/api/v1/relatorios/'
        data = {
            'dashboard': str(self.dashboard.id),
            'titulo': 'Relatório Teste',
            'tipo': 'coletas',
            'formato': 'pdf'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_gerar_relatorio(self):
        """Testa geração de relatório"""
        relatorio = Relatorio.objects.create(
            dashboard=self.dashboard,
            titulo='Relatório Teste',
            tipo='profissionais'
        )
        
        url = f'/api/v1/relatorios/{relatorio.id}/gerar/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_download_relatorio(self):
        """Testa download de relatório"""
        relatorio = Relatorio.objects.create(
            dashboard=self.dashboard,
            titulo='Relatório Teste',
            tipo='coletas',
            status='concluido'
        )
        
        url = f'/api/v1/relatorios/{relatorio.id}/download/'
        response = self.client.get(url)
        # Download pode retornar 200 com arquivo ou mensagem
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])


class AlertaAPITest(APITestCase):
    """Testes para API de alertas"""
    
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
        self.dashboard = Dashboard.objects.create(
            empresa=empresa,
            nome='Dashboard Teste'
        )
        self.client.force_authenticate(user=usuario_empresa)
    
    def test_list_alertas_nao_lidos(self):
        """Testa listagem de alertas não lidos"""
        Alerta.objects.create(
            dashboard=self.dashboard,
            titulo='Alerta 1',
            mensagem='Mensagem 1',
            lido=False
        )
        Alerta.objects.create(
            dashboard=self.dashboard,
            titulo='Alerta 2',
            mensagem='Mensagem 2',
            lido=True
        )
        
        url = '/api/v1/alertas/?lido=false'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_marcar_como_lido(self):
        """Testa marcar alerta como lido"""
        alerta = Alerta.objects.create(
            dashboard=self.dashboard,
            titulo='Alerta Teste',
            mensagem='Mensagem teste',
            lido=False
        )
        
        url = f'/api/v1/alertas/{alerta.id}/marcar_lido/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        alerta.refresh_from_db()
        self.assertTrue(alerta.lido)
    
    def test_marcar_todos_como_lido(self):
        """Testa marcar todos os alertas como lidos"""
        Alerta.objects.create(
            dashboard=self.dashboard,
            titulo='Alerta 1',
            mensagem='Mensagem 1',
            lido=False
        )
        Alerta.objects.create(
            dashboard=self.dashboard,
            titulo='Alerta 2',
            mensagem='Mensagem 2',
            lido=False
        )
        
        url = '/api/v1/alertas/marcar_todos_lido/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        alertas_nao_lidos = Alerta.objects.filter(lido=False).count()
        self.assertEqual(alertas_nao_lidos, 0)

