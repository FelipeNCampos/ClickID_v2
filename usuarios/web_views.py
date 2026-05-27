"""
Views web para gerente
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from functools import wraps
from empresas.models import Empresa, Departamento, Profissional
from empresas import serializers as empresas_serializers
from usuarios.models import LogAuditoria
from coletas.models import Coleta
from auditoria.models import LogAuditoria as AuditoriaLog
from django.db import models
import logging
import time
from django.db.utils import InterfaceError
from rest_framework_simplejwt.tokens import RefreshToken
logger = logging.getLogger(__name__)


def _mask_token(tkn: str) -> str:
    if not tkn:
        return ''
    try:
        return f"{tkn[:8]}..."
    except Exception:
        return '***'


def token_required(view_func):
    """Decorator para verificar se usuário tem token JWT na sessão"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        token = request.session.get('access_token')
        logger.debug('token_required: access_token present=%s token_prefix=%s', bool(token), _mask_token(token))
        if not token:
            messages.warning(request, 'Você precisa fazer login primeiro')
            return redirect('web-gerente:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def gerente_required(view_func):
    """Decorator para garantir que apenas gerentes acessem rotas administrativas"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        token = request.session.get('access_token')
        logger.debug('gerente_required: access_token present=%s token_prefix=%s', bool(token), _mask_token(token))
        if not token:
            messages.warning(request, 'Você precisa fazer login primeiro')
            return redirect('web-gerente:login')
        
        # Verificar se o usuário é gerente
        if request.user.is_authenticated and request.user.tipo_usuario != 'gerente':
            messages.error(request, 'Acesso negado. Área restrita para gerentes.')
            return redirect('web-empresa:dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def home(request):
    """Página inicial - redireciona conforme tipo de usuário"""
    if request.user.is_authenticated:
        if request.user.tipo_usuario == 'gerente':
            return redirect('web-gerente:dashboard')
        elif request.user.tipo_usuario == 'empresa':
            return redirect('web-empresa:dashboard')
    return redirect('web-gerente:login')


def login_view(request):
    """Página de login"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Medição de tempo para diagnosticar operações lentas
        start_total = time.monotonic()

        # Autenticar o usuário com Django
        t0 = time.monotonic()
        user = authenticate(request, username=email, password=password)
        t1 = time.monotonic()
        logger.info('login_view: authenticate time=%.3fs email=%s user=%s', t1 - t0, email, getattr(user, 'id', None))
        
        if user is not None:
            # Verificar se é empresa e se está ativa
            if user.tipo_usuario == 'empresa':
                try:
                    from empresas.models import Empresa
                    empresa = Empresa.objects.get(usuario=user)
                    if not empresa.is_active:
                        messages.error(request, 'Sua empresa está desativada. Entre em contato com o administrador.')
                        return render(request, 'usuarios/login.html')
                except Empresa.DoesNotExist:
                    messages.error(request, 'Empresa não encontrada.')
                    return render(request, 'usuarios/login.html')
            
            # Fazer login do usuário no Django
            t2 = time.monotonic()
            login(request, user)
            t3 = time.monotonic()
            logger.info('login_view: django.login time=%.3fs email=%s', t3 - t2, email)
            
            # Gerar tokens JWT localmente para evitar chamada HTTP interna
            try:
                t4 = time.monotonic()
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)
                request.session['access_token'] = access_token
                request.session['refresh_token'] = refresh_token
                request.session['user_email'] = email
                t5 = time.monotonic()
                logger.info('login_view: token generation time=%.3fs email=%s', t5 - t4, email)
                logger.debug('login_view: created access_token token_prefix=%s for user=%s', _mask_token(access_token), email)
            except Exception as e:
                logger.exception('login_view: failed to create JWT tokens: %s', e)
            
            # Redirecionar conforme tipo de usuário
            end_total = time.monotonic()
            logger.info('login_view: total time=%.3fs email=%s', end_total - start_total, email)
            if user.tipo_usuario == 'gerente':
                return redirect('web-gerente:dashboard')
            elif user.tipo_usuario == 'empresa':
                return redirect('web-empresa:dashboard')
        else:
            messages.error(request, 'Email ou senha inválidos')
            logger.info('login_view: invalid credentials for email=%s', email)
    
    return render(request, 'usuarios/login.html')


def logout_view(request):
    """Logout"""
    logout(request)
    request.session.flush()
    messages.success(request, 'Logout realizado com sucesso')
    return redirect('web-gerente:login')


@gerente_required
def gerente_dashboard(request):
    """Dashboard do gerente"""
    try:
        empresas_qs = Empresa.objects.all()
        coletas_qs = Coleta.objects.all()
        logs_qs = AuditoriaLog.objects.all().order_by('-data_hora')

        # Use serializers to render objects to dicts for templates
        empresas_ser = empresas_serializers.EmpresaListSerializer(empresas_qs, many=True, context={'request': request})
        empresas = empresas_ser.data

        # Users: count usuarios via Usuario model for accurate counts
        from usuarios.models import Usuario
        usuarios = list(Usuario.objects.all().values('id', 'email', 'tipo_usuario'))
        gerentes = [u for u in usuarios if u.get('tipo_usuario') == 'gerente']

        coletas = list(coletas_qs.values('id', 'nome', 'empresa', 'status'))
        logs = list(logs_qs.values('usuario_nome', 'tipo_acao', 'descricao', 'data_hora')[:10])

        context = {
            'total_empresas': empresas_qs.count(),
            'total_usuarios': len(usuarios),
            'total_gerentes': len(gerentes),
            'total_coletas': coletas_qs.count(),
            'empresas_recentes': empresas[:5],
            'logs_recentes': logs,
        }
    except InterfaceError as ie:
        logger.exception('Database InterfaceError in gerente_dashboard: %s', ie)
        messages.error(request, 'Erro de conexão com o banco de dados. Por favor, tente novamente mais tarde.')
        context = {
            'total_empresas': 0,
            'total_usuarios': 0,
            'total_gerentes': 0,
            'total_coletas': 0,
            'empresas_recentes': [],
            'logs_recentes': [],
        }
    except Exception as e:
        messages.error(request, f'Erro ao carregar dados: {str(e)}')
        context = {
            'total_empresas': 0,
            'total_usuarios': 0,
            'total_gerentes': 0,
            'total_coletas': 0,
            'empresas_recentes': [],
            'logs_recentes': [],
        }
    
    return render(request, 'usuarios/gerente_dashboard.html', context)


