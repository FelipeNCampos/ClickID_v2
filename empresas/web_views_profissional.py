"""
Views web para Profissional
Interface para profissionais preencherem formulários com login por CPF
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from functools import wraps
from django.contrib.auth import authenticate, login
from rest_framework_simplejwt.tokens import RefreshToken
import logging
import json


def profissional_login_required(view_func):
    """Decorator para verificar se profissional está logado"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        token = request.session.get('prof_access_token')
        logger = logging.getLogger(__name__)
        try:
            token_prefix = token[:8] + '...' if token else ''
        except Exception:
            token_prefix = ''
        # ...removed debug print...
        if not token:
            messages.warning(request, 'Você precisa fazer login primeiro')
            return redirect('profissional:login')
        
        # Verificar se a empresa do profissional está ativa
        try:
            from .models import Profissional, Empresa
            user_id = request.session.get('prof_user_id')
            if user_id:
                profissional = Profissional.objects.select_related('empresa').get(usuario_id=user_id)
                if not profissional.empresa.is_active:
                    messages.error(request, 'Sua empresa está desativada. Entre em contato com o administrador.')
                    # Fazer logout
                    request.session.pop('prof_access_token', None)
                    request.session.pop('prof_user_id', None)
                    request.session.pop('prof_cpf', None)
                    request.session.pop('prof_empresa_id', None)
                    return redirect('profissional:login')
        except Profissional.DoesNotExist:
            messages.error(request, 'Profissional não encontrado.')
            return redirect('profissional:login')
        
        return view_func(request, *args, **kwargs)
    return wrapper


# Logger para debug temporário
logger = logging.getLogger(__name__)


def profissional_login(request):
    """Login para profissional com CPF"""
    if request.method == 'POST':
        cpf = request.POST.get('cpf', '').replace('.', '').replace('-', '').replace('/', '').strip()
        senha = request.POST.get('senha', '').strip()
        
        if not cpf or not senha:
            messages.error(request, 'CPF e senha são obrigatórios.')
            return render(request, 'profissional/login.html')
        
        try:
            # Buscar profissional pelo CPF
            from .models import Profissional
            try:
                profissional = Profissional.objects.select_related('usuario', 'empresa').get(
                    cpf=cpf,
                    is_active=True
                )
            except Profissional.DoesNotExist:
                messages.error(request, 'CPF ou senha inválidos.')
                return render(request, 'profissional/login.html')
            
            # Verificar se a empresa está ativa
            if not profissional.empresa.is_active:
                messages.error(request, 'Sua empresa está desativada. Entre em contato com o administrador.')
                return render(request, 'profissional/login.html')

            # Impedir login se o profissional já finalizou todas as coletas (nenhuma pendente)
            try:
                from coletas.models import ColetaProfissional
                has_pending = ColetaProfissional.objects.filter(
                    profissional=profissional,
                    status__in=['pendente', 'em_progresso', 'em_andamento']
                ).exists()
                if not has_pending:
                    messages.error(request, 'Você já finalizou as coletas designadas; não é possível efetuar login novamente.')
                    return render(request, 'profissional/login.html')
            except Exception:
                # If anything goes wrong when checking coletas, log and continue with normal flow
                logger.exception('Erro verificando coletas pendentes para profissional %s', getattr(profissional, 'cpf', ''))
            
            # Autenticar localmente usando o email do usuário (evita chamadas internas HTTP)
            email = profissional.usuario.email
            try:
                user = authenticate(request, username=email, password=senha)
                if user is not None:
                    # Verificar se é profissional
                    if getattr(user, 'tipo_usuario', '') == 'profissional':
                        # Double-check pending coletas using the authenticated user to avoid bypass
                        try:
                            from empresas.models import Profissional as ProfissionalModel
                            from coletas.models import ColetaProfissional
                            prof_obj = ProfissionalModel.objects.select_related('usuario', 'empresa').filter(usuario=user, is_active=True).first()
                            if not prof_obj:
                                messages.error(request, 'Acesso negado. Profissional não encontrado.')
                                return render(request, 'profissional/login.html')

                            has_pending = ColetaProfissional.objects.filter(
                                profissional=prof_obj,
                                status__in=['pendente', 'em_progresso']
                            ).exists()
                            if not has_pending:
                                messages.error(request, 'Você já finalizou as coletas designadas; não é possível efetuar login novamente.')
                                return render(request, 'profissional/login.html')
                        except Exception:
                            logger.exception('Erro ao verificar coletas pendentes após autenticação')
                            messages.error(request, 'Erro ao verificar coletas pendentes. Tente novamente mais tarde.')
                            return render(request, 'profissional/login.html')

                        # All checks passed — log the user in
                        login(request, user)
                        refresh = RefreshToken.for_user(user)
                        access = str(refresh.access_token)
                        request.session['prof_access_token'] = access
                        request.session['prof_refresh_token'] = str(refresh)
                        request.session['prof_user_id'] = str(profissional.usuario.pk)
                        request.session['prof_cpf'] = cpf
                        request.session['prof_empresa_id'] = str(profissional.empresa.usuario.pk)
                        # Store company public url if available
                        request.session['prof_empresa_url'] = getattr(profissional.empresa, 'url_personalizada', '') or getattr(profissional.empresa, 'url', '')
                        messages.success(request, f'Bem-vindo, {profissional.nome}!')
                        return redirect('profissional:dashboard')
                    else:
                        messages.error(request, 'Acesso negado. Esta área é apenas para profissionais.')
                else:
                    messages.error(request, 'CPF ou senha inválidos.')
            except Profissional.DoesNotExist:
                messages.error(request, 'CPF ou senha inválidos.')
            except Exception:
                messages.error(request, 'CPF ou senha inválidos.')
        except Exception:
            messages.error(request, 'CPF ou senha inválidos.')
    
    return render(request, 'profissional/login.html')


