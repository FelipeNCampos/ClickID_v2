"""
Views web para coleta (profissional)
"""
from django.shortcuts import render, redirect
from django.contrib import messages
import requests

import json
from django.utils.dateparse import parse_datetime
import logging
import base64
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.urls import reverse

# Logger para debug temporário
logger = logging.getLogger('django')


def coleta_acesso(request, token):
    """Página de acesso à coleta via token"""
    try:
        # Validar token localmente (token here is expected to be ColetaProfissional.id)
        from .models import ColetaProfissional
        from .serializers import ColetaProfissionalSerializer

        cp = ColetaProfissional.objects.select_related('coleta', 'profissional').filter(id=token).first()
        if not cp:
            messages.error(request, 'Token inválido ou expirado')
            return render(request, 'coletas/erro.html')

        coleta_prof = ColetaProfissionalSerializer(cp).data
        # Armazenar token na sessão
        request.session['coleta_token'] = token
        request.session['coleta_profissional_id'] = coleta_prof['id']
        return render(request, 'coletas/acesso.html', {'coleta_prof': coleta_prof})
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        return render(request, 'coletas/erro.html')


def coleta_preencher(request, token):
    """Formulário de preenchimento da coleta"""
    if request.session.get('coleta_token') != token:
        messages.error(request, 'Acesso não autorizado')
        return redirect('web-coleta:acesso', token=token)
    
    try:
        # Buscar dados da coleta localmente via ORM
        from .models import ColetaProfissional
        from .serializers import ColetaProfissionalSerializer
        cp_obj = ColetaProfissional.objects.select_related('coleta__modelo', 'profissional').filter(id=token).first()
        if not cp_obj:
            messages.error(request, 'Coleta não encontrada')
            return render(request, 'coletas/erro.html')

        coleta_prof = ColetaProfissionalSerializer(cp_obj).data

        # Buscar modelo e campos via ORM
        modelo = None
        api_campos = []
        try:
            modelo_obj = cp_obj.coleta.modelo
            if modelo_obj:
                # tentar serializar modelo se existir serializer
                try:
                    from modelos.serializers import ModeloCartaoSerializer
                    modelo = ModeloCartaoSerializer(modelo_obj).data
                except Exception:
                    modelo = {'id': str(modelo_obj.id), 'nome': getattr(modelo_obj, 'nome', '')}

                # campos ORM
                from modelos.models import CampoCartao
                orm_campos = list(CampoCartao.objects.filter(modelo_id=modelo_obj.id).order_by('ordem'))
                api_campos = []
                for oc in orm_campos:
                    api_campos.append({
                        'id': str(oc.id),
                        'nome': oc.nome_campo,
                        'nome_campo': oc.nome_campo,
                        'obrigatorio': oc.obrigatorio,
                        'tipo': oc.tipo,
                        'pergunta_formulario': oc.pergunta_formulario,
                        'placeholder': oc.placeholder,
                        'opcoes': oc.opcoes,
                    })
        except Exception:
            api_campos = []

            # Se não houver campos definidos no modelo, mas a coleta foi configurada
            # para aceitar apenas Dados/Foto/Assinatura (ex.: "Dados Extras + Foto"),
            # criamos campos sintéticos para que o template sempre receba alguma
            # pergunta a ser renderizada no fluxo de preenchimento.
            raw_campos = api_campos
            if not raw_campos:
                try:
                    coleta_info = coleta_prof.get('coleta', {}) if isinstance(coleta_prof, dict) else {}
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

            # normalizar tipos e filtrar cpf/nome
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

            campos_filtrados = []
            for c in raw_campos:
                nome = (c.get('nome') or c.get('nome_campo') or '').strip().lower()
                if nome in ('cpf', 'nome'):
                    continue
                c['tipo_campo'] = _normalize_tipo(c)
                campos_filtrados.append(c)

            # Attach filtered campos to modelo so template receives them
            if modelo is None:
                modelo = {}
            modelo['campos'] = campos_filtrados

            if request.method == 'POST':
                # Processar envio
                # Suportar tanto form-encoded (request.POST / request.FILES)
                # quanto JSON enviado via fetch (application/json)

                respostas_payload = []

                def _append_resposta(campo_id, valor):
                    if valor is None:
                        return
                    # Para listas (múltipla escolha) serializar como JSON-compatível
                    if isinstance(valor, (list, tuple)):
                        # Remover itens vazios
                        cleaned = [v for v in valor if v is not None and str(v) != '']
                        if not cleaned:
                            return
                        respostas_payload.append({
                            'campo_id': str(campo_id),
                            'valor': cleaned
                        })
                    else:
                        if str(valor).strip() == '':
                            return
                        respostas_payload.append({
                            'campo_id': str(campo_id),
                            'valor': valor
                        })

                # Caso JSON (fetch SPA)
                if request.content_type and 'application/json' in request.content_type:
                    try:
                        body = json.loads(request.body.decode('utf-8') or '{}')
                    except Exception:
                        body = {}

                    # Aceitar duas formas comuns: lista de respostas ou mapa {campo_id: valor}
                    respostas_from_body = body.get('respostas')
                    if isinstance(respostas_from_body, list):
                        for r in respostas_from_body:
                            cid = r.get('campo_id') or r.get('campo') or r.get('id')
                            val = r.get('valor') if 'valor' in r else r.get('valor_texto') if 'valor_texto' in r else None
                            if cid is not None:
                                _append_resposta(cid, val)
                    elif isinstance(respostas_from_body, dict):
                        # mapa campo_id -> valor
                        for cid, val in respostas_from_body.items():
                            _append_resposta(cid, val)
                    else:
                        # Fallback: some frontends send respostas keyed by campo id at root
                        for campo in modelo.get('campos', []):
                            cid = campo.get('id')
                            val = body.get(str(cid)) or body.get(f'campo_{cid}')
                            _append_resposta(cid, val)

                    # Capturar foto/assinatura enviados em base64 no JSON (mantido abaixo)
                else:
                    # Form tradicional (fallback)
                    for campo in modelo.get('campos', []):
                        campo_id = campo['id']
                        tipo = campo.get('tipo_campo') or campo.get('tipo') or ''

                        if tipo in ('texto', 'texto_longo', 'numero', 'data', 'escolha_unica'):
                            # Aceita 'campo_<id>' ou '<id>' como nome de campo
                            valor = request.POST.get(f'campo_{campo_id}')
                            if valor is None:
                                valor = request.POST.get(str(campo_id))
                            _append_resposta(campo_id, valor)
                        elif tipo == 'multipla_escolha':
                            # Múltiplos valores
                            valores = request.POST.getlist(f'campo_{campo_id}') or request.POST.getlist(str(campo_id))
                            _append_resposta(campo_id, valores)
                        elif tipo == 'foto':
                            # Upload será tratado separadamente; se houver arquivo, não colocamos como resposta de campo
                            if request.FILES.get(f'campo_{campo_id}'):
                                # Attach to top-level foto later
                                pass

                # respostas_payload agora contém lista com {'campo_id','valor'} conforme esperado pelo serializer

                data = {
                    'coleta_profissional_id': coleta_prof['id'],
                    'respostas': respostas_payload
                }
                try:
                    # If frontend sent foto/assinatura in JSON (base64), capture them to save locally after saving
                    foto_base64 = None
                    assinatura_base64 = None
                    if request.content_type and 'application/json' in request.content_type:
                        try:
                            body = json.loads(request.body.decode('utf-8') or '{}')
                        except Exception:
                            body = {}
                        foto_base64 = body.get('foto')
                        assinatura_base64 = body.get('assinatura')

                    # Create resposta locally using the serializer (bypass API)
                    try:
                        from .serializers import RespostaColetaCreateSerializer
                        from coletas.models import Foto, Assinatura

                        serializer = RespostaColetaCreateSerializer(data=data)
                        if serializer.is_valid():
                            resposta_obj = serializer.save()

                            # If there are base64 media parts, save them via ORM
                            if (foto_base64 or assinatura_base64):
                                try:
                                    coleta_prof_obj = resposta_obj.coleta_profissional

                                    if foto_base64:
                                        try:
                                            fb = foto_base64
                                            if 'base64,' in fb:
                                                fb = fb.split('base64,')[1]
                                            foto_data = base64.b64decode(fb)
                                            foto_file = ContentFile(foto_data, name=f'{coleta_prof_obj.profissional.cpf.replace(".","").replace("-","")}_foto.jpg')
                                            foto_obj, _ = Foto.objects.get_or_create(resposta_coleta=resposta_obj)
                                            foto_obj.arquivo = foto_file
                                            foto_obj.tamanho = len(foto_data)
                                            foto_obj.formato = 'jpg'
                                            foto_obj.save()
                                        except Exception as e:
                                            logger.error(f'Erro salvando foto base64: {str(e)}')

                                    if assinatura_base64:
                                        try:
                                            ab = assinatura_base64
                                            if 'base64,' in ab:
                                                ab = ab.split('base64,')[1]
                                            assinatura_data = base64.b64decode(ab)
                                            assinatura_file = ContentFile(assinatura_data, name=f'{coleta_prof_obj.profissional.cpf.replace(".","").replace("-","")}_assinatura.png')
                                            assinatura_obj, _ = Assinatura.objects.get_or_create(resposta_coleta=resposta_obj)
                                            assinatura_obj.arquivo = assinatura_file
                                            assinatura_obj.tamanho = len(assinatura_data)
                                            assinatura_obj.formato = 'png'
                                            assinatura_obj.save()
                                        except Exception as e:
                                            logger.error(f'Erro salvando assinatura base64: {str(e)}')
                                except Exception as e:
                                    logger.error(f'Erro ao associar mídias via ORM: {str(e)}')

                            # Se request JSON, retornar JSON com redirect
                            if request.content_type and 'application/json' in request.content_type:
                                redirect_url = reverse('web-coleta:confirmar', args=[token])
                                return JsonResponse({'redirect_url': redirect_url}, status=201)
                            return redirect('web-coleta:confirmar', token=token)
                        else:
                            # Se for JSON, retornar erros em JSON para o frontend
                            if request.content_type and 'application/json' in request.content_type:
                                return JsonResponse({'errors': serializer.errors}, status=400)
                            messages.error(request, f'Erro ao salvar resposta: {serializer.errors}')
                    except Exception as e:
                        logger.error(f'Erro ao salvar via serializer: {str(e)}')
                        if request.content_type and 'application/json' in request.content_type:
                            return JsonResponse({'error': str(e)}, status=500)
                        messages.error(request, f'Erro: {str(e)}')
                except Exception as e:
                    messages.error(request, f'Erro: {str(e)}')
            
            return render(request, 'coletas/preencher.html', {
                'coleta_prof': coleta_prof,
                'modelo': modelo
            })
        else:
            messages.error(request, 'Coleta não encontrada')
            return render(request, 'coletas/erro.html')
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        return render(request, 'coletas/erro.html')


