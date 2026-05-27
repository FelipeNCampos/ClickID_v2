"""
Views públicas para páginas de empresas
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Empresa
from datetime import datetime


def empresa_public_page(request, url_personalizada):
    """Página pública da empresa - Login de profissionais"""
    
    try:
        # Buscar empresa pela URL personalizada
        empresa = Empresa.objects.filter(url_personalizada=url_personalizada).first()
        
        if not empresa:
            return render(request, '404.html', status=404)
        
        # Se já estiver logado como profissional, redirecionar para dashboard
        if 'prof_access_token' in request.session:
            return redirect('profissional:dashboard')
        
        # Se for POST, processar login
        if request.method == 'POST':
            cpf = request.POST.get('cpf', '').replace('.', '').replace('-', '').replace('/', '').strip()
            senha = request.POST.get('senha', '').strip()
            
            if not cpf or not senha:
                messages.error(request, 'CPF e senha são obrigatórios')
            else:
                # Fazer login via API de profissional
                try:
                    # Verificar se profissional existe e pertence à empresa
                    from .models import Profissional
                    try:
                        profissional = Profissional.objects.select_related('usuario').get(
                            cpf=cpf,
                            empresa=empresa,
                            is_active=True
                        )
                    except Profissional.DoesNotExist:
                        messages.error(request, 'CPF ou senha inválidos')
                        return render(request, 'empresas/public_login.html', {
                            'empresa': empresa,
                            'current_year': datetime.now().year
                        })

                    # Tentar autenticar localmente usando o email do usuário (evita chamadas HTTP internas)
                    from django.contrib.auth import authenticate, login
                    from rest_framework_simplejwt.tokens import RefreshToken

                    try:
                        email = profissional.usuario.email
                        user = authenticate(request, username=email, password=senha)
                        if user is not None and getattr(user, 'tipo_usuario', '') == 'profissional':
                            # Login Django (session)
                            login(request, user)
                            refresh = RefreshToken.for_user(user)
                            request.session['prof_access_token'] = str(refresh.access_token)
                            request.session['prof_refresh_token'] = str(refresh)
                            request.session['prof_user_id'] = str(profissional.usuario.pk)
                            request.session['prof_cpf'] = cpf
                            request.session['prof_empresa_id'] = str(empresa.usuario.pk)
                            request.session['prof_empresa_url'] = empresa.url_personalizada
                            return redirect('profissional:dashboard')
                        else:
                            messages.error(request, 'CPF ou senha inválidos')
                    except Exception:
                        messages.error(request, 'CPF ou senha inválidos')
                except Exception as e:
                    messages.error(request, f'Erro ao processar login: {str(e)}')
        
        # Renderizar página de login
        context = {
            'empresa': empresa,
            'current_year': datetime.now().year
        }
        
        return render(request, 'empresas/public_login.html', context)
        
    except Exception as e:
        messages.error(request, f'Erro ao carregar página: {str(e)}')
        return render(request, '404.html', status=404)