def profissional_logout(request):
    """Logout do profissional"""
    # Capturar URL da empresa antes de limpar sessão
    empresa_url = request.session.get('prof_empresa_url')
    
    request.session.pop('prof_access_token', None)
    request.session.pop('prof_user_id', None)
    request.session.pop('prof_cpf', None)
    request.session.pop('prof_empresa_id', None)
    request.session.pop('prof_empresa_url', None)
    
    messages.success(request, 'Logout realizado com sucesso!')
    
    # Redirecionar para página personalizada da empresa
    if empresa_url:
        # Usar redirect direto com URL construída manualmente
        return redirect(f'/{empresa_url}/')
    
    # Fallback para login padrão
    return redirect('profissional:login')


@profissional_login_required
def profissional_dashboard(request):
    """Dashboard do profissional com coletas pendentes e histórico"""
    headers = {'Authorization': f'Bearer {request.session.get("prof_access_token")}'}
    user_id = request.session.get('prof_user_id')
    
    context = {
        'coletas_pendentes': [],
        'coletas_concluidas': [],
        'precisa_alterar_senha': False,
        'profissional': {'nome': ''},  # Fallback vazio
        'empresa': {}  # Dados da empresa
    }
    
    try:
        # Buscar dados do profissional via ORM/serializers (evita chamadas HTTP internas)
        from empresas.models import Profissional as ProfissionalModel
        from empresas.serializers import ProfissionalSerializer, EmpresaSerializer
        from coletas.models import ColetaProfissional
        from coletas.serializers import ColetaProfissionalSerializer

        profissional_obj = None
        if user_id:
            profissional_obj = ProfissionalModel.objects.select_related('usuario', 'empresa').filter(usuario__pk=user_id).first()

        if profissional_obj:
            try:
                profissional_data = ProfissionalSerializer(profissional_obj).data
            except Exception:
                profissional_data = {
                    'usuario': str(profissional_obj.usuario.pk),
                    'nome': getattr(profissional_obj, 'nome', '') or getattr(profissional_obj.usuario, 'email', 'Profissional')
                }

            context['profissional'] = profissional_data
            context['profissional']['nome'] = profissional_data.get('nome') or 'Profissional'
            context['precisa_alterar_senha'] = profissional_data.get('precisa_alterar_senha', False)

            # Empresa
            empresa = profissional_obj.empresa
            if empresa:
                try:
                    context['empresa'] = EmpresaSerializer(empresa).data
                except Exception:
                    context['empresa'] = {'id': str(empresa.usuario.pk), 'nome': getattr(empresa, 'razao_social', '')}

            # Coletas-profissionais do profissional
            # ColetaProfissional does not have `created_at`; order by when the profissional started the coleta
            # fallback to coleta.created_at so recent coletas appear first
            coletas_qs = ColetaProfissional.objects.filter(
                profissional=profissional_obj
            ).select_related('coleta').order_by('-data_inicio', '-coleta__created_at')
            coletas = []
            for cp in coletas_qs:
                try:
                    cp_data = ColetaProfissionalSerializer(cp).data
                except Exception:
                    cp_data = {'id': str(cp.id), 'status': getattr(cp, 'status', ''), 'coleta': str(getattr(cp, 'coleta_id', ''))}
                coletas.append(cp_data)

            for coleta in coletas:
                status = (coleta.get('status') or '').lower()
                if status in ['pendente', 'em_progresso', 'em_andamento']:
                    context['coletas_pendentes'].append(coleta)
                elif status in ['concluido', 'concluida', 'aprovada']:
                    context['coletas_concluidas'].append(coleta)

    except Exception as e:
        # Log full exception with traceback to help debugging in container logs
        logger.exception('Erro ao carregar dados do dashboard')
        # Show a clearer message to the user while avoiding leaking internals
        messages.error(request, f'Erro ao carregar dados do dashboard: {str(e)}')
    
    # Redirecionar automaticamente se houver apenas 1 coleta pendente
    if not context['precisa_alterar_senha'] and len(context['coletas_pendentes']) == 1:
        coleta_id = context['coletas_pendentes'][0].get('id')
        if coleta_id:
            return redirect('profissional:coleta-preencher', pk=coleta_id)

    # If there are NO pending coletas, instruct template to show logout popup
    if not context['precisa_alterar_senha'] and len(context['coletas_pendentes']) == 0:
        context['force_logout_popup'] = True
    
    return render(request, 'profissional/dashboard.html', context)


