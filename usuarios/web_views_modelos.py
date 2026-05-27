"""
Views web para gerenciamento de modelos pelo gerente
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from functools import wraps

from empresas.models import Empresa
from modelos.models import ModeloCartao, CampoCartao
from modelos.serializers import (
    ModeloCartaoListSerializer, ModeloCartaoSerializer,
    ModeloCartaoCreateSerializer, CampoCartaoListSerializer
)
from empresas import serializers as empresas_serializers
from django.db import transaction


def gerente_required(view_func):
    """Decorator para garantir que apenas gerentes acessem rotas administrativas"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('access_token'):
            messages.warning(request, 'Você precisa fazer login primeiro')
            return redirect('web-gerente:login')
        
        # Verificar se o usuário é gerente
        if request.user.is_authenticated and request.user.tipo_usuario != 'gerente':
            messages.error(request, 'Acesso negado. Área restrita para gerentes.')
            return redirect('web-empresa:dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


@gerente_required
def modelos_list(request, empresa_pk):
    """Listar modelos de uma empresa"""
    try:
        empresa_obj = get_object_or_404(Empresa, usuario__id=empresa_pk)
        empresa = empresas_serializers.EmpresaSerializer(empresa_obj, context={'request': request}).data
        empresa['id'] = empresa.get('usuario', {}).get('id', empresa_pk)

        modelos_qs = ModeloCartao.objects.filter(empresa=empresa_obj).order_by('-created_at')
        modelos = ModeloCartaoListSerializer(modelos_qs, many=True).data
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        empresa = None
        modelos = []
    
    return render(request, 'gerente/modelos_list.html', {
        'empresa': empresa,
        'modelos': modelos
    })


@gerente_required
def modelo_create(request, empresa_pk):
    """Criar novo modelo para empresa"""
    if request.method == 'POST':
        try:
            data = request.POST.dict()
            data['empresa'] = str(empresa_pk)
            data['largura_mm'] = float(data.get('largura_mm', 85.6))
            data['altura_mm'] = float(data.get('altura_mm', 54.0))
            data['is_active'] = False

            serializer = ModeloCartaoCreateSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                modelo = serializer.save()
                # handle possible files
                if 'background_image' in request.FILES:
                    modelo.background_image = request.FILES['background_image']
                if 'background_image_verso' in request.FILES:
                    modelo.background_image_verso = request.FILES['background_image_verso']
                modelo.save()
                messages.success(request, 'Modelo criado com sucesso!')
                return redirect('web-gerente:modelos-list', empresa_pk=empresa_pk)
            else:
                for field, errors in serializer.errors.items():
                    if isinstance(errors, list):
                        messages.error(request, f"{field}: {errors[0]}")
                    else:
                        messages.error(request, f"{field}: {errors}")
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    
    try:
        empresa_obj = get_object_or_404(Empresa, usuario__id=empresa_pk)
        empresa = empresas_serializers.EmpresaSerializer(empresa_obj, context={'request': request}).data
        empresa['id'] = empresa.get('usuario', {}).get('id', empresa_pk)
    except:
        empresa = None
    
    return render(request, 'gerente/modelo_form.html', {'empresa': empresa})


@gerente_required
def modelo_detail(request, empresa_pk, pk):
    """Detalhes do modelo"""
    try:
        empresa_obj = get_object_or_404(Empresa, usuario__id=empresa_pk)
        empresa = empresas_serializers.EmpresaSerializer(empresa_obj, context={'request': request}).data
        empresa['id'] = empresa.get('usuario', {}).get('id', empresa_pk)

        modelo_obj = get_object_or_404(ModeloCartao, id=pk)
        modelo = ModeloCartaoSerializer(modelo_obj, context={'request': request}).data

        # Converter datas
        from datetime import datetime
        for fld in ('created_at', 'updated_at'):
            if modelo.get(fld):
                try:
                    dt = datetime.fromisoformat(modelo[fld].replace('Z', '+00:00'))
                    modelo[f'{fld}_formatted'] = dt.strftime('%d/%m/%Y %H:%M')
                except Exception:
                    modelo[f'{fld}_formatted'] = 'Não disponível'
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        empresa = None
        modelo = None
    
    return render(request, 'gerente/modelo_detail.html', {
        'empresa': empresa,
        'modelo': modelo
    })


@gerente_required
def modelo_edit(request, empresa_pk, pk):
    """Editar modelo"""
    if request.method == 'POST':
        try:
            modelo_obj = get_object_or_404(ModeloCartao, id=pk)
            data = request.POST.dict()
            data['largura_mm'] = float(data.get('largura_mm', modelo_obj.largura_mm))
            data['altura_mm'] = float(data.get('altura_mm', modelo_obj.altura_mm))

            serializer = ModeloCartaoSerializer(modelo_obj, data=data, partial=True, context={'request': request})
            if serializer.is_valid():
                modelo = serializer.save()
                if 'background_image' in request.FILES:
                    modelo.background_image = request.FILES['background_image']
                if 'background_image_verso' in request.FILES:
                    modelo.background_image_verso = request.FILES['background_image_verso']
                modelo.save()
                messages.success(request, 'Modelo atualizado com sucesso!')
                return redirect('web-gerente:modelo-detail', empresa_pk=empresa_pk, pk=pk)
            else:
                for field, errors in serializer.errors.items():
                    messages.error(request, f"{field}: {errors}")
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    
    try:
        empresa_obj = get_object_or_404(Empresa, usuario__id=empresa_pk)
        empresa = empresas_serializers.EmpresaSerializer(empresa_obj, context={'request': request}).data
        empresa['id'] = empresa.get('usuario', {}).get('id', empresa_pk)

        modelo_obj = get_object_or_404(ModeloCartao, id=pk)
        modelo = ModeloCartaoSerializer(modelo_obj, context={'request': request}).data
    except:
        empresa = None
        modelo = None
    
    return render(request, 'gerente/modelo_edit.html', {
        'empresa': empresa,
        'modelo': modelo
    })


@gerente_required
def modelo_delete(request, empresa_pk, pk):
    """Excluir modelo"""
    if request.method != 'POST':
        return redirect('web-gerente:modelos-list', empresa_pk=empresa_pk)
    
    try:
        modelo = get_object_or_404(ModeloCartao, id=pk)
        modelo.delete()
        messages.success(request, 'Modelo excluído com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-gerente:modelos-list', empresa_pk=empresa_pk)


@gerente_required
def modelo_toggle_active(request, empresa_pk, pk):
    """Ativar/desativar modelo - apenas 1 ativo por empresa"""
    if request.method != 'POST':
        return redirect('web-gerente:modelo-detail', empresa_pk=empresa_pk, pk=pk)
    
    try:
        modelo_obj = get_object_or_404(ModeloCartao, id=pk)
        novo_status = not modelo_obj.is_active

        with transaction.atomic():
            if novo_status:
                # desativar outros modelos da mesma empresa
                ModeloCartao.objects.filter(empresa_id=modelo_obj.empresa_id).exclude(id=pk).update(is_active=False)
            modelo_obj.is_active = novo_status
            modelo_obj.save()

        if novo_status:
            messages.success(request, 'Modelo definido como ativo! Todos os outros modelos foram desativados.')
        else:
            messages.warning(request, 'Modelo desativado. A empresa ficará sem modelo ativo.')
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
    
    return redirect('web-gerente:modelos-list', empresa_pk=empresa_pk)


@gerente_required
def modelo_canvas_editor(request, empresa_pk, pk):
    """Editor canvas drag-and-drop para campos do modelo"""
    try:
        empresa_obj = get_object_or_404(Empresa, usuario__id=empresa_pk)
        empresa = empresas_serializers.EmpresaSerializer(empresa_obj, context={'request': request}).data
        empresa['id'] = empresa.get('usuario', {}).get('id', empresa_pk)

        modelo_obj = get_object_or_404(ModeloCartao, id=pk)
        modelo = ModeloCartaoSerializer(modelo_obj, context={'request': request}).data

        campos_qs = CampoCartao.objects.filter(modelo=modelo_obj).order_by('ordem')
        campos = CampoCartaoListSerializer(campos_qs, many=True).data
    except Exception as e:
        messages.error(request, f'Erro: {str(e)}')
        empresa = None
        modelo = None
        campos = []
    
    return render(request, 'gerente/modelo_canvas_editor.html', {
        'empresa': empresa,
        'modelo': modelo,
        'campos': campos
    })