@gerente_required
def empresas_list(request):
    """Lista de empresas"""
    # Obter filtros
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')

    try:
        qs = Empresa.objects.all()
        if status_filter == 'ativo':
            qs = qs.filter(is_active=True)
        elif status_filter == 'inativo':
            qs = qs.filter(is_active=False)

        if search:
            qs = qs.filter(models.Q(razao_social__icontains=search) | models.Q(cnpj__icontains=search))

        serializer = empresas_serializers.EmpresaListSerializer(qs, many=True, context={'request': request})
        empresas = serializer.data
    except InterfaceError as ie:
        logger.exception('Database InterfaceError in empresas_list: %s', ie)
        messages.error(request, 'Erro de conexão com o banco de dados. Por favor, tente novamente mais tarde.')
        empresas = []
    except Exception as e:
        messages.error(request, f'Erro ao carregar empresas: {str(e)}')
        empresas = []
    
    # Aplicar filtro local se a API não suportar
    if search and empresas:
        empresas = [
            e for e in empresas 
            if search.lower() in e.get('razao_social', '').lower() 
            or search.lower() in e.get('cnpj', '').lower()
        ]
    
    # Paginação
    paginator = Paginator(empresas, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search': search
    }
    return render(request, 'usuarios/empresas_list.html', context)


@gerente_required
def empresa_create(request):
    """Criar nova empresa"""
    if request.method == 'POST':
        data = {
            'email': request.POST.get('email'),
            'password': request.POST.get('password'),
            'razao_social': request.POST.get('razao_social'),
            'cnpj': request.POST.get('cnpj'),
            'telefone': request.POST.get('telefone'),
            'url_personalizada': request.POST.get('url_personalizada'),
        }

        # Construir serializer e salvar diretamente
        try:
            # Serializador aceita 'logo' como arquivo field
            serializer = empresas_serializers.EmpresaSerializer(data=data, context={'request': request})
            if 'logo' in request.FILES:
                # attach file to serializer.validated_data via manual handling
                # DRF serializers handle files through request.data, but here we'll set after is_valid
                pass

            if serializer.is_valid():
                empresa = serializer.save()
                # If logo was provided, update it
                if 'logo' in request.FILES:
                    empresa.logo = request.FILES['logo']
                    empresa.save()

                messages.success(request, 'Empresa criada com sucesso!')
                return redirect('web-gerente:empresas-list')
            else:
                # Tratar erros do serializer para exibir mensagens amigáveis
                errors = serializer.errors
                if 'cnpj' in errors:
                    messages.error(request, 'Já existe uma empresa cadastrada com este CNPJ.')
                else:
                    parts = []
                    for field, val in errors.items():
                        if isinstance(val, list):
                            parts.append(f"{field}: {', '.join(str(x) for x in val)}")
                        else:
                            parts.append(f"{field}: {val}")
                    messages.error(request, 'Erro ao criar empresa: ' + '; '.join(parts))
        except InterfaceError as ie:
            logger.exception('Database InterfaceError in empresa_create: %s', ie)
            messages.error(request, 'Erro de conexão com o banco de dados. Por favor, tente novamente mais tarde.')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    
    return render(request, 'usuarios/empresa_form.html', {'action': 'Criar'})


@gerente_required
def empresa_detail(request, pk):
    """Detalhes da empresa"""
    try:
        empresa_obj = get_object_or_404(Empresa, usuario__id=pk) if isinstance(pk, str) else get_object_or_404(Empresa, usuario__id=pk)

        empresa_ser = empresas_serializers.EmpresaSerializer(empresa_obj, context={'request': request})
        empresa = empresa_ser.data

        # Departamentos
        departamentos_qs = Departamento.objects.filter(empresa=empresa_obj)
        dept_ser = empresas_serializers.DepartamentoListSerializer(departamentos_qs, many=True)
        departamentos = dept_ser.data

        # Profissionais
        prof_qs = Profissional.objects.filter(empresa=empresa_obj)
        prof_ser = empresas_serializers.ProfissionalListSerializer(prof_qs, many=True)
        profissionais = prof_ser.data

        # Modelos (usar modelos.serializers)
        from modelos.models import ModeloCartao
        from modelos.serializers import ModeloCartaoListSerializer
        modelos_qs = ModeloCartao.objects.filter(empresa=empresa_obj)
        modelos_ser = ModeloCartaoListSerializer(modelos_qs, many=True)
        modelos = modelos_ser.data

        # Adicionar listas ao contexto
        empresa['departamentos'] = departamentos
        empresa['profissionais'] = profissionais
        empresa['modelos'] = modelos
        empresa['total_profissionais'] = len(profissionais)
        empresa['total_departamentos'] = len(departamentos)
        empresa['total_modelos'] = len(modelos)
    except InterfaceError as ie:
        logger.exception('Database InterfaceError in empresa_detail: %s', ie)
        messages.error(request, 'Erro de conexão com o banco de dados. Por favor, tente novamente mais tarde.')
        empresa = None
    except Exception as e:
        messages.error(request, f'Erro ao carregar empresa: {str(e)}')
        empresa = None
    
    return render(request, 'usuarios/empresa_detail.html', {'empresa': empresa})