def coleta_confirmar(request, token):
    """Página de confirmação dos dados"""
    if request.session.get('coleta_token') != token:
        messages.error(request, 'Acesso não autorizado')
        return redirect('web-coleta:acesso', token=token)
    
    try:
        # Buscar resposta localmente
        coleta_prof_id = request.session.get('coleta_profissional_id')
        from .models import RespostaColeta

        respostas_qs = RespostaColeta.objects.filter(coleta_profissional_id=coleta_prof_id).order_by('-created_at')
        resposta_obj = respostas_qs.first()

        if not resposta_obj:
            messages.error(request, 'Resposta não encontrada')
            return render(request, 'coletas/erro.html')

        # Serializar resposta para template simples
        try:
            from .serializers import RespostaColetaSerializer
            resposta = RespostaColetaSerializer(resposta_obj).data
        except Exception:
            resposta = {'id': str(resposta_obj.id)}

        if request.method == 'POST':
            # Finalizar resposta
            if request.POST.get('confirmar') == 'sim':
                try:
                    resposta_obj.coleta_profissional.finalizar()
                    return redirect('web-coleta:sucesso', token=token)
                except Exception:
                    messages.error(request, 'Erro ao finalizar')
            else:
                return redirect('web-coleta:preencher', token=token)

        return render(request, 'coletas/confirmar.html', {'resposta': resposta})
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        return render(request, 'coletas/erro.html')


