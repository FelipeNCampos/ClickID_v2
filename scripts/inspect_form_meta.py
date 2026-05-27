import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','clickid_core.settings')
import django
django.setup()
from django.test import RequestFactory
from django.contrib.sessions.backends.db import SessionStore
from empresas.web_views_profissional import profissional_coleta_preencher
from coletas.models import ColetaProfissional

rf = RequestFactory()
cp = ColetaProfissional.objects.first()
if not cp:
    print('NO_COLETA_PROFISSIONAL')
    raise SystemExit(0)
req = rf.get(f'/profissional/coletas/{cp.id}/preencher/')
# prepare session
session = SessionStore()
session['prof_access_token'] = 'fake-token'
session['prof_user_id'] = str(cp.profissional.usuario.pk)
session.create()
req.session = session
req.META['REMOTE_ADDR'] = '127.0.0.1'
# Call view
resp = profissional_coleta_preencher(req, str(cp.id))
if hasattr(resp, 'content'):
    content = resp.content.decode('utf-8')
    print('LEN:', len(content))
    print('HAS_FORM_META:', 'id="form-meta"' in content)
    idx = content.find('id="form-meta"')
    if idx!=-1:
        print(content[max(0,idx-200):idx+200])
else:
    print('Response has no content or is redirect:', type(resp), getattr(resp,'status_code',None))
