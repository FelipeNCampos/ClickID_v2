import os
import sys
import pathlib
import django
import json
import logging

# Prepare project path
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clickid_core.settings')
django.setup()

from coletas.models import ColetaProfissional
from modelos.models import CampoCartao
from coletas.serializers import RespostaColetaCreateSerializer

# Setup logger to also write to logs/clickid.log
logger = logging.getLogger('django')
logger.setLevel(logging.DEBUG)
try:
    fh = logging.FileHandler(PROJECT_ROOT / 'logs' / 'clickid.log')
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)
except Exception as e:
    print('Could not attach file handler to logger:', e)

# Find a ColetaProfissional
cp = ColetaProfissional.objects.first()
if not cp:
    print('No ColetaProfissional found in DB')
    sys.exit(1)

# Find a texto field for the coleta's modelo
modelo = cp.coleta.modelo
campo = None
if modelo:
    try:
        campo = CampoCartao.objects.filter(modelo=modelo).exclude(tipo__in=['foto','assinatura']).first()
    except Exception:
        campo = None

if not campo:
    print('No suitable CampoCartao (texto) found for coleta.modelo')
    sys.exit(1)

payload = {
    'coleta_profissional_id': str(cp.id),
    'respostas': [
        {
            'campo_id': str(campo.id),
            'valor': 'Teste manual via script'
        }
    ]
}

logger.info('Teste manual payload: %s', json.dumps(payload, ensure_ascii=False))

serializer = RespostaColetaCreateSerializer(data=payload)
if not serializer.is_valid():
    logger.error('Serializer validation errors: %s', json.dumps(serializer.errors, ensure_ascii=False, default=str))
    print('Serializer invalid. Errors:')
    print(serializer.errors)
    sys.exit(1)

resposta = serializer.save()
logger.info('Resposta criada via script: %s', str(resposta.id))
print('Created RespostaColeta id:', resposta.id)
print('Respostas campos count:', resposta.respostas_campos.count())
for rc in resposta.respostas_campos.all():
    print('campo:', rc.campo_id, 'valor_texto:', rc.valor_texto)
