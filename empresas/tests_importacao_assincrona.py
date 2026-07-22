import io
from unittest.mock import patch

import openpyxl
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from empresas.models import Empresa, ImportacaoProfissionais, Profissional
from empresas.tasks import processar_importacao_profissionais
from usuarios.models import Gerente, Usuario


def arquivo_excel(linhas):
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(['Nome', 'CPF', 'Email'])
    for linha in linhas:
        worksheet.append(linha)
    stream = io.BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return SimpleUploadedFile(
        'profissionais.xlsx',
        stream.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )


class ImportacaoProfissionaisAssincronaTest(TestCase):
    def setUp(self):
        self.gerente_usuario = Usuario.objects.create_user(
            email='gerente@example.com', password='senha', tipo_usuario='gerente'
        )
        Gerente.objects.create(usuario=self.gerente_usuario, nome='Gerente Teste', cpf='12345678901')
        empresa_usuario = Usuario.objects.create_user(
            email='empresa@example.com', password='senha', tipo_usuario='empresa'
        )
        self.empresa = Empresa.objects.create(
            usuario=empresa_usuario,
            razao_social='Empresa Teste',
            cnpj='12345678000199',
            url_personalizada='empresa-teste',
        )
        self.client.force_login(self.gerente_usuario)
        session = self.client.session
        session['access_token'] = 'token-de-teste'
        session.save()

    @patch('usuarios.web_views.processar_importacao_profissionais.delay')
    def test_post_de_importacao_retorna_job_enfileirado_sem_processar_arquivo(self, delay):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse('web-gerente:profissional-import', kwargs={'empresa_pk': self.empresa.pk}),
                {'arquivo': arquivo_excel([['Ana', '12345678909', '-']])},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            )

        self.assertEqual(response.status_code, 202)
        payload = response.json()
        job = ImportacaoProfissionais.objects.get(pk=payload['importacao_id'])
        self.assertEqual(job.status, ImportacaoProfissionais.Status.AGUARDANDO)
        self.assertEqual(Profissional.objects.count(), 0)
        self.assertTrue(delay.called)

    @patch('empresas.tasks.make_password', return_value=make_password('senha-temporaria'))
    def test_task_processa_750_linhas_e_registra_resultado_consultavel(self, _make_password):
        linhas = [
            [f'Profissional {indice}', f'{indice:011d}', '-']
            for indice in range(1, 751)
        ]
        job = ImportacaoProfissionais.objects.create(
            empresa=self.empresa,
            solicitada_por=self.gerente_usuario,
            arquivo=arquivo_excel(linhas),
        )

        processar_importacao_profissionais(job.pk)

        job.refresh_from_db()
        self.assertEqual(job.status, ImportacaoProfissionais.Status.CONCLUIDA)
        self.assertEqual(job.total_importados, 750)
        self.assertEqual(job.total_erros, 0)
        self.assertEqual(Profissional.objects.filter(empresa=self.empresa).count(), 750)