def coleta_sucesso(request, token):
    """Página de sucesso"""
    request.session.flush()
    return render(request, 'coletas/sucesso.html')


def participante_respostas(request, coleta_id, usuario_id):
    """Visualizar respostas de um participante de uma coleta"""
    try:
        from coletas.models import Coleta, RespostaColeta
        from empresas.models import Profissional
        from .serializers import RespostaColetaSerializer

        coleta = Coleta.objects.filter(id=coleta_id).first()
        participante_obj = Profissional.objects.select_related('usuario').filter(usuario__pk=usuario_id).first()

        respostas_qs = RespostaColeta.objects.filter(coleta_profissional__coleta_id=coleta_id, coleta_profissional__profissional__usuario__pk=usuario_id).order_by('-created_at')
        respostas = []
        for r in respostas_qs:
            try:
                respostas.append(RespostaColetaSerializer(r).data)
            except Exception:
                respostas.append({'id': str(r.id), 'created_at': r.created_at})

        # Converter datas (já objetos) - templates lidarão com formatação
    except Exception as e:
        messages.error(request, f'Erro ao buscar respostas: {str(e)}')
        return redirect('web-empresa:coleta-detail', coleta_id=coleta_id)

    return render(request, 'empresas/participante_respostas.html', {
        'coleta': coleta,
        'participante': participante_obj,
        'respostas': respostas
    })