@profissional_login_required
def profissional_alterar_senha(request):
    """Alterar senha do profissional"""
    # Change-password for professionals is disabled by policy.
    messages.info(request, 'Alteração de senha não está disponível. Entre em contato com a empresa se precisar de suporte.')
    return redirect('profissional:dashboard')


@profissional_login_required
def profissional_coleta_detail(request, pk):
    """Detalhes de uma coleta"""
    headers = {'Authorization': f'Bearer {request.session.get("prof_access_token")}'}
    
    try:
        from coletas.models import Coleta
        from coletas.serializers import ColetaSerializer
        coleta_obj = Coleta.objects.filter(id=pk).first()
        if coleta_obj:
            try:
                coleta = ColetaSerializer(coleta_obj).data
            except Exception:
                coleta = {'id': str(coleta_obj.id), 'nome': getattr(coleta_obj, 'nome', '')}
        else:
            coleta = None
    except Exception as e:
        messages.error(request, f'Erro ao carregar coleta: {str(e)}')
        coleta = None
    
    return render(request, 'profissional/coleta_detail.html', {'coleta': coleta})


@profissional_login_required
def profissional_coleta_preencher(request, pk):
    """Preencher formulário de coleta"""
    headers = {'Authorization': f'Bearer {request.session.get("prof_access_token")}'}
    user_id = request.session.get('prof_user_id')
    logger = logging.getLogger('coletas')
    context = {
        'coleta_profissional': {},
        'modelo': None,
        'campos': [],
        'empresa': {},
        'profissional': {}
    }
    
    try:
        # Buscar dados do profissional, empresa e ColetaProfissional via ORM/serializers
        from empresas.models import Profissional as ProfissionalModel
        from empresas.serializers import ProfissionalSerializer, EmpresaSerializer
        from coletas.models import ColetaProfissional, Coleta
        from coletas.serializers import ColetaProfissionalSerializer, ColetaSerializer
        from modelos.models import CampoCartao, ModeloCartao

        profissional_obj = ProfissionalModel.objects.select_related('usuario', 'empresa').filter(usuario__pk=user_id).first()
        if profissional_obj:
            try:
                context['profissional'] = ProfissionalSerializer(profissional_obj).data
            except Exception:
                context['profissional'] = {'usuario': str(profissional_obj.usuario.pk), 'nome': getattr(profissional_obj, 'nome', '')}

            empresa = profissional_obj.empresa
            if empresa:
                try:
                    context['empresa'] = EmpresaSerializer(empresa).data
                except Exception:
                    context['empresa'] = {'id': str(empresa.usuario.pk), 'nome': getattr(empresa, 'razao_social', '')}

        coleta_prof_obj = ColetaProfissional.objects.select_related('coleta', 'profissional').filter(id=pk).first()
        if coleta_prof_obj:
            try:
                coleta_prof = ColetaProfissionalSerializer(coleta_prof_obj).data
            except Exception:
                coleta_prof = {'id': str(coleta_prof_obj.id)}
            context['coleta_profissional'] = coleta_prof

            coleta_obj = coleta_prof_obj.coleta
            try:
                context['coleta_profissional']['coleta'] = ColetaSerializer(coleta_obj).data
            except Exception:
                context['coleta_profissional']['coleta'] = {'id': str(getattr(coleta_obj, 'id', '')), 'nome': getattr(coleta_obj, 'nome', '')}

            modelo_obj = getattr(coleta_obj, 'modelo', None)
            modelo_id = modelo_obj.id if modelo_obj else None
            if modelo_id and modelo_obj:
                try:
                    context['modelo'] = {
                        'id': str(modelo_obj.id),
                        'nome': modelo_obj.nome
                    }
                except Exception:
                    context['modelo'] = None

                # Buscar campos do modelo via ORM
                orm_qs = CampoCartao.objects.filter(modelo_id=modelo_id).order_by('ordem')
                raw_campos = []
                for oc in orm_qs:
                    raw_campos.append({
                        'id': str(oc.id),
                        'nome': oc.nome_campo,
                        'nome_campo': oc.nome_campo,
                        'obrigatorio': oc.obrigatorio,
                        'tipo': oc.tipo,
                        'pergunta_formulario': oc.pergunta_formulario,
                        'placeholder': oc.placeholder,
                        'opcoes': oc.opcoes,
                    })

                # Filtrar campos que são mapeados para CPF/NOME — não precisamos mostrá-los nos dados adicionais
                # Se não houver campos no modelo, mas a coleta aceita apenas foto/dados/assinatura,
                # criar campos sintéticos para que o template possa renderizar os passos corretamente.
                if not raw_campos:
                    try:
                        coleta_info = context.get('coleta_profissional', {}).get('coleta', {}) or {}
                        synthetic = []
                        if coleta_info.get('include_dados'):
                            synthetic.append({
                                'id': 'dados_extras',
                                'nome': 'Dados adicionais',
                                'nome_campo': 'dados_adicionais',
                                'obrigatorio': False,
                                'tipo': 'texto_longo',
                                'pergunta_formulario': 'Dados adicionais',
                                'placeholder': 'Insira dados adicionais...'
                            })
                        if coleta_info.get('include_foto'):
                            synthetic.append({
                                'id': 'foto_coleta',
                                'nome': 'Foto',
                                'nome_campo': 'foto',
                                'obrigatorio': False,
                                'tipo': 'foto',
                                'pergunta_formulario': 'Envie sua foto',
                                'placeholder': ''
                            })
                        if coleta_info.get('include_assinatura'):
                            synthetic.append({
                                'id': 'assinatura_coleta',
                                'nome': 'Assinatura',
                                'nome_campo': 'assinatura',
                                'obrigatorio': False,
                                'tipo': 'assinatura',
                                'pergunta_formulario': 'Assinatura digital',
                                'placeholder': ''
                            })
                        if synthetic:
                            raw_campos = synthetic
                    except Exception:
                        pass

                def _normalize_tipo(campo):
                    t = (campo.get('tipo') or campo.get('tipo_campo') or '').strip().lower()
                    if 'texto_curto' in t or t == 'texto_curto' or 'texto-curto' in t:
                        return 'texto'
                    if 'texto_longo' in t or t == 'texto_longo' or 'texto-longo' in t:
                        return 'texto_longo'
                    if t in ('numero', 'number'):
                        return 'numero'
                    if t in ('data', 'date'):
                        return 'data'
                    if t in ('escolha_unica', 'selecao_unica', 'select'):
                        return 'escolha_unica'
                    if t in ('multipla_escolha', 'selecao_multipla', 'multiple_choice'):
                        return 'multipla_escolha'
                    if t in ('foto', 'imagem', 'image'):
                        return 'foto'
                    if t in ('assinatura', 'signature'):
                        return 'assinatura'
                    return t

                filtered_campos = []
                for c in raw_campos:
                    # Compatibilidade: nome do campo
                    c['nome'] = c.get('nome') or c.get('nome_campo') or c.get('pergunta_formulario') or ''
                    nome = (c.get('nome') or '').strip().lower()
                    # Ignorar campos de sistema
                    if nome in ('cpf', 'nome'):
                        continue
                    # Normalizar tipo para o template
                    tipo_campo = _normalize_tipo(c)
                    c['tipo_campo'] = tipo_campo
                    # Garantir que opcoes seja lista se aplicável
                    if tipo_campo in ('escolha_unica', 'multipla_escolha'):
                        opcoes = c.get('opcoes')
                        if isinstance(opcoes, str):
                            try:
                                c['opcoes'] = json.loads(opcoes)
                            except Exception:
                                c['opcoes'] = []
                        elif opcoes is None:
                            c['opcoes'] = []
                    filtered_campos.append(c)
                context['campos'] = filtered_campos
                try:
                    context['campos_json'] = json.dumps(filtered_campos, ensure_ascii=False)
                except Exception:
                    context['campos_json'] = '[]'
        
        # Se for POST, processar envio
        if request.method == 'POST':
            # removed local import of json to prevent UnboundLocalError
            import base64
            # removed local import of logging to prevent UnboundLocalError
            from django.http import JsonResponse
            from django.core.files.base import ContentFile
            from coletas.models import RespostaColeta, Foto, Assinatura, ColetaProfissional
            
            logger = logging.getLogger('coletas')
            
            try:
                # Parsear dados JSON
                try:
                    data = json.loads(request.body)
                except json.JSONDecodeError as e:
                    logger.error(f'Erro ao decodificar JSON: {str(e)}')
                    return JsonResponse({
                        'success': False,
                        'error': 'Dados inválidos enviados. Por favor, tente novamente.'
                    }, status=400)
                
                foto_base64 = data.get('foto')
                assinatura_base64 = data.get('assinatura')
                respostas = data.get('respostas', {})
                
                logger.info(f'Processando envio de formulário - ColetaProfissional: {pk}')
                logger.info(f'Dados recebidos - Foto: {bool(foto_base64)}, Assinatura: {bool(assinatura_base64)}, Respostas: {len(respostas)}')
                
                # Obter ColetaProfissional do banco
                try:
                    coleta_prof = ColetaProfissional.objects.select_related('coleta', 'profissional', 'profissional__usuario').get(id=pk)
                except ColetaProfissional.DoesNotExist:
                    logger.error(f'ColetaProfissional {pk} não encontrada')
                    return JsonResponse({
                        'success': False,
                        'error': 'Coleta não encontrada. Por favor, verifique se você tem acesso a esta coleta.'
                    }, status=404)
                
                # Verificar se o profissional pode enviar esta coleta
                if str(coleta_prof.profissional.usuario.pk) != str(user_id):
                    logger.error(f'Tentativa de envio por profissional não autorizado. ColetaProfissional: {pk}, User: {user_id}')
                    return JsonResponse({
                        'success': False,
                        'error': 'Você não tem permissão para enviar esta coleta.'
                    }, status=403)
                
                # Verificar se a coleta já foi finalizada
                if coleta_prof.status == 'concluido':
                    logger.warning(f'Tentativa de reenvio de coleta já finalizada: {pk}')
                    return JsonResponse({
                        'success': False,
                        'error': 'Esta coleta já foi finalizada anteriormente.'
                    }, status=400)
                
                # Criar ou obter RespostaColeta
                resposta_coleta, created = RespostaColeta.objects.get_or_create(
                    coleta_profissional=coleta_prof
                )
                logger.info(f'RespostaColeta {"criada" if created else "obtida"}: {resposta_coleta.id}')
                
                # Salvar foto
                if foto_base64:
                    try:
                        # Remover prefixo data:image/...;base64,
                        if 'base64,' in foto_base64:
                            foto_base64 = foto_base64.split('base64,')[1]
                        
                        foto_data = base64.b64decode(foto_base64)
                        foto_file = ContentFile(foto_data, name=f'{coleta_prof.profissional.cpf.replace(".", "").replace("-", "")}_foto.jpg')
                        
                        # Criar ou atualizar Foto
                        foto, _ = Foto.objects.get_or_create(resposta_coleta=resposta_coleta)
                        foto.arquivo = foto_file
                        foto.tamanho = len(foto_data)
                        foto.formato = 'jpg'
                        foto.save()
                        logger.info(f'Foto salva com sucesso - Tamanho: {len(foto_data)} bytes')
                    except Exception as e:
                        logger.error(f'Erro ao salvar foto: {str(e)}')
                        return JsonResponse({
                            'success': False,
                            'error': f'Erro ao processar foto: {str(e)}'
                        }, status=400)
                
                # Salvar assinatura
                if assinatura_base64:
                    try:
                        # Remover prefixo data:image/...;base64,
                        if 'base64,' in assinatura_base64:
                            assinatura_base64 = assinatura_base64.split('base64,')[1]
                        
                        assinatura_data = base64.b64decode(assinatura_base64)
                        assinatura_file = ContentFile(assinatura_data, name=f'{coleta_prof.profissional.cpf.replace(".", "").replace("-", "")}_assinatura.png')
                        
                        # Criar ou atualizar Assinatura
                        assinatura, _ = Assinatura.objects.get_or_create(resposta_coleta=resposta_coleta)
                        assinatura.arquivo = assinatura_file
                        assinatura.tamanho = len(assinatura_data)
                        assinatura.formato = 'png'
                        assinatura.save()
                        logger.info(f'Assinatura salva com sucesso - Tamanho: {len(assinatura_data)} bytes')
                    except Exception as e:
                        logger.error(f'Erro ao salvar assinatura: {str(e)}')
                        return JsonResponse({
                            'success': False,
                            'error': f'Erro ao processar assinatura: {str(e)}'
                        }, status=400)
                
                # Finalizar ColetaProfissional
                try:
                    coleta_prof.finalizar()
                    logger.info(f'ColetaProfissional {pk} finalizada com sucesso')
                except Exception as e:
                    logger.error(f'Erro ao finalizar ColetaProfissional: {str(e)}')
                    return JsonResponse({
                        'success': False,
                        'error': f'Erro ao finalizar coleta: {str(e)}'
                    }, status=400)
                
                # Registrar auditoria
                try:
                    from auditoria.models import LogAuditoria, TipoAcao
                    LogAuditoria.registrar(
                        usuario=request.user if request.user.is_authenticated else coleta_prof.profissional.usuario,
                        tipo_acao=TipoAcao.COLETA_CONCLUIDA,
                        descricao=f"Profissional {coleta_prof.profissional.nome} finalizou coleta '{coleta_prof.coleta.nome}'",
                        empresa=coleta_prof.coleta.empresa,
                        coleta=coleta_prof.coleta,
                        request=request
                    )
                except Exception as e:
                    # Log mas não falha
                    logger.error(f'Erro ao registrar auditoria: {str(e)}')
                
                # Capture company's public URL (if any) so we can redirect there after logout
                empresa_url = request.session.get('prof_empresa_url')
                if empresa_url:
                    # Normalize: ensure no leading/trailing slashes
                    empresa_url = empresa_url.strip().strip('/')
                    redirect_to = f'/{empresa_url}/'
                else:
                    from django.urls import reverse
                    redirect_to = reverse('profissional:login')

                # Logout profissional after successful submission (clear professional session keys)
                try:
                    # Deactivate the profissional's user account to prevent further logins
                    try:
                        prof = coleta_prof.profissional
                        if prof:
                            # deactivate profissional record
                            prof.is_active = False
                            prof.save(update_fields=['is_active'])
                            # deactivate underlying Usuario as well
                            try:
                                u = getattr(prof, 'usuario', None)
                                if u:
                                    u.is_active = False
                                    u.save(update_fields=['is_active'])
                            except Exception:
                                logger.exception('Erro ao desativar Usuario do profissional %s', getattr(prof, 'cpf', ''))

                    except Exception:
                        logger.exception('Erro ao desativar profissional após submissão')

                    request.session.pop('prof_access_token', None)
                    request.session.pop('prof_refresh_token', None)
                    request.session.pop('prof_user_id', None)
                    request.session.pop('prof_cpf', None)
                    request.session.pop('prof_empresa_id', None)
                    request.session.pop('prof_empresa_url', None)
                except Exception as e:
                    logger.error(f'Erro ao fazer logout: {str(e)}')

                return JsonResponse({
                    'success': True,
                    'message': 'Seu envio foi recebido e sua sessão foi encerrada por segurança.',
                    'redirect_url': redirect_to
                })
                
            except Exception as e:
                logger.exception('Erro inesperado ao processar formulário')
                return JsonResponse({
                    'success': False,
                    'error': f'Erro ao processar formulário: {str(e)}'
                }, status=500)
        
    except Exception as e:
        messages.error(request, f'Erro ao carregar formulário: {str(e)}')
        return redirect('profissional:dashboard')
    
    # Inject debug flag: show debug toggle when DEBUG=True or the client IP is allowed
    try:
        from django.conf import settings
        client_ip = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        allowed = getattr(settings, 'DEBUG_ALLOWED_IPS', []) or []
        context['debug'] = bool(getattr(settings, 'DEBUG', False) or (client_ip in allowed))
    except Exception:
        context['debug'] = bool(getattr(__import__('django.conf').conf.settings, 'DEBUG', False))

    return render(request, 'profissional/coleta_preencher.html', context)