@gerente_required
def empresa_edit(request, pk):
    """Editar empresa"""
    
    
    if request.method == 'POST':
        try:
            empresa_obj = Empresa.objects.get(usuario__id=pk)
            serializer = empresas_serializers.EmpresaSerializer(empresa_obj, data=request.POST, partial=True, context={'request': request})
            if serializer.is_valid():
                empresa = serializer.save()
                if 'logo' in request.FILES:
                    empresa.logo = request.FILES['logo']
                    empresa.save()
                messages.success(request, 'Empresa atualizada com sucesso!')
                return redirect('web-gerente:empresa-detail', pk=pk)
            else:
                messages.error(request, f'Erro ao atualizar: {serializer.errors}')
        except Empresa.DoesNotExist:
            messages.error(request, 'Empresa não encontrada.')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    
    # Buscar dados da empresa
    try:
        empresa_obj = Empresa.objects.filter(usuario__id=pk).first()
        empresa = empresas_serializers.EmpresaSerializer(empresa_obj, context={'request': request}).data if empresa_obj else None
    except:
        empresa = None
    
    return render(request, 'usuarios/empresa_form.html', {'empresa': empresa, 'action': 'Editar'})


@gerente_required
def departamento_create(request, empresa_pk):
    """Criar novo departamento"""
    if request.method == 'POST':
        data = {
            'empresa': str(empresa_pk),
            'nome': request.POST.get('nome'),
            'descricao': request.POST.get('descricao'),
        }
        try:
            serializer = empresas_serializers.DepartamentoSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                messages.success(request, 'Departamento criado com sucesso!')
                return redirect('web-gerente:empresa-detail', pk=empresa_pk)
            else:
                errors = serializer.errors
                if 'non_field_errors' in errors or 'nome' in errors:
                    messages.error(request, 'Já existe um departamento com este nome nesta empresa.')
                else:
                    messages.error(request, f'Erro ao criar departamento: {errors}')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    
    # Buscar dados da empresa
    try:
        empresa_obj = Empresa.objects.filter(usuario__id=empresa_pk).first()
        empresa = empresas_serializers.EmpresaSerializer(empresa_obj, context={'request': request}).data if empresa_obj else None
    except:
        empresa = None
    
    return render(request, 'empresas/departamento_form.html', {'empresa': empresa, 'action': 'Criar'})


@gerente_required
def departamento_detail(request, empresa_pk, pk):
    """Detalhes do departamento"""
    try:
        departamento_obj = Departamento.objects.filter(id=pk, empresa__usuario__id=empresa_pk).first()
        departamento = empresas_serializers.DepartamentoSerializer(departamento_obj, context={'request': request}).data if departamento_obj else None

        empresa_obj = Empresa.objects.filter(usuario__id=empresa_pk).first()
        empresa = empresas_serializers.EmpresaSerializer(empresa_obj, context={'request': request}).data if empresa_obj else None
    except Exception as e:
        messages.error(request, f'Erro ao carregar departamento: {str(e)}')
        departamento = None
        empresa = None
    
    return render(request, 'empresas/departamento_detail.html', {
        'departamento': departamento,
        'empresa': empresa
    })


