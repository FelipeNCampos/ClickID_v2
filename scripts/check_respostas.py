import os
import sys
import pathlib
import django
import json

# Ensure project root is on sys.path so Django settings can be imported
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clickid_core.settings')
django.setup()

from coletas.models import RespostaCampo

qs = RespostaCampo.objects.all().order_by('-id')[:50]
out = []
for r in qs:
    out.append({
        'id': str(r.id),
        'campo_id': str(r.campo_id) if r.campo_id else None,
        'resposta_coleta_id': str(r.resposta_coleta_id) if r.resposta_coleta_id else None,
        'valor_texto': r.valor_texto,
        'valor_numero': str(r.valor_numero) if r.valor_numero is not None else None,
        'valor_data': r.valor_data.isoformat() if r.valor_data else None,
        'valor_json': r.valor_json
    })

print(json.dumps(out, ensure_ascii=False, indent=2))
