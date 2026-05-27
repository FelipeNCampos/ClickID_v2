"""
Script para testar login de profissional
"""
import os
import sys

# Adicionar o diretório raiz ao path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clickid_core.settings')

import django
django.setup()

from empresas.models import Profissional
from django.contrib.auth import authenticate

cpf = '533.463.601-30'
cpf_sem_pontos = cpf.replace('.', '').replace('-', '')
senha = '0130'

print(f"Testando login com CPF: {cpf}")
print(f"CPF sem pontos: {cpf_sem_pontos}")
print(f"Senha: {senha}")
print("-" * 50)

# Verificar se profissional existe
try:
    profissional = Profissional.objects.select_related('usuario').get(cpf=cpf_sem_pontos)
    print(f"✅ Profissional encontrado!")
    print(f"   Nome: {profissional.nome}")
    print(f"   Email: {profissional.usuario.email}")
    print(f"   Ativo: {profissional.is_active}")
    print(f"   Usuário ativo: {profissional.usuario.is_active}")
    print(f"   Tipo: {profissional.usuario.tipo_usuario}")
    print("-" * 50)
    
    # Testar autenticação
    user = authenticate(username=profissional.usuario.email, password=senha)
    if user:
        print(f"✅ Autenticação bem-sucedida!")
        print(f"   User ID: {user.id}")
        print(f"   Email: {user.email}")
    else:
        print(f"❌ Autenticação falhou!")
        print(f"   Tentando verificar a senha diretamente...")
        if profissional.usuario.check_password(senha):
            print(f"   ✅ Senha está correta (check_password)")
        else:
            print(f"   ❌ Senha incorreta")
            print(f"   Tentando resetar senha para: {senha}")
            profissional.usuario.set_password(senha)
            profissional.usuario.save()
            print(f"   ✅ Senha resetada!")
            
except Profissional.DoesNotExist:
    print(f"❌ Profissional com CPF {cpf_sem_pontos} não encontrado")
    print("\nBuscando profissionais cadastrados:")
    profissionais = Profissional.objects.all()[:5]
    for p in profissionais:
        print(f"   - {p.nome} | CPF: {p.cpf}")