@gerente_required
def departamento_edit(request, empresa_pk, pk):
    """Editar departamento"""
    if request.method == 'POST':
        data = {
            'nome': request.POST.get('nome'),
            'descricao': request.POST.get('descricao'),
        }
        try:
            departamento_obj = Departamento.objects.filter(id=pk, empresa__usuario__id=empresa_pk).first()
            if not departamento_obj:
                messages.error(request, 'Departamento não encontrado.')
            else:
                serializer = empresas_serializers.DepartamentoSerializer(departamento_obj, data=data, partial=True, context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                    messages.success(request, 'Departamento atualizado com sucesso!')
                    return redirect('web-gerente:empresa-detail', pk=empresa_pk)
                else:
                    errors = serializer.errors
                    if 'non_field_errors' in errors or 'nome' in errors:
                        messages.error(request, 'Já existe um departamento com este nome nesta empresa.')
                    else:
                        messages.error(request, f'Erro ao atualizar departamento: {errors}')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    
    # Buscar dados atuais
    try:
        departamento_obj = Departamento.objects.filter(id=pk, empresa__usuario__id=empresa_pk).first()
        departamento = empresas_serializers.DepartamentoSerializer(departamento_obj, context={'request': request}).data if departamento_obj else None
        empresa_obj = Empresa.objects.filter(usuario__id=empresa_pk).first()
        empresa = empresas_serializers.EmpresaSerializer(empresa_obj, context={'request': request}).data if empresa_obj else None
    except:
        departamento = None
        empresa = None
    
    return render(request, 'empresas/departamento_form.html', {
        'departamento': departamento,
        'empresa': empresa,
        'action': 'Editar'
    })


@gerente_required
def profissional_create(request, empresa_pk):
    """Criar novo profissional"""
    if request.method == 'POST':
        data = {
            'empresa': str(empresa_pk),
            'nome': request.POST.get('nome'),
            'cpf': request.POST.get('cpf').replace('.', '').replace('-', ''),
            'email': request.POST.get('email') or None,
            'departamento': request.POST.get('departamento') if request.POST.get('departamento') else None,
        }
        try:
            serializer = empresas_serializers.ProfissionalSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                messages.success(request, 'Profissional criado com sucesso!')
                return redirect('web-gerente:empresa-detail', pk=empresa_pk)
            else:
                errors = serializer.errors
                if 'cpf' in errors:
                    messages.error(request, 'Este CPF já está cadastrado no sistema.')
                else:
                    messages.error(request, f'Erro ao criar profissional: {errors}')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    
    # Buscar dados da empresa e departamentos
    try:
        empresa_obj = Empresa.objects.filter(usuario__id=empresa_pk).first()
        empresa = empresas_serializers.EmpresaSerializer(empresa_obj, context={'request': request}).data if empresa_obj else None
        departamentos_qs = Departamento.objects.filter(empresa=empresa_obj) if empresa_obj else Departamento.objects.none()
        departamentos = empresas_serializers.DepartamentoListSerializer(departamentos_qs, many=True).data
    except:
        empresa = None
        departamentos = []
    
    return render(request, 'empresas/profissional_form.html', {
        'empresa': empresa,
        'departamentos': departamentos,
        'action': 'Criar'
    })


@gerente_required
def profissional_import(request, empresa_pk):
    """Importar profissionais via Excel"""
    from django.http import JsonResponse
    from django.urls import reverse

    def build_error_payload(error_messages):
        payload = []
        for message in error_messages:
            linha = None
            erro = str(message)
            if isinstance(message, str) and message.lower().startswith('linha '):
                prefix, sep, detail = message.partition(':')
                digits = ''.join(ch for ch in prefix if ch.isdigit())
                linha = int(digits) if digits else None
                erro = detail.strip() if sep else message
            payload.append({'linha': linha, 'erro': erro})
        return payload

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    
    if request.method == 'POST' and 'arquivo' in request.FILES:
        arquivo = request.FILES['arquivo']
        departamento_id = request.POST.get('departamento')
        
        try:
            import openpyxl
            from io import BytesIO
            
            # Ler arquivo Excel
            wb = openpyxl.load_workbook(BytesIO(arquivo.read()))
            ws = wb.active
            
            profissionais_criados = []
            erros = []
            
            # Pular cabeçalho e processar linhas
            for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if not row[0]:  # Nome vazio, pular linha
                    continue
                
                nome = str(row[0]).strip() if row[0] else None
                cpf = str(row[1]).strip() if row[1] else None
                email = str(row[2]).strip() if row[2] and row[2] != '-' else None
                
                if not nome or not cpf:
                    erros.append(f"Linha {row_num}: Nome e CPF são obrigatórios")
                    continue
                
                # Limpar CPF
                cpf_limpo = ''.join(filter(str.isdigit, cpf))
                if len(cpf_limpo) != 11:
                    erros.append(f"Linha {row_num}: CPF inválido ({cpf})")
                    continue
                
                # Criar profissional via API
                data = {
                    'empresa': str(empresa_pk),
                    'nome': nome,
                    'cpf': cpf_limpo,
                    'email': email,
                    'departamento': departamento_id if departamento_id else None,
                }
                
                try:
                    serializer = empresas_serializers.ProfissionalSerializer(data=data, context={'request': request})
                    if serializer.is_valid():
                        serializer.save()
                        profissionais_criados.append(nome)
                    else:
                        err = serializer.errors
                        if 'cpf' in err:
                            erros.append(f"Linha {row_num}: CPF {cpf} já cadastrado")
                        else:
                            erros.append(f"Linha {row_num}: {err}")
                except Exception as e:
                    erros.append(f"Linha {row_num}: Erro ao criar - {str(e)}")
            
            # Mensagens de resultado
            if profissionais_criados:
                messages.success(request, f'{len(profissionais_criados)} profissional(is) importado(s) com sucesso!')
            if erros:
                for erro in erros[:5]:  # Mostrar apenas os 5 primeiros erros
                    messages.warning(request, erro)
                if len(erros) > 5:
                    messages.warning(request, f'... e mais {len(erros) - 5} erro(s)')

            if is_ajax:
                return JsonResponse({
                    'total_importados': len(profissionais_criados),
                    'total_ignorados': 0,
                    'total_erros': len(erros),
                    'erros': build_error_payload(erros),
                }, status=201)

            return redirect('web-gerente:empresa-detail', pk=empresa_pk)
            
        except Exception as e:
            if is_ajax:
                return JsonResponse({'erro': str(e)}, status=500)
            messages.error(request, f'Erro ao processar arquivo: {str(e)}')
    
    try:
        empresa_obj = Empresa.objects.filter(usuario__id=empresa_pk).first()
        empresa = empresas_serializers.EmpresaSerializer(empresa_obj, context={'request': request}).data if empresa_obj else None
        departamentos_qs = Departamento.objects.filter(empresa=empresa_obj) if empresa_obj else Departamento.objects.none()
        departamentos = empresas_serializers.DepartamentoListSerializer(departamentos_qs, many=True).data
    except:
        empresa = None
        departamentos = []
    
    return render(request, 'empresas/profissional_import.html', {
        'empresa': empresa,
        'departamentos': departamentos,
        'import_post_url': reverse('web-gerente:profissional-import', kwargs={'empresa_pk': empresa_pk}),
        'back_url': reverse('web-gerente:empresa-detail', kwargs={'pk': empresa_pk}),
        'success_url': reverse('web-gerente:empresa-detail', kwargs={'pk': empresa_pk}),
        'empresa_hidden_id': str(empresa_pk),
    })


@gerente_required
def profissional_detail(request, empresa_pk, pk):
    """Detalhes do profissional"""
    try:
        from datetime import datetime
        profissional_obj = Profissional.objects.filter(usuario__id=pk, empresa__usuario__id=empresa_pk).first()
        profissional = empresas_serializers.ProfissionalSerializer(profissional_obj, context={'request': request}).data if profissional_obj else None

        # Buscar empresa
        empresa_obj = Empresa.objects.filter(usuario__id=empresa_pk).first()
        empresa = empresas_serializers.EmpresaSerializer(empresa_obj, context={'request': request}).data if empresa_obj else None

        # Converter datas se necessário
        if profissional:
            for date_field in ['data_cadastro', 'data_primeiro_login']:
                if profissional.get(date_field) and isinstance(profissional.get(date_field), str):
                    try:
                        profissional[date_field] = datetime.fromisoformat(profissional[date_field])
                    except Exception:
                        pass
    except Exception as e:
        messages.error(request, f'Erro ao carregar profissional: {str(e)}')
        profissional = None
        empresa = None
    
    return render(request, 'empresas/profissional_detail.html', {
        'profissional': profissional,
        'empresa': empresa
    })


@gerente_required
def profissional_edit(request, empresa_pk, pk):
    """Editar profissional"""
    headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
    
    if request.method == 'POST':
        data = {
            'nome': request.POST.get('nome'),
            'cpf': request.POST.get('cpf').replace('.', '').replace('-', ''),
            'email': request.POST.get('email') or None,
            'departamento': request.POST.get('departamento') or None,
        }
        try:
            prof_obj = Profissional.objects.filter(usuario__id=pk, empresa__usuario__id=empresa_pk).first()
            if not prof_obj:
                messages.error(request, 'Profissional não encontrado.')
            else:
                serializer = empresas_serializers.ProfissionalSerializer(prof_obj, data=data, partial=True, context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                    messages.success(request, 'Profissional atualizado com sucesso!')
                    return redirect('web-gerente:empresa-detail', pk=empresa_pk)
                else:
                    errors = serializer.errors
                    if 'cpf' in errors:
                        messages.error(request, 'Este CPF já está cadastrado no sistema.')
                    else:
                        messages.error(request, f'Erro ao atualizar profissional: {errors}')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    
    # Buscar dados atuais
    try:
        prof_obj = Profissional.objects.filter(usuario__id=pk, empresa__usuario__id=empresa_pk).first()
        profissional = empresas_serializers.ProfissionalSerializer(prof_obj, context={'request': request}).data if prof_obj else None

        empresa_obj = Empresa.objects.filter(usuario__id=empresa_pk).first()
        empresa = empresas_serializers.EmpresaSerializer(empresa_obj, context={'request': request}).data if empresa_obj else None

        departamentos_qs = Departamento.objects.filter(empresa=empresa_obj) if empresa_obj else Departamento.objects.none()
        departamentos = empresas_serializers.DepartamentoListSerializer(departamentos_qs, many=True).data
    except:
        profissional = None
        empresa = None
        departamentos = []
    
    return render(request, 'empresas/profissional_form.html', {
        'profissional': profissional,
        'empresa': empresa,
        'departamentos': departamentos,
        'action': 'Editar'
    })


@gerente_required
def profissional_reset_password(request, empresa_pk, pk):
    """Resetar senha do profissional para padrão"""
    try:
        prof_obj = Profissional.objects.filter(usuario__id=pk, empresa__usuario__id=empresa_pk).first()
        if not prof_obj:
            messages.error(request, 'Profissional não encontrado.')
        else:
            senha_padrao = prof_obj.gerar_senha_padrao()
            usuario = prof_obj.usuario
            usuario.set_password(senha_padrao)
            usuario.save()
            prof_obj.senha_alterada = False
            prof_obj.save()
            messages.success(request, f'Senha resetada com sucesso! Nova senha: {senha_padrao}')
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-gerente:profissional-detail', empresa_pk=empresa_pk, pk=pk)


@gerente_required
def logs_auditoria(request):
    """Logs de auditoria"""
    try:
        from auditoria.serializers import LogAuditoriaSerializer
        logs_qs = AuditoriaLog.objects.all().order_by('-data_hora')
        logs = LogAuditoriaSerializer(logs_qs, many=True).data
    except Exception as e:
        messages.error(request, f'Erro ao carregar logs: {str(e)}')
        logs = []
    
    # Paginação
    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'usuarios/logs_auditoria.html', {'page_obj': page_obj})


@gerente_required
def empresa_toggle_active(request, pk):
    """Ativar/Desativar empresa"""
    if request.method != 'POST':
        return redirect('web-gerente:empresas-list')
    
    # Verificar de onde veio a requisição
    referer = request.META.get('HTTP_REFERER', '')
    from_detail = 'empresa-detail' in referer or f'/empresas/{pk}/' in referer

    try:
        empresa_obj = Empresa.objects.filter(usuario__id=pk).first()
        if not empresa_obj:
            messages.error(request, 'Empresa não encontrada.')
        else:
            empresa_obj.is_active = not empresa_obj.is_active
            empresa_obj.save()
            status_text = 'ativada' if empresa_obj.is_active else 'desativada'
            messages.success(request, f'Empresa {status_text} com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
    
    # Redirecionar para a página correta
    if from_detail:
        return redirect('web-gerente:empresa-detail', pk=pk)
    else:
        return redirect('web-gerente:empresas-list')


@gerente_required
def profissional_toggle_active(request, empresa_pk, pk):
    """Ativar/Desativar profissional"""
    if request.method != 'POST':
        return redirect('web-gerente:empresa-detail', pk=empresa_pk)
    
    try:
        prof_obj = Profissional.objects.filter(usuario__id=pk, empresa__usuario__id=empresa_pk).first()
        if not prof_obj:
            messages.error(request, 'Profissional não encontrado.')
        else:
            prof_obj.is_active = not prof_obj.is_active
            prof_obj.save()
            status_text = 'ativado' if prof_obj.is_active else 'desativado'
            messages.success(request, f'Profissional {status_text} com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-gerente:empresa-detail', pk=empresa_pk)


@gerente_required
def profissional_delete(request, empresa_pk, pk):
    """Excluir profissional"""
    if request.method != 'POST':
        return redirect('web-gerente:empresa-detail', pk=empresa_pk)
    
    try:
        prof_obj = Profissional.objects.filter(usuario__id=pk, empresa__usuario__id=empresa_pk).first()
        if not prof_obj:
            messages.error(request, 'Profissional não encontrado.')
        else:
            # Deletar usuário associado (Profissional.usuario é PK)
            usuario = prof_obj.usuario
            usuario.delete()
            messages.success(request, 'Profissional excluído com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-gerente:empresa-detail', pk=empresa_pk)


@gerente_required
def departamento_delete(request, empresa_pk, pk):
    """Excluir departamento"""
    if request.method != 'POST':
        return redirect('web-gerente:empresa-detail', pk=empresa_pk)
    
    try:
        deleted, _ = Departamento.objects.filter(id=pk, empresa__usuario__id=empresa_pk).delete()
        if deleted:
            messages.success(request, 'Departamento excluído com sucesso!')
        else:
            messages.error(request, 'Departamento não encontrado ou não foi possível excluir.')
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-gerente:empresa-detail', pk=empresa_pk)


# =====================================
# GERENTE - GERENCIAMENTO DE COLETAS
# =====================================

@gerente_required
def gerente_coletas_list(request):
    """Listar todas as coletas do sistema"""
    try:
        from coletas.serializers import ColetaListSerializer
        coletas_qs = Coleta.objects.select_related('empresa').all()
        serializer = ColetaListSerializer(coletas_qs, many=True, context={'request': request})
        coletas = serializer.data
    except InterfaceError as ie:
        logger.exception('Database InterfaceError in gerente_coletas_list: %s', ie)
        messages.error(request, 'Erro de conexão com o banco de dados. Por favor, tente novamente mais tarde.')
        coletas = []
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        coletas = []
    
    return render(request, 'gerente/coletas_list.html', {'coletas': coletas})


@gerente_required
def gerente_coleta_detail(request, pk):
    """Detalhes da coleta"""
    try:
        from coletas.serializers import ColetaSerializer, ColetaEstatisticasSerializer
        coleta_obj = Coleta.objects.select_related('empresa').filter(id=pk).first()
        coleta = ColetaSerializer(coleta_obj, context={'request': request}).data if coleta_obj else None

        # Estatísticas
        if coleta_obj:
            from coletas.models import ColetaProfissional, StatusPreenchimento
            total_profissionais = coleta_obj.coleta_profissionais.count()
            total_concluidos = coleta_obj.coleta_profissionais.filter(status=StatusPreenchimento.CONCLUIDO).count()
            total_pendentes = coleta_obj.coleta_profissionais.filter(status=StatusPreenchimento.PENDENTE).count()
            total_em_progresso = coleta_obj.coleta_profissionais.filter(status=StatusPreenchimento.EM_PROGRESSO).count()
            percentual_conclusao = coleta_obj.calcular_percentual()

            from django.db.models import Count
            profissionais_por_status = {
                item['status']: item['total']
                for item in ColetaProfissional.objects.filter(coleta=coleta_obj).values('status').annotate(total=Count('id'))
            }

            estatisticas = {
                'total_profissionais': total_profissionais,
                'total_concluidos': total_concluidos,
                'total_pendentes': total_pendentes,
                'total_em_progresso': total_em_progresso,
                'percentual_conclusao': percentual_conclusao,
                'profissionais_por_status': profissionais_por_status,
                'participantes_concluidos': total_concluidos,
                'participantes_pendentes': total_pendentes,
                'participantes_em_progresso': total_em_progresso,
            }
        else:
            estatisticas = {}
    except InterfaceError as ie:
        logger.exception('Database InterfaceError in gerente_coleta_detail: %s', ie)
        messages.error(request, 'Erro de conexão com o banco de dados. Por favor, tente novamente mais tarde.')
        coleta = None
        estatisticas = {}
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        coleta = None
        estatisticas = {}
    
    return render(request, 'gerente/coleta_detail.html', {
        'coleta': coleta,
        'estatisticas': estatisticas
    })


@gerente_required
def gerente_coleta_manage(request, pk):
    """Gerenciar coleta"""
    if request.method == 'POST':
        tipo_adicao = request.POST.get('tipo_adicao')

        profissionais = []
        try:
            coleta = Coleta.objects.select_related('empresa').get(id=pk)

            if tipo_adicao == 'todos':
                profissionais = list(coleta.empresa.profissionais.filter(is_active=True))
            elif tipo_adicao == 'departamentos':
                departamentos_ids = request.POST.getlist('departamentos_selecionados')
                for dept_id in departamentos_ids:
                    profissionais.extend(list(Profissional.objects.filter(departamento_id=dept_id, is_active=True)))
            elif tipo_adicao == 'individuais':
                profissionais_ids = request.POST.getlist('profissionais_selecionados')
                profissionais.extend(list(Profissional.objects.filter(usuario__in=profissionais_ids, is_active=True)))

            adicionados = 0
            for prof in set(profissionais):
                coleta.adicionar_profissional(prof)
                adicionados += 1

            if adicionados > 0:
                coleta.atualizar_totais()
                messages.success(request, f'{adicionados} profissional(is) adicionado(s) com sucesso!')
            else:
                messages.info(request, 'Nenhum profissional adicionado.')

        except Coleta.DoesNotExist:
            messages.error(request, 'Coleta não encontrada.')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')

        return redirect('web-gerente:coleta-manage', pk=pk)
    
    try:
        coleta_obj = Coleta.objects.select_related('empresa').filter(id=pk).first()
        if coleta_obj:
            # Profissionais da empresa que ainda não estão na coleta
            existentes = coleta_obj.coleta_profissionais.values_list('profissional_id', flat=True)
            todos_profissionais_qs = coleta_obj.empresa.profissionais.filter(is_active=True).exclude(usuario__in=existentes)
            from empresas.serializers import ProfissionalListSerializer
            profissionais = ProfissionalListSerializer(todos_profissionais_qs, many=True, context={'request': request}).data

            # Departamentos da empresa
            dept_qs = Departamento.objects.filter(empresa=coleta_obj.empresa)
            departamentos = empresas_serializers.DepartamentoListSerializer(dept_qs, many=True).data
            coleta = None
            # For template we may still want serialized coleta details
            from coletas.serializers import ColetaSerializer
            coleta = ColetaSerializer(coleta_obj, context={'request': request}).data
        else:
            profissionais = []
            departamentos = []
            coleta = None
    except InterfaceError as ie:
        logger.exception('Database InterfaceError in gerente_coleta_manage: %s', ie)
        messages.error(request, 'Erro de conexão com o banco de dados. Por favor, tente novamente mais tarde.')
        coleta = None
        profissionais = []
        departamentos = []
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        coleta = None
        profissionais = []
        departamentos = []
    
    return render(request, 'gerente/coleta_manage.html', {
        'coleta': coleta,
        'profissionais': profissionais,
        'departamentos': departamentos
    })


@gerente_required
def gerente_coleta_cancelar(request, pk):
    """Cancelar coleta"""
    if request.method != 'POST':
        return redirect('web-gerente:coleta-detail', pk=pk)
    
    try:
        coleta = Coleta.objects.filter(id=pk).first()
        if not coleta:
            messages.error(request, 'Coleta não encontrada.')
        else:
            coleta.cancelar()
            messages.success(request, 'Coleta cancelada com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-gerente:coleta-detail', pk=pk)


@gerente_required
@gerente_required
def gerente_coleta_exportar(request, pk):
    """Exportar resumo da coleta em Excel"""
    access_token = request.session.get('access_token')
    
    if not access_token:
        messages.error(request, 'Sessão expirada. Faça login novamente.')
        return redirect('usuarios:login')
    
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        # Reuse the API ViewSet export implementation by calling it with request
        from rest_framework.request import Request as DRFRequest
        from coletas.views import ColetaViewSet

        base_request = getattr(request, '_request', request)
        drf_request = DRFRequest(base_request)
        drf_request.user = request.user

        viewset = ColetaViewSet()
        viewset.request = drf_request
        viewset.kwargs = {'pk': pk}
        resp = viewset.exportar_excel(drf_request, pk=pk)
        # If viewset returned a Django HttpResponse, return it directly
        from django.http import HttpResponse
        if isinstance(resp, HttpResponse):
            return resp
        # If DRF Response, convert to template message
        messages.error(request, 'Erro ao exportar dados.')
    except Exception as e:
        logging.getLogger(__name__).exception('Erro ao exportar coleção: %s', e)
        messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-gerente:coleta-detail', pk=pk)


@gerente_required
def gerente_coleta_exportar_dados_textuais(request, pk):
    """Exportar dados textuais em Excel"""
    try:
        from rest_framework.request import Request as DRFRequest
        from coletas.views import ColetaViewSet

        base_request = getattr(request, '_request', request)
        drf_request = DRFRequest(base_request)
        drf_request.user = request.user

        viewset = ColetaViewSet()
        viewset.request = drf_request
        viewset.kwargs = {'pk': pk}
        resp = viewset.exportar_dados_textuais(drf_request, pk=pk)
        from django.http import HttpResponse
        if isinstance(resp, HttpResponse):
            return resp
        messages.error(request, 'Erro ao exportar dados.')
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-gerente:coleta-detail', pk=pk)


@gerente_required
def gerente_coleta_exportar_participantes(request, pk):
    """Exportar participantes em CSV"""
    try:
        from rest_framework.request import Request as DRFRequest
        from coletas.views import ColetaViewSet

        base_request = getattr(request, '_request', request)
        drf_request = DRFRequest(base_request)
        drf_request.user = request.user

        viewset = ColetaViewSet()
        viewset.request = drf_request
        viewset.kwargs = {'pk': pk}
        resp = viewset.exportar_participantes_excel(drf_request, pk=pk)
        from django.http import HttpResponse
        if isinstance(resp, HttpResponse):
            return resp
        messages.error(request, 'Erro ao exportar participantes.')
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-gerente:coleta-detail', pk=pk)


@gerente_required
def gerente_coleta_exportar_midias(request, pk):
    """Exportar mídias em ZIP"""
    try:
        from rest_framework.request import Request as DRFRequest
        from coletas.views import ColetaViewSet

        base_request = getattr(request, '_request', request)
        drf_request = DRFRequest(base_request)
        drf_request.user = request.user

        viewset = ColetaViewSet()
        viewset.request = drf_request
        viewset.kwargs = {'pk': pk}
        resp = viewset.exportar_midias(drf_request, pk=pk)
        from django.http import HttpResponse
        if isinstance(resp, HttpResponse):
            return resp
        messages.error(request, 'Erro ao exportar mídias.')
    except Exception as e:
        # Log and attempt HTTP fallback to API endpoint
        logger.exception('Erro ao exportar mídias via ViewSet: %s', e)
        try:
            import requests
            access_token = request.session.get('access_token')
            headers = {'Authorization': f'Bearer {access_token}'} if access_token else {}
            api_url = f'http://127.0.0.1:8000/api/v1/coletas/{pk}/exportar_midias/'
            r = requests.get(api_url, headers=headers, stream=True, timeout=60)
            from django.http import HttpResponse
            if r.status_code == 200:
                response = HttpResponse(r.content, content_type=r.headers.get('Content-Type', 'application/zip'))
                if 'Content-Disposition' in r.headers:
                    response['Content-Disposition'] = r.headers['Content-Disposition']
                return response
            else:
                messages.error(request, f'Erro ao exportar mídias: status {r.status_code}')
        except Exception as ie:
            logger.exception('Fallback HTTP export failed: %s', ie)
            messages.error(request, f'Erro ao exportar mídias: {str(ie)}')

    return redirect('web-gerente:coleta-detail', pk=pk)


@gerente_required
def gerente_coleta_remover_participante(request, pk):
    """Remover participante de uma coleta"""
    if request.method == 'POST':
        profissional_id = request.POST.get('profissional_id')
        try:
            coleta = Coleta.objects.get(id=pk)
            prof = Profissional.objects.filter(usuario__id=profissional_id, empresa=coleta.empresa).first()
            if not prof:
                messages.error(request, 'Participante não encontrado.')
            else:
                from coletas.models import ColetaProfissional
                cp = ColetaProfissional.objects.filter(coleta=coleta, profissional=prof).first()
                if not cp:
                    messages.error(request, 'Participante não está cadastrado nesta coleta.')
                else:
                    nome = cp.profissional.nome
                    cp.delete()
                    coleta.atualizar_totais()
                    messages.success(request, 'Participante removido com sucesso!')
        except Coleta.DoesNotExist:
            messages.error(request, 'Coleta não encontrada.')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-gerente:coleta-detail', pk=pk)


@gerente_required
def gerente_coleta_refazer(request, pk):
    """Refazer coleta (apagar todas as respostas e reabrir)"""
    if request.method == 'POST':
        try:
            coleta = Coleta.objects.get(id=pk)
            # Apagar todas as respostas e resetar participantes
            from coletas.models import RespostaColeta

            participantes_count = 0
            respostas_count = 0

            for cp in coleta.coleta_profissionais.all():
                if hasattr(cp, 'resposta'):
                    resposta = cp.resposta
                    if hasattr(resposta, 'foto'):
                        resposta.foto.delete()
                    if hasattr(resposta, 'assinatura'):
                        resposta.assinatura.delete()
                    resposta.delete()
                    respostas_count += 1

                cp.status = 'pendente'
                cp.data_inicio = None
                cp.data_conclusao = None
                cp.save()
                participantes_count += 1

            coleta.status = 'em_andamento'
            coleta.data_fim = None
            coleta.save()
            coleta.atualizar_totais()

            messages.success(request, f'Coleta reaberta com sucesso! {respostas_count} respostas apagadas e {participantes_count} participantes resetados.')
        except Coleta.DoesNotExist:
            messages.error(request, 'Coleta não encontrada.')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-gerente:coleta-detail', pk=pk)


@gerente_required
def gerente_coleta_refazer_individual(request, pk):
    """Permitir que um profissional específico refaça o formulário"""
    if request.method == 'POST':
        profissional_id = request.POST.get('profissional_id')
        try:
            coleta = Coleta.objects.get(id=pk)
            prof = Profissional.objects.filter(usuario__id=profissional_id, empresa=coleta.empresa).first()
            if not prof:
                messages.error(request, 'Participante não encontrado.')
            else:
                from coletas.models import ColetaProfissional
                cp = ColetaProfissional.objects.filter(coleta=coleta, profissional=prof).first()
                if not cp:
                    messages.error(request, 'Participante não encontrado nesta coleta.')
                else:
                    if hasattr(cp, 'resposta'):
                        resp = cp.resposta
                        if hasattr(resp, 'foto'):
                            resp.foto.delete()
                        if hasattr(resp, 'assinatura'):
                            resp.assinatura.delete()
                        resp.delete()

                    cp.status = 'pendente'
                    cp.data_inicio = None
                    cp.data_conclusao = None
                    cp.save()

                    coleta.atualizar_totais()

                    if coleta.status == 'concluida':
                        coleta.status = 'em_andamento'
                        coleta.data_fim = None
                        coleta.save()

                    messages.success(request, 'Profissional pode refazer o formulário!')
        except Coleta.DoesNotExist:
            messages.error(request, 'Coleta não encontrada.')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-gerente:coleta-detail', pk=pk)

