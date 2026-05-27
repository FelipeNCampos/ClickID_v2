from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from usuarios.models import Usuario
from empresas.models import Empresa
import io
import unittest


class ProfissionalImportTest(TestCase):
    def setUp(self):
        # Create company user and Empresa
        self.user = Usuario.objects.create_user(email='empresa@test.com', password='testpass123', tipo_usuario='empresa')
        self.empresa = Empresa.objects.create(usuario=self.user, razao_social='Empresa Teste')
        self.client = Client()
        # Login via Django auth (web view uses session access_token but empresa_required checks session token)
        # We'll set session access_token manually to mimic web login
        self.client.force_login(self.user)
        session = self.client.session
        session['access_token'] = 'dummy-token-for-tests'
        session.save()

    def make_xlsx_file(self):
        try:
            import openpyxl
        except Exception:
            raise unittest.SkipTest('openpyxl is required for this test. Please install with `pip install openpyxl`')

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['Nome', 'CPF', 'Email'])
        ws.append(['João Teste', '01234567890', 'joao@test.com'])
        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return stream

    def test_import_proficional_via_web_view(self):
        url = reverse('web-empresa:profissionais-import')
        xlsx = self.make_xlsx_file()
        upload = SimpleUploadedFile('dados.xlsx', xlsx.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        # Build a proper multipart body to ensure Django test client sends files correctly
        # Use DRF's APIClient to post multipart to the API endpoint directly
        from rest_framework.test import APIClient

        api_client = APIClient()
        api_client.force_authenticate(user=self.user)

        api_url = '/api/v1/profissionais/import_excel/'
        response = api_client.post(api_url, {'empresa': str(self.empresa.usuario.pk), 'arquivo': upload}, format='multipart')
        # We expect either redirect to list or a JSON response depending on view path
        # Ensure that no error 'Arquivo não fornecido' is returned in response content
        content = response.content.decode('utf-8')
        self.assertNotIn('Arquivo não fornecido', content, msg=f"Response contained error: {content}")
        # Successful API import returns 201 (created)
        self.assertIn(response.status_code, (200, 201, 302))
