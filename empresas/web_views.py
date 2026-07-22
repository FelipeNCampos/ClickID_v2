"""
Views web para empresa
"""
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from functools import wraps
import logging
import requests
from django.conf import settings
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from datetime import datetime as _datetime
from django.db.utils import InterfaceError
from clickid_core.db_utils import close_db_connections
from .models import Departamento, Empresa, ImportacaoProfissionais
from .tasks import processar_importacao_profissionais
logger = logging.getLogger(__name__)


def _mask_token(tkn: str) -> str:
    if not tkn:
        return ''
    try:
        return f"{tkn[:8]}..."
    except Exception:
        return '***'


def empresa_required(view_func):
    """Decorator para views que requerem autenticação de empresa"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Verificar se tem token na sessão E se usuário está autenticado
        token = request.session.get('access_token')
        logger.debug('empresa_required: access_token present=%s token_prefix=%s user_authenticated=%s', bool(token), _mask_token(token), request.user.is_authenticated)
        if not token or not request.user.is_authenticated:
            messages.warning(request, 'Você precisa fazer login primeiro')
            return redirect('web-gerente:login')
        
        # Verificar se o usuário é empresa
        if request.user.tipo_usuario != 'empresa':
            messages.error(request, 'Acesso negado. Área restrita para empresas.')
            if request.user.tipo_usuario == 'gerente':
                return redirect('web-gerente:dashboard')
            return redirect('web-gerente:login')
        
        # Verificar se a empresa está ativa
        try:
            from .models import Empresa
            empresa = Empresa.objects.get(usuario=request.user)
            if not empresa.is_active:
                messages.error(request, 'Sua empresa está desativada. Entre em contato com o administrador.')
                from django.contrib.auth import logout
                logout(request)
                request.session.flush()
                return redirect('web-gerente:login')
        except Empresa.DoesNotExist:
            messages.error(request, 'Empresa não encontrada.')
            return redirect('web-gerente:login')
        except InterfaceError as ie:
            # Erro de conexão com o banco - mostrar mensagem amigável e redirecionar
            logger.exception('Database InterfaceError in empresa_required: %s', ie)
            messages.error(request, 'Erro de conexão com o banco de dados. Tente novamente mais tarde.')
            return redirect('web-gerente:login')
        
        return view_func(request, *args, **kwargs)
    return wrapper


@empresa_required
def empresa_dashboard(request):
    """Dashboard da empresa"""
    try:
        # Buscar dados da empresa logada via ORM/serializers (evita chamadas HTTP internas)
        from .models import Empresa, Profissional, Departamento
        from .serializers import EmpresaSerializer, ProfissionalListSerializer, DepartamentoListSerializer
        from coletas.models import Coleta
        from coletas.serializers import ColetaListSerializer

        empresa_obj = Empresa.objects.select_related('usuario').filter(usuario=request.user).first()
        if not empresa_obj:
            messages.error(request, 'Empresa não encontrada')
            return redirect('web-gerente:login')

        # Serializar empresa
        try:
            empresa = EmpresaSerializer(empresa_obj).data
        except Exception:
            empresa = {'usuario': str(empresa_obj.usuario.pk), 'razao_social': getattr(empresa_obj, 'razao_social', '')}

        # Buscar profissionais, coletas e departamentos via ORM
        profissionais_qs = Profissional.objects.filter(empresa=empresa_obj).select_related('usuario')
        coletas_qs = Coleta.objects.filter(empresa=empresa_obj).order_by('-created_at')
        departamentos_qs = Departamento.objects.filter(empresa=empresa_obj)

        try:
            profissionais = ProfissionalListSerializer(profissionais_qs, many=True).data
        except Exception:
            profissionais = list(profissionais_qs.values())

        try:
            coletas = ColetaListSerializer(coletas_qs, many=True).data
        except Exception:
            coletas = list(coletas_qs.values())

        try:
            departamentos = DepartamentoListSerializer(departamentos_qs, many=True).data
        except Exception:
            departamentos = list(departamentos_qs.values())

        # Calcular estatísticas
        total_profissionais = len(profissionais)
        total_departamentos = len(departamentos)
        total_coletas = len(coletas)

        coletas_ativas = [c for c in coletas if (c.get('status') or '').lower() == 'em_andamento']
        coletas_concluidas = [c for c in coletas if (c.get('status') or '').lower() in ('concluida', 'concluido')]
        coletas_rascunho = [c for c in coletas if (c.get('status') or '').lower() == 'rascunho']

        profissionais_ativos = [p for p in profissionais if p.get('is_active', True)]

        context = {
            'empresa': empresa,
            'total_profissionais': total_profissionais,
            'total_departamentos': total_departamentos,
            'total_coletas': total_coletas,
            'total_coletas_ativas': len(coletas_ativas),
            'total_coletas_concluidas': len(coletas_concluidas),
            'total_coletas_rascunho': len(coletas_rascunho),
            'total_profissionais_ativos': len(profissionais_ativos),
            'coletas_recentes': coletas[:5],
            'profissionais_recentes': profissionais[:5],
        }
    except InterfaceError as ie:
        logger.exception('Database InterfaceError in empresa_dashboard: %s', ie)
        messages.error(request, 'Erro de conexão com o banco de dados. Por favor, recarregue a página mais tarde.')
        context = {}
    except Exception as e:
        messages.error(request, f'Erro ao carregar dados: {str(e)}')
        context = {}
    
    return render(request, 'empresas/dashboard.html', context)


@empresa_required
def departamentos_list(request):
    """Lista de departamentos"""
    try:
        from .models import Departamento, Empresa
        from .serializers import DepartamentoListSerializer
        empresa = Empresa.objects.get(usuario=request.user)
        qs = Departamento.objects.filter(empresa=empresa).order_by('nome')
        try:
            departamentos = DepartamentoListSerializer(qs, many=True).data
        except Exception:
            departamentos = list(qs.values())
    except Exception as e:
        messages.error(request, f'Erro ao carregar departamentos: {str(e)}')
        departamentos = []
    
    return render(request, 'empresas/departamentos_list.html', {'departamentos': departamentos})


@empresa_required
def departamento_create(request):
    """Criar departamento"""
    if request.method == 'POST':
        try:
            from .models import Departamento, Empresa
            empresa = Empresa.objects.get(usuario=request.user)
            nome = request.POST.get('nome')
            descricao = request.POST.get('descricao', '')
            if not nome:
                messages.error(request, 'Nome é obrigatório.')
                return render(request, 'empresas/departamento_form.html')
            Departamento.objects.create(empresa=empresa, nome=nome, descricao=descricao)
            messages.success(request, 'Departamento criado com sucesso!')
            return redirect('web-empresa:dashboard')
        except Exception as e:
            messages.error(request, f'Erro ao criar departamento: {str(e)}')
    
    return render(request, 'empresas/departamento_form.html')


@empresa_required
def profissionais_list(request):
    """Lista de profissionais"""
    try:
        from .models import Profissional, Empresa
        from .serializers import ProfissionalListSerializer
        empresa = Empresa.objects.get(usuario=request.user)
        busca = request.GET.get('busca', '').strip()
        qs = Profissional.objects.filter(empresa=empresa).select_related('usuario', 'departamento')
        if busca:
            qs = qs.filter(nome__icontains=busca)
        qs = qs.order_by('nome')
        try:
            profissionais = ProfissionalListSerializer(qs, many=True).data
        except Exception:
            profissionais = list(qs.values())
    except Exception as e:
        messages.error(request, f'Erro ao carregar profissionais: {str(e)}')
        profissionais = []

    paginator = Paginator(profissionais, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'empresas/profissionais_list.html', {'page_obj': page_obj, 'busca': busca})


@empresa_required
def profissional_create(request):
    """Criar profissional"""
    headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
    
    if request.method == 'POST':
        try:
            from .serializers import ProfissionalSerializer
            data = {
                'nome': request.POST.get('nome'),
                'cpf': request.POST.get('cpf', '').replace('.', '').replace('-', ''),
                'email': request.POST.get('email'),
                'empresa': str(request.user.id),
                'departamento': request.POST.get('departamento') if request.POST.get('departamento') else None,
            }
            # Remover campos vazios
            data = {k: v for k, v in data.items() if v or k == 'empresa'}

            serializer = ProfissionalSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                messages.success(request, 'Profissional criado com sucesso!')
                return redirect('web-empresa:profissionais-list')
            else:
                messages.error(request, str(serializer.errors))
        except Exception as e:
            messages.error(request, f'Erro ao criar profissional: {str(e)}')
    
    # Buscar departamentos
    try:
        from .models import Departamento, Empresa
        empresa = Empresa.objects.get(usuario=request.user)
        departamentos_qs = Departamento.objects.filter(empresa=empresa).order_by('nome')
        from .serializers import DepartamentoListSerializer
        departamentos = DepartamentoListSerializer(departamentos_qs, many=True).data
    except Exception:
        departamentos = []
    
    return render(request, 'empresas/profissional_form.html', {'departamentos': departamentos})


@empresa_required
def profissionais_import_legacy(request):
    """Importar profissionais via Excel"""
    # Log incoming request keys to help diagnose missing file issues
    try:
        logger.debug('profissionais_import called: method=%s request.FILES.keys=%s request.POST.keys=%s',
                     request.method, list(request.FILES.keys()), list(request.POST.keys()))
    except Exception:
        logger.debug('profissionais_import called: could not read request keys')

    # Be tolerant: some test clients or middleware may populate files on the underlying
    # WSGI request object. Prefer explicit source so we don't miss the uploaded file.
    underlying_files = None
    try:
        underlying_files = getattr(getattr(request, '_request', None), 'FILES', None)
    except Exception:
        underlying_files = None

    files_source = request.FILES if request.FILES else (underlying_files or {})

    # If still empty, try to parse multipart from raw body (useful in some test-client cases)
    if not files_source:
        try:
            content_type = request.META.get('CONTENT_TYPE') or request.META.get('HTTP_CONTENT_TYPE', '')
            if content_type and content_type.startswith('multipart/') and getattr(request, 'body', None):
                import cgi, io
                fs = cgi.FieldStorage(fp=io.BytesIO(request.body), environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': content_type,
                })
                if fs and fs.list:
                    parsed_files = {}
                    for field in fs.list:
                        if field.filename:
                            # read file content
                            try:
                                field.file.seek(0)
                            except Exception:
                                pass
                            data = field.file.read()
                            from django.core.files.uploadedfile import SimpleUploadedFile
                            parsed_files[field.name] = SimpleUploadedFile(field.filename, data, content_type=field.type or 'application/octet-stream')
                    if parsed_files:
                        files_source = parsed_files
        except Exception:
            logger.debug('profissionais_import: parsing multipart from raw body failed', exc_info=True)

    if request.method == 'POST' and files_source and files_source.get('arquivo'):
        # Evitar chamada HTTP local; invocar o ViewSet import_excel diretamente
        try:
            from rest_framework.request import Request as DRFRequest
            from rest_framework.test import APIRequestFactory
            from empresas.views import ProfissionalViewSet
            from django.http import JsonResponse

            # Garantir que o POST contenha o campo 'empresa' referente à Empresa
            mutable_post = request.POST.copy()
            try:
                from .models import Empresa
                empresa_obj = Empresa.objects.get(usuario=request.user)
                mutable_post['empresa'] = str(empresa_obj.usuario.pk)
            except Exception:
                # Fallback: use the raw user id (older behavior)
                mutable_post['empresa'] = str(request.user.id)

            # Em vez de construir um novo request via APIRequestFactory (que pode gerar
            # content-types não compatíveis neste ambiente), reutilizamos o WSGI request
            # original e injetamos o POST/files necessários para que DRF consiga parsear
            base_request = getattr(request, '_request', request)
            try:
                base_request._post = mutable_post
            except Exception:
                # Se não for possível atribuir, log e prosseguir
                logger.debug('profissionais_import: não foi possível atribuir base_request._post')
            try:
                # prefer the populated files_source (may come from request._request.FILES in tests)
                base_request._files = files_source
            except Exception:
                logger.debug('profissionais_import: não foi possível atribuir base_request._files')

            # Construir DRF Request a partir do WSGI request atualizado
            drf_request = DRFRequest(base_request)
            drf_request.user = request.user

            viewset = ProfissionalViewSet()
            viewset.request = drf_request
            response = viewset.import_excel(drf_request)

            # If the local call failed because the file was not present, attempt an internal HTTP POST
            try:
                resp_data = getattr(response, 'data', {}) or {}
                resp_status = getattr(response, 'status_code', None)
            except Exception:
                resp_data = {}
                resp_status = None

            arquivo_missing = False
            if resp_data and isinstance(resp_data, dict):
                arquivo_missing = resp_data.get('erro') and 'arquivo' in resp_data.get('erro').lower()
            if (not files_source or arquivo_missing) and request.method == 'POST':
                try:
                    logger.warning('profissionais_import: arquivo ausente no request; tentando fallback HTTP POST to API')
                    # Prepare files and data for multipart POST
                    try:
                        empresa_obj = None
                        from .models import Empresa
                        empresa_obj = Empresa.objects.get(usuario=request.user)
                        empresa_id = str(empresa_obj.usuario.pk)
                    except Exception:
                        empresa_id = str(request.user.id)

                    api_url = request.build_absolute_uri('/api/v1/profissionais/import_excel/')
                    sess = requests.Session()
                    # Copy cookies from incoming request to session
                    for k, v in request.COOKIES.items():
                        sess.cookies.set(k, v)

                    files_payload = {}
                    if files_source and files_source.get('arquivo'):
                        f = files_source.get('arquivo')
                        # Use underlying file-like object when possible to avoid reading into memory
                        file_obj = getattr(f, 'file', None) or f
                        try:
                            file_obj.seek(0)
                        except Exception:
                            pass
                        files_payload['arquivo'] = (getattr(f, 'name', 'upload.xlsx'), file_obj, getattr(f, 'content_type', 'application/octet-stream'))
                    data_payload = {'empresa': empresa_id}

                    headers = {}
                    # pass Authorization header if access token is stored in session
                    access_token = request.session.get('access_token')
                    if access_token:
                        headers['Authorization'] = f'Bearer {access_token}'
                    # pass CSRF token header if available (best-effort)
                    csrf = request.COOKIES.get('csrftoken') or request.META.get('CSRF_COOKIE')
                    if csrf:
                        headers['X-CSRFToken'] = csrf
                    headers['Accept'] = 'application/json'

                    r = sess.post(api_url, data=data_payload, files=files_payload, headers=headers, timeout=120)
                    logger.debug('profissionais_import: fallback HTTP POST status=%s content-type=%s', r.status_code, r.headers.get('Content-Type'))

                    # If success and content-type JSON, return JSON response to AJAX
                    if r.status_code in (200, 201):
                        from django.http import HttpResponse
                        return HttpResponse(r.content, status=r.status_code, content_type=r.headers.get('Content-Type', 'application/json'))
                    else:
                        # prepare message for non-AJAX flow
                        messages.error(request, r.text[:2000])
                except Exception as ie:
                    logger.exception('profissionais_import: fallback HTTP POST falhou: %s', ie)

            status_code = getattr(response, 'status_code', 500)
            data = getattr(response, 'data', {}) or {}

            # If request came from AJAX (frontend fetch), return JSON so client JS can handle progress/results
            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
            if is_ajax:
                return JsonResponse(data, status=status_code)

            # Non-AJAX (normal form submit) — use messages + redirect flow
            if status_code == 201:
                total = data.get('total_importados', 0)
                erros = data.get('erros', [])
                total_erros = data.get('total_erros', 0)

                if total > 0:
                    messages.success(request, f'✅ {total} profissional(is) importado(s) com sucesso!')

                if erros:
                    messages.warning(request, f'⚠️ {total_erros} erro(s) encontrado(s):')
                    for erro in erros[:5]:
                        messages.error(request, f'Linha {erro.get("linha")}: {erro.get("erro")}')
                    if total_erros > 5:
                        messages.info(request, f'... e mais {total_erros - 5} erro(s)')

                if total == 0 and total_erros > 0:
                    messages.error(request, 'Nenhum profissional foi importado. Verifique os erros acima.')

                return redirect('web-empresa:profissionais-list')
            else:
                messages.error(request, str(data))
        except Exception as e:
            logger.exception('Erro ao executar import_excel localmente: %s', e)
            messages.error(request, f'Erro ao importar arquivo: {str(e)}')
    
    from django.urls import reverse

    return render(request, 'empresas/profissional_import.html', {
        'import_post_url': reverse('web-empresa:profissionais-import'),
        'back_url': reverse('web-empresa:profissionais-list'),
        'success_url': reverse('web-empresa:profissionais-list'),
        'empresa_hidden_id': str(request.user.id),
    })


@empresa_required
def profissionais_import(request):
    """Recebe o arquivo e deixa o worker processá-lo em segundo plano."""
    from django.urls import reverse

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    empresa = get_object_or_404(Empresa, usuario=request.user)
    if request.method == 'POST':
        arquivo = request.FILES.get('arquivo')
        if not arquivo:
            return JsonResponse({'erro': 'Arquivo não fornecido'}, status=400) if is_ajax else redirect(request.path)
        if arquivo.size > 50 * 1024 * 1024:
            return JsonResponse({'erro': 'O arquivo deve ter no máximo 50 MB'}, status=400) if is_ajax else redirect(request.path)

        departamento = None
        departamento_id = request.POST.get('departamento')
        if departamento_id:
            departamento = Departamento.objects.filter(pk=departamento_id, empresa=empresa).first()
            if not departamento:
                return JsonResponse({'erro': 'Departamento inválido'}, status=400) if is_ajax else redirect(request.path)

        importacao = ImportacaoProfissionais.objects.create(
            empresa=empresa,
            solicitada_por=request.user,
            departamento=departamento,
            arquivo=arquivo,
        )
        transaction.on_commit(lambda: processar_importacao_profissionais.delay(str(importacao.pk)))
        status_url = reverse('web-empresa:profissionais-import-status', kwargs={'importacao_pk': importacao.pk})
        if is_ajax:
            return JsonResponse({
                'importacao_id': str(importacao.pk),
                'status': importacao.status,
                'status_url': status_url,
                'mensagem': 'Arquivo recebido. A importação continuará em segundo plano.',
            }, status=202)
        messages.info(request, 'Arquivo recebido. A importação continuará em segundo plano.')
        return redirect('web-empresa:profissionais-list')

    return render(request, 'empresas/profissional_import.html', {
        'import_post_url': reverse('web-empresa:profissionais-import'),
        'back_url': reverse('web-empresa:profissionais-list'),
        'success_url': reverse('web-empresa:profissionais-list'),
        'empresa_hidden_id': str(request.user.id),
    })


@empresa_required
def profissionais_import_status(request, importacao_pk):
    importacao = get_object_or_404(ImportacaoProfissionais, pk=importacao_pk, empresa__usuario=request.user)
    return JsonResponse({
        'id': str(importacao.pk),
        'status': importacao.status,
        'total_linhas': importacao.total_linhas,
        'total_processados': importacao.total_processados,
        'total_importados': importacao.total_importados,
        'total_ignorados': importacao.total_ignorados,
        'total_erros': importacao.total_erros,
        'erros': importacao.erros[:10],
        'mensagem_erro': importacao.mensagem_erro,
    })


@empresa_required
def profissionais_import_dados(request):
    """Importar dados adicionais para profissionais já cadastrados"""
    return render(request, 'empresas/profissional_import_dados.html')


@empresa_required
def profissional_detail(request, pk):
    """Detalhes do profissional e atualização via POST (sem chamadas HTTP internas)"""
    from .models import Profissional, Empresa
    from .serializers import ProfissionalSerializer, ProfissionalListSerializer

    profissional = Profissional.objects.filter(usuario=pk).select_related('usuario', 'departamento', 'empresa').first()
    if not profissional:
        messages.error(request, 'Profissional não encontrado.')
        return redirect('web-empresa:profissionais-list')

    if request.method == 'POST':
        try:
            cpf = request.POST.get('cpf', '').replace('.', '').replace('-', '').strip() or None
            email = request.POST.get('email', '').strip() or None
            departamento = request.POST.get('departamento') or None

            data = {
                'nome': request.POST.get('nome'),
                'cpf': cpf,
                'email': email,
                'departamento': departamento,
            }

            # Remover chaves com valor None para permitir partial update
            data = {k: v for k, v in data.items() if v is not None}

            serializer = ProfissionalSerializer(profissional, data=data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                messages.success(request, 'Profissional atualizado com sucesso!')
                return redirect('web-empresa:profissional-detail', pk=pk)
            else:
                for field, errs in serializer.errors.items():
                    if isinstance(errs, list):
                        for err in errs:
                            messages.error(request, f'{field}: {err}')
                    else:
                        messages.error(request, f'{field}: {errs}')
                return redirect('web-empresa:profissional-edit', pk=pk)
        except Exception as e:
            logger.exception('Erro ao atualizar profissional: %s', e)
            messages.error(request, f'Erro ao atualizar profissional: {str(e)}')
            return redirect('web-empresa:profissional-edit', pk=pk)

    # GET: renderizar detalhes
    try:
        data = ProfissionalSerializer(profissional).data
    except Exception:
        data = {}

    # Buscar departamentos para o formulário de edição
    try:
        empresa = profissional.empresa
        from .serializers import DepartamentoListSerializer
        departamentos_qs = empresa.departamentos.all()
        departamentos = DepartamentoListSerializer(departamentos_qs, many=True).data
    except Exception:
        departamentos = []

    return render(request, 'empresas/profissional_edit.html', {
        'profissional': data,
        'departamentos': departamentos
    })


@empresa_required
def profissional_toggle_active(request, pk):
    """Ativar/desativar profissional"""
    if request.method == 'POST':
        try:
            from .models import Profissional
            prof = Profissional.objects.filter(usuario=pk).first()
            if not prof:
                messages.error(request, 'Profissional não encontrado.')
            else:
                prof.is_active = not getattr(prof, 'is_active', True)
                prof.save(update_fields=['is_active'])
                status_text = 'ativado' if prof.is_active else 'desativado'
                messages.success(request, f'Profissional {status_text} com sucesso!')
        except Exception as e:
            logger.exception('Erro ao alternar status do profissional: %s', e)
            messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-empresa:profissional-detail', pk=pk)


@empresa_required
def profissional_delete(request, pk):
    """Excluir profissional"""
    if request.method == 'POST':
        try:
            from .models import Profissional
            prof = Profissional.objects.filter(usuario=pk).select_related('usuario').first()
            if not prof:
                messages.error(request, 'Profissional não encontrado.')
            else:
                # Deletar o usuário vinculado para remover tudo consistentemente
                try:
                    prof.usuario.delete()
                    messages.success(request, 'Profissional excluído com sucesso!')
                except Exception:
                    # Fallback: remover apenas o registro de Profissional
                    prof.delete()
                    messages.success(request, 'Profissional excluído (registro removido).')
        except Exception as e:
            logger.exception('Erro ao excluir profissional: %s', e)
            messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-empresa:profissionais-list')


@empresa_required
def modelos_list(request):
    """Lista de modelos de cartão"""
    try:
        from modelos.models import ModeloCartao
        from modelos.serializers import ModeloCartaoListSerializer
        from .models import Empresa

        empresa = Empresa.objects.filter(usuario=request.user).first()
        if not empresa:
            modelos = []
        else:
            qs = ModeloCartao.objects.filter(empresa=empresa).order_by('-created_at')
            modelos = ModeloCartaoListSerializer(qs, many=True).data
    except Exception as e:
        messages.error(request, f'Erro ao carregar modelos: {str(e)}')
        modelos = []
    
    return render(request, 'empresas/modelos_list.html', {'modelos': modelos})


@empresa_required
def modelo_create(request):
    """Criar modelo de cartão"""
    if request.method == 'POST':
        try:
            from modelos.serializers import ModeloCartaoCreateSerializer
            from .models import Empresa

            empresa = Empresa.objects.get(usuario=request.user)
            data = {
                'nome': request.POST.get('nome'),
                'descricao': request.POST.get('descricao', ''),
                'empresa': empresa.pk
            }

            serializer = ModeloCartaoCreateSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                modelo = serializer.save()
                messages.success(request, 'Modelo criado!')
                return redirect('web-empresa:modelo-edit', pk=modelo.id)
            else:
                messages.error(request, str(serializer.errors))
        except Exception as e:
            messages.error(request, f'Erro ao criar modelo: {str(e)}')
    
    return render(request, 'empresas/modelo_form.html')


@empresa_required
def modelo_detail(request, pk):
    """Detalhes do modelo"""
    try:
        from modelos.models import ModeloCartao
        from modelos.serializers import ModeloCartaoSerializer
        modelo_obj = ModeloCartao.objects.filter(id=pk).first()
        modelo = ModeloCartaoSerializer(modelo_obj).data if modelo_obj else None
    except Exception as e:
        messages.error(request, f'Erro ao carregar modelo: {str(e)}')
        modelo = None

    return render(request, 'empresas/modelo_detail.html', {'modelo': modelo})


@empresa_required
def modelo_edit(request, pk):
    """Editor visual de modelo (canvas)"""
    try:
        from modelos.models import ModeloCartao
        from modelos.serializers import ModeloCartaoSerializer
        modelo_obj = ModeloCartao.objects.filter(id=pk).first()
        modelo = ModeloCartaoSerializer(modelo_obj).data if modelo_obj else None
    except Exception as e:
        messages.error(request, f'Erro ao carregar modelo para edição: {str(e)}')
        modelo = None

    return render(request, 'empresas/modelo_editor.html', {'modelo': modelo})


@empresa_required
def modelo_duplicate(request, pk):
    """Duplicar modelo"""
    if request.method == 'POST':
        # Call the API ViewSet action `duplicate` locally to reuse validation and copying logic
        try:
            from rest_framework.request import Request as DRFRequest
            from rest_framework.test import APIRequestFactory
            from rest_framework.test import force_authenticate
            from modelos.views import ModeloCartaoViewSet

            novo_nome = request.POST.get('nome') or ''
            copiar_campos = request.POST.get('copiar_campos', 'true').lower() in ('1', 'true', 'yes')

            # Ensure request._request._post contains the expected fields for DRF parsing
            mutable_post = request.POST.copy()
            mutable_post['novo_nome'] = novo_nome
            mutable_post['copiar_campos'] = str(copiar_campos).lower()
            base_request = getattr(request, '_request', request)
            try:
                base_request._post = mutable_post
            except Exception:
                pass

            # Build a DRF Request from the current WSGI request and call the viewset action
            drf_request = DRFRequest(base_request)
            drf_request.user = request.user

            viewset = ModeloCartaoViewSet()
            viewset.request = drf_request
            viewset.kwargs = {'pk': pk}

            resp = viewset.duplicate(drf_request, pk=pk)

            status_code = getattr(resp, 'status_code', 500)
            data = getattr(resp, 'data', {}) or {}

            if status_code == 201:
                messages.success(request, 'Modelo duplicado!')
                return redirect('web-empresa:modelos-list')
            else:
                messages.error(request, data if data else 'Erro ao duplicar modelo.')
        except Exception as e:
            logger.exception('Erro ao duplicar modelo via ViewSet: %s', e)
            messages.error(request, f'Erro ao duplicar modelo: {str(e)}')
    
    return redirect('web-empresa:modelos-list')


@empresa_required
def coletas_list(request):
    """Lista de coletas"""
    try:
        from coletas.models import Coleta, StatusColeta
        from coletas.serializers import ColetaListSerializer
        from coletas.models import Coleta as ColetaModel
        from empresas.models import Empresa

        empresa = Empresa.objects.filter(usuario=request.user).first()
        if not empresa:
            coletas = []
        else:
            qs = Coleta.objects.filter(empresa=empresa, is_active=True).order_by('-created_at')
            coletas = ColetaListSerializer(qs, many=True).data
    except Exception as e:
        logger.exception('Erro ao listar coletas: %s', e)
        messages.error(request, f'Erro ao carregar coletas: {str(e)}')
        coletas = []

    return render(request, 'empresas/coletas_list.html', {'coletas': coletas})


@empresa_required
def coleta_create(request):
    """Criar coleta"""
    if request.method == 'POST':
        try:
            from empresas.models import Empresa, Profissional
            from modelos.models import ModeloCartao
            from coletas.serializers import ColetaSerializer

            empresa = Empresa.objects.get(usuario=request.user)

            tipo_coleta = request.POST.get('tipo_coleta')
            incluir_foto = request.POST.get('incluir_foto') == 'true'
            incluir_assinatura = request.POST.get('incluir_assinatura') == 'true'

            if tipo_coleta == 'dados_extras' and not incluir_foto and not incluir_assinatura:
                messages.error(request, 'Para o tipo "Dados Extras", você deve selecionar pelo menos Foto ou Assinatura.')
                return redirect('web-empresa:coleta-create')

            modelo_id = None
            if tipo_coleta == 'modelo_ativo':
                modelo = ModeloCartao.objects.filter(empresa=empresa, is_active=True).order_by('-created_at').first()
                if not modelo:
                    messages.error(request, 'Nenhum modelo ativo encontrado. Cadastre um modelo antes de criar a coleta.')
                    return redirect('web-empresa:coleta-create')
                modelo_id = modelo.pk

            # Preparar dados para o serializer
            data = {
                'nome': request.POST.get('nome'),
                'descricao': request.POST.get('descricao', ''),
                'empresa': str(empresa.pk),
                'tipo_coleta': tipo_coleta,
                'include_foto': incluir_foto,
                'include_assinatura': incluir_assinatura,
            }

            if modelo_id:
                data['modelo'] = str(modelo_id)

            tipo_destinatarios = request.POST.get('tipo_destinatarios')
            profissionais_ids = []

            if tipo_destinatarios == 'todos':
                profissionais_qs = Profissional.objects.filter(empresa=empresa, is_active=True)
                profissionais_ids = [str(p.usuario.pk) for p in profissionais_qs]
                if not profissionais_ids:
                    messages.error(request, 'Nenhum profissional ativo encontrado na empresa')
                    return redirect('web-empresa:coleta-create')
            elif tipo_destinatarios == 'departamentos':
                departamentos_ids = request.POST.getlist('departamentos_selecionados')
                if not departamentos_ids:
                    messages.error(request, 'Selecione pelo menos um departamento')
                    return redirect('web-empresa:coleta-create')
                for dept_id in departamentos_ids:
                    qs = Profissional.objects.filter(empresa=empresa, departamento_id=dept_id, is_active=True)
                    profissionais_ids.extend([str(p.usuario.pk) for p in qs])
            elif tipo_destinatarios == 'individuais':
                profissionais_ids = request.POST.getlist('profissionais_selecionados')
                if not profissionais_ids:
                    messages.error(request, 'Selecione pelo menos um profissional')
                    return redirect('web-empresa:coleta-create')

            if profissionais_ids:
                data['profissionais_ids'] = list(dict.fromkeys(profissionais_ids))

            serializer = ColetaSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                coleta = serializer.save(iniciado_por=request.user)
                total_prof = len(profissionais_ids) if profissionais_ids else 0
                messages.success(request, f'Coleta criada com sucesso! {total_prof} profissional(is) adicionado(s).')
                return redirect('web-empresa:coleta-detail', pk=coleta.pk)
            else:
                messages.error(request, str(serializer.errors))
        except Exception as e:
            logger.exception('Erro ao criar coleta: %s', e)
            messages.error(request, f'Erro ao criar coleta: {str(e)}')
    
    # Buscar dados para o formulário
    try:
        from empresas.models import Empresa, Profissional
        from coletas.models import Coleta
        from modelos.models import ModeloCartao
        from coletas.serializers import ColetaListSerializer

        empresa = Empresa.objects.filter(usuario=request.user).first()
        if empresa:
            departamentos_qs = empresa.departamentos.all().order_by('nome')
            departamentos = [d for d in departamentos_qs.values('id', 'nome')]

            profissionais_qs = Profissional.objects.filter(empresa=empresa, is_active=True).select_related('usuario')
            from empresas.serializers import ProfissionalListSerializer
            profissionais = ProfissionalListSerializer(profissionais_qs, many=True).data

            tem_modelo_ativo = ModeloCartao.objects.filter(empresa=empresa, is_active=True).exists()
        else:
            departamentos = []
            profissionais = []
            tem_modelo_ativo = False
    except Exception as e:
        logger.exception('Erro ao carregar dados do formulário de coleta: %s', e)
        messages.error(request, f'Erro ao carregar dados: {str(e)}')
        departamentos = []
        profissionais = []
        tem_modelo_ativo = False
    
    return render(request, 'empresas/coleta_form.html', {
        'departamentos': departamentos,
        'profissionais': profissionais,
        'tem_modelo_ativo': tem_modelo_ativo
    })


@empresa_required
def coleta_detail(request, pk):
    """Detalhes da coleta"""
    try:
        from coletas.models import Coleta
        from coletas.serializers import ColetaSerializer

        coleta_obj = Coleta.objects.filter(id=pk).select_related('empresa', 'modelo').first()
        if not coleta_obj:
            messages.error(request, 'Coleta não encontrada.')
            return redirect('web-empresa:coletas-list')

        coleta = ColetaSerializer(coleta_obj).data

        # Estatísticas básicas
        total_profissionais = coleta_obj.coleta_profissionais.count()
        total_concluidos = coleta_obj.coleta_profissionais.filter(status__iexact='concluido').count()
        total_pendentes = coleta_obj.coleta_profissionais.filter(status__iexact='pendente').count()
        total_em_progresso = coleta_obj.coleta_profissionais.filter(status__iexact='em_progresso').count()

        percentual = coleta_obj.calcular_percentual()

        estatisticas = {
            'total_profissionais': total_profissionais,
            'total_concluidos': total_concluidos,
            'total_pendentes': total_pendentes,
            'total_em_progresso': total_em_progresso,
            'percentual_conclusao': percentual,
            'participantes_concluidos': total_concluidos,
            'participantes_pendentes': total_pendentes,
            'participantes_em_progresso': total_em_progresso,
        }

    except Exception as e:
        logger.exception('Erro ao carregar detalhe da coleta: %s', e)
        messages.error(request, f'Erro: {str(e)}')
        return redirect('web-empresa:coletas-list')

    return render(request, 'empresas/coleta_detail.html', {
        'coleta': coleta,
        'estatisticas': estatisticas
    })


@empresa_required
def coleta_manage(request, pk):
    """Gerenciar coleta (adicionar profissionais, enviar notificações)"""
    try:
        from coletas.models import Coleta
        from empresas.models import Profissional, Empresa
        from empresas.serializers import ProfissionalListSerializer
        from coletas.serializers import ColetaSerializer

        coleta_obj = Coleta.objects.filter(id=pk).select_related('empresa').first()
        if not coleta_obj:
            messages.error(request, 'Coleta não encontrada.')
            return redirect('web-empresa:coletas-list')

        if request.method == 'POST':
            tipo_adicao = request.POST.get('tipo_adicao')
            adicionados = 0

            if tipo_adicao == 'todos':
                profissionais = coleta_obj.empresa.profissionais.filter(is_active=True)
            elif tipo_adicao == 'departamentos':
                departamentos_ids = request.POST.getlist('departamentos_selecionados')
                profissionais = Profissional.objects.filter(empresa=coleta_obj.empresa, departamento_id__in=departamentos_ids, is_active=True)
            else:
                profissionais_ids = request.POST.getlist('profissionais_selecionados')
                profissionais = Profissional.objects.filter(usuario__in=profissionais_ids, is_active=True)

            for prof in set(profissionais):
                coleta_obj.adicionar_profissional(prof)
                adicionados += 1

            if adicionados > 0:
                coleta_obj.atualizar_totais()
                messages.success(request, f'{adicionados} profissional(is) adicionado(s) à coleta.')

            # Use the actual object PK to avoid accidental empty-string reverses
            try:
                target_pk = getattr(coleta_obj, 'pk') or pk
            except Exception:
                target_pk = pk

            if not target_pk:
                logger.warning('coleta_manage: target_pk is empty; redirecting to list')
                return redirect('web-empresa:coletas-list')

            return redirect('web-empresa:coleta-manage', pk=target_pk)

        # GET: preparar dados para template
        coleta = ColetaSerializer(coleta_obj).data

        todos_profissionais_qs = coleta_obj.empresa.profissionais.filter(is_active=True).select_related('usuario')
        profissionais_na_coleta = coleta_obj.coleta_profissionais.values_list('profissional__usuario', flat=True)
        disponiveis_qs = todos_profissionais_qs.exclude(usuario__in=profissionais_na_coleta)
        profissionais = ProfissionalListSerializer(disponiveis_qs, many=True).data

        departamentos = coleta_obj.empresa.departamentos.all()
        from coletas.serializers import ColetaListSerializer

    except Exception as e:
        logger.exception('Erro em coleta_manage: %s', e)
        messages.error(request, f'Erro: {str(e)}')
        coleta = None
        profissionais = []
        departamentos = []

    return render(request, 'empresas/coleta_manage.html', {
        'coleta': coleta,
        'profissionais': profissionais,
        'departamentos': departamentos
    })


@empresa_required
def coleta_cancelar(request, pk):
    """Cancelar coleta"""
    if request.method == 'POST':
        try:
            from coletas.models import Coleta
            coleta = Coleta.objects.filter(id=pk).first()
            if not coleta:
                messages.error(request, 'Coleta não encontrada.')
            else:
                coleta.cancelar()
                messages.success(request, 'Coleta cancelada com sucesso!')
        except Exception as e:
            logger.exception('Erro ao cancelar coleta: %s', e)
            messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-empresa:coletas-list')


@empresa_required
def coleta_apagar(request, pk):
    """Apagar coleta (soft delete - apenas marca como inativa)"""
    if request.method == 'POST':
        try:
            from coletas.models import Coleta
            coleta = Coleta.objects.filter(id=pk).first()
            if not coleta:
                messages.error(request, 'Coleta não encontrada.')
            else:
                coleta.is_active = False
                coleta.save(update_fields=['is_active'])
                messages.success(request, 'Coleta apagada com sucesso!')
        except Exception as e:
            logger.exception('Erro ao apagar coleta: %s', e)
            messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-empresa:coletas-list')


@empresa_required
def coleta_exportar(request, pk):
    """Exportar dados da coleta para Excel"""
    try:
        from rest_framework.request import Request as DRFRequest
        from coletas.views import ColetaViewSet
        from django.http import HttpResponse

        base_request = getattr(request, '_request', request)
        drf_request = DRFRequest(base_request)
        drf_request.user = request.user

        viewset = ColetaViewSet()
        viewset.request = drf_request
        viewset.kwargs = {'pk': pk}

        resp = viewset.exportar_excel(drf_request, pk=pk)
        if hasattr(resp, 'content'):
            return resp
        else:
            data = getattr(resp, 'data', {}) or {}
            messages.error(request, data.get('error', 'Erro ao exportar dados da coleta.'))
            return redirect('web-empresa:coleta-detail', pk=pk)
    except Exception as e:
        logger.exception('Erro ao exportar coleta: %s', e)
        messages.error(request, f'Erro: {str(e)}')
        return redirect('web-empresa:coleta-detail', pk=pk)


@empresa_required
def coleta_exportar_dados_textuais(request, pk):
    """Exportar dados textuais da coleta"""
    try:
        from rest_framework.request import Request as DRFRequest
        from coletas.views import ColetaViewSet
        from django.http import HttpResponse

        base_request = getattr(request, '_request', request)
        drf_request = DRFRequest(base_request)
        drf_request.user = request.user

        viewset = ColetaViewSet()
        viewset.request = drf_request
        viewset.kwargs = {'pk': pk}

        resp = viewset.exportar_dados_textuais(drf_request, pk=pk)
        if hasattr(resp, 'content'):
            return resp
        else:
            data = getattr(resp, 'data', {}) or {}
            messages.error(request, data.get('error', 'Nenhuma resposta concluída encontrada.'))
            return redirect('web-empresa:coleta-detail', pk=pk)
    except Exception as e:
        logger.exception('Erro ao exportar dados textuais: %s', e)
        messages.error(request, f'Erro: {str(e)}')
        return redirect('web-empresa:coleta-detail', pk=pk)


@empresa_required
def coleta_exportar_participantes(request, pk):
    """Exportar participantes em CSV"""
    try:
        from rest_framework.request import Request as DRFRequest
        from coletas.views import ColetaViewSet
        from django.http import HttpResponse

        base_request = getattr(request, '_request', request)
        drf_request = DRFRequest(base_request)
        drf_request.user = request.user

        viewset = ColetaViewSet()
        viewset.request = drf_request
        viewset.kwargs = {'pk': pk}

        resp = viewset.exportar_participantes_excel(drf_request, pk=pk)
        if hasattr(resp, 'content'):
            return resp
        else:
            data = getattr(resp, 'data', {}) or {}
            messages.error(request, data.get('error', 'Erro ao exportar participantes (Excel).'))
            return redirect('web-empresa:coleta-detail', pk=pk)
    except Exception as e:
        logger.exception('Erro ao exportar participantes: %s', e)
        messages.error(request, f'Erro: {str(e)}')
        return redirect('web-empresa:coleta-detail', pk=pk)


@empresa_required
def coleta_exportar_midias(request, pk):
    """Exportar mídias em ZIP"""
    try:
        from rest_framework.request import Request as DRFRequest
        from coletas.views import ColetaViewSet
        from django.http import HttpResponse
        base_request = getattr(request, '_request', request)
        drf_request = DRFRequest(base_request)
        drf_request.user = request.user

        viewset = ColetaViewSet()
        viewset.request = drf_request
        viewset.kwargs = {'pk': pk}

        resp = viewset.exportar_midias(drf_request, pk=pk)
        if hasattr(resp, 'content'):
            return resp
        else:
            data = getattr(resp, 'data', {}) or {}
            messages.error(request, data.get('error', 'Nenhuma mídia encontrada.'))
            return redirect('web-empresa:coleta-detail', pk=pk)
    except Exception as e:
        # Log and attempt HTTP fallback to API endpoint
        logger.exception('Erro ao exportar mídias via ViewSet: %s', e)
        try:
            import requests
            access_token = request.session.get('access_token')
            headers = {'Authorization': f'Bearer {access_token}'} if access_token else {}
            api_url = f'http://127.0.0.1:8000/api/v1/coletas/{pk}/exportar_midias/'
            r = requests.get(api_url, headers=headers, stream=True, timeout=60)
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

    return redirect('web-empresa:coleta-detail', pk=pk)


@empresa_required
def coleta_remover_participante(request, pk):
    """Remover participante de uma coleta"""
    if request.method == 'POST':
        profissional_id = request.POST.get('profissional_id')
        try:
            from coletas.models import Coleta, ColetaProfissional
            coleta = Coleta.objects.filter(id=pk).first()
            if not coleta:
                messages.error(request, 'Coleta não encontrada.')
            else:
                cp = ColetaProfissional.objects.filter(coleta=coleta, profissional_id=profissional_id).first()
                if not cp:
                    messages.error(request, 'Participante não encontrado nesta coleta')
                else:
                    nome = cp.profissional.nome
                    cp.delete()
                    coleta.atualizar_totais()
                    messages.success(request, 'Participante removido com sucesso!')
        except Exception as e:
            logger.exception('Erro ao remover participante: %s', e)
            messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-empresa:coleta-detail', pk=pk)


@empresa_required
def coleta_refazer(request, pk):
    """Refazer coleta (apagar todas as respostas e reabrir)"""
    if request.method == 'POST':
        try:
            from coletas.models import Coleta, RespostaColeta
            coleta = Coleta.objects.filter(id=pk).first()
            if not coleta:
                messages.error(request, 'Coleta não encontrada.')
            else:
                # Apenas permitir refazer se concluída ou cancelada
                if coleta.status not in ['concluida', 'cancelada']:
                    messages.error(request, 'Apenas coletas concluídas ou canceladas podem ser refeitas')
                else:
                    respostas_count = 0
                    participantes_count = 0
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
        except Exception as e:
            logger.exception('Erro ao refazer coleta: %s', e)
            messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-empresa:coleta-detail', pk=pk)


@empresa_required
def coleta_refazer_individual(request, pk):
    """Permitir que um profissional específico refaça o formulário"""
    if request.method == 'POST':
        profissional_id = request.POST.get('profissional_id')
        try:
            from coletas.models import Coleta, ColetaProfissional
            coleta = Coleta.objects.filter(id=pk).first()
            if not coleta:
                messages.error(request, 'Coleta não encontrada.')
            else:
                cp = ColetaProfissional.objects.filter(coleta=coleta, profissional_id=profissional_id).first()
                if not cp:
                    messages.error(request, 'Participante não encontrado nesta coleta')
                else:
                    if hasattr(cp, 'resposta'):
                        resposta = cp.resposta
                        if hasattr(resposta, 'foto'):
                            resposta.foto.delete()
                        if hasattr(resposta, 'assinatura'):
                            resposta.assinatura.delete()
                        resposta.delete()
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
        except Exception as e:
            logger.exception('Erro ao permitir refazer individual: %s', e)
            messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-empresa:coleta-detail', pk=pk)


@empresa_required
def logs_auditoria(request):
    """Página de logs de auditoria"""
    try:
        from auditoria.models import LogAuditoria
        from auditoria.serializers import LogAuditoriaSerializer

        qs = LogAuditoria.objects.all().order_by('-data_hora')[:200]
        logs = LogAuditoriaSerializer(qs, many=True).data
    except Exception as e:
        logger.exception('Erro ao carregar logs de auditoria: %s', e)
        messages.error(request, f'Erro: {str(e)}')
        logs = []

    return render(request, 'empresas/logs_auditoria.html', {
        'logs': logs
    })
