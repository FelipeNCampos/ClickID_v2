import os, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE','clickid_core.settings')
import django
django.setup()
from django.test import RequestFactory
from django.contrib.sessions.backends.db import SessionStore
from empresas.web_views_profissional import profissional_coleta_preencher
from coletas.models import ColetaProfissional, RespostaColeta
from django.core.files.storage import default_storage

# 1x1 transparent PNG
png_base64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII='
data_uri = 'data:image/png;base64,' + png_base64

rf = RequestFactory()
# Prefer a coleta_profissional that requires both photo and signature
cp = ColetaProfissional.objects.filter(coleta__include_foto=True, coleta__include_assinatura=True).select_related('profissional','coleta').first()
if not cp:
    cp = ColetaProfissional.objects.select_related('profissional','coleta').first()
    if not cp:
        print('NO_COLETA_PROFISSIONAL_FOUND')
        raise SystemExit(1)

print('Using ColetaProfissional:', cp.pk, 'Coleta:', cp.coleta.pk)

url = f'/profissional/coletas/{cp.id}/preencher/'
req = rf.post(url, data=json.dumps({'foto': data_uri, 'assinatura': data_uri, 'respostas': {}}), content_type='application/json')
# Prepare session expected by decorator
session = SessionStore()
session['prof_access_token'] = 'test-token'
session['prof_user_id'] = str(cp.profissional.usuario.pk)
session.create()
req.session = session
req.META['REMOTE_ADDR'] = '127.0.0.1'
# Attach user if possible
try:
    # Try to set request.user to profissional.usuario
    req.user = cp.profissional.usuario
except Exception:
    pass

# Call the view
resp = profissional_coleta_preencher(req, str(cp.id))
print('Response type:', type(resp))
try:
    content = resp.content.decode('utf-8')
    print('Response content:', content)
except Exception:
    print('No content to decode')

# Inspect RespostaColeta and related files
try:
    resposta = RespostaColeta.objects.get(coleta_profissional=cp)
    print('RespostaColeta found:', resposta.pk)
    # Foto
    try:
        foto = resposta.foto
        print('Foto object:', getattr(foto, 'arquivo', None))
        if foto.arquivo and default_storage.exists(foto.arquivo.name):
            print('Foto saved at:', foto.arquivo.name, 'size:', foto.arquivo.size)
        else:
            print('Foto file not found in storage')
    except Exception as e:
        print('No Foto object or error:', e)
    # Assinatura
    try:
        assinatura = resposta.assinatura
        print('Assinatura object:', getattr(assinatura, 'arquivo', None))
        if assinatura.arquivo and default_storage.exists(assinatura.arquivo.name):
            print('Assinatura saved at:', assinatura.arquivo.name, 'size:', assinatura.arquivo.size)
        else:
            print('Assinatura file not found in storage')
    except Exception as e:
        print('No Assinatura object or error:', e)
except Exception as e:
    print('RespostaColeta not found or error:', e)

print('Test finished')
