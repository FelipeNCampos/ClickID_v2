"""
Views/ViewSets for empresas app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db import transaction
from auditoria.models import LogAuditoria, TipoAcao
from .models import Empresa, Departamento, Profissional
from .serializers import (
    EmpresaSerializer, EmpresaListSerializer,
    DepartamentoSerializer, DepartamentoListSerializer,
    ProfissionalSerializer, ProfissionalListSerializer,
    ProfissionalImportSerializer, ProfissionalBulkCreateSerializer,
    ProfissionalLoginSerializer, ProfissionalPasswordChangeSerializer
)
import logging

logger = logging.getLogger(__name__)
from clickid_core.db_utils import get_request_params


def _process_profissionais_excel_import(arquivo, empresa, user, request=None):
    """Processa a importação de profissionais a partir de um arquivo Excel."""
    import openpyxl
    from io import BytesIO
    import uuid
    from django.db import IntegrityError
    from usuarios.models import Usuario

    try:
        wb = openpyxl.load_workbook(BytesIO(arquivo.read()))
        ws = wb.active
    except Exception as e:
        return {'erro': f'Erro ao ler arquivo Excel: {str(e)}'}, status.HTTP_400_BAD_REQUEST

    cpfs_existentes = set(
        Profissional.objects.filter(empresa=empresa)
        .values_list('cpf', flat=True)
    )

    emails_existentes = set(
        Usuario.objects.values_list('email', flat=True)
    )

    profissionais_para_criar = []
    importados = []
    ignorados = []
    erros = []

    for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not any(row):
            continue

        nome = row[0]
        cpf = str(row[1]).replace('.', '').replace('-', '').strip() if row[1] else None
        email_excel = row[2] if len(row) > 2 and row[2] and str(row[2]).strip() != '-' else None

        if not nome or not cpf:
            erros.append({'linha': idx, 'erro': 'Nome e CPF são obrigatórios'})
            continue

        if cpf in cpfs_existentes:
            ignorados.append({'linha': idx, 'nome': nome, 'cpf': cpf, 'motivo': 'CPF já cadastrado'})
            continue

        if email_excel:
            email_final = email_excel
            email_base = email_excel.split('@')[0]
            email_dominio = email_excel.split('@')[1] if '@' in email_excel else 'clickid.temp'
        else:
            unique_id = str(uuid.uuid4())[:8]
            email_final = f'profissional_{cpf}_{unique_id}@clickid.temp'
            email_base = f'profissional_{cpf}'
            email_dominio = 'clickid.temp'

        tentativas = 0
        while email_final in emails_existentes and tentativas < 10:
            unique_id = str(uuid.uuid4())[:8]
            email_final = f'{email_base}_{unique_id}@{email_dominio}'
            tentativas += 1

        if tentativas >= 10:
            erros.append({'linha': idx, 'erro': 'Não foi possível gerar email único'})
            continue

        emails_existentes.add(email_final)
        profissionais_para_criar.append({
            'linha': idx,
            'nome': nome,
            'cpf': cpf,
            'email_excel': email_excel,
            'email_final': email_final,
            'senha': cpf[-4:] if len(cpf) >= 4 else cpf
        })

    for idx, prof_data in enumerate(profissionais_para_criar, 1):
        try:
            with transaction.atomic():
                usuario = Usuario.objects.create(
                    email=prof_data['email_final'],
                    tipo_usuario='profissional'
                )
                usuario.set_password(prof_data['senha'])
                usuario.save()

                Profissional.objects.create(
                    usuario=usuario,
                    empresa=empresa,
                    nome=prof_data['nome'],
                    cpf=prof_data['cpf'],
                    email=prof_data['email_excel']
                )

                importados.append({
                    'linha': prof_data['linha'],
                    'nome': prof_data['nome'],
                    'cpf': prof_data['cpf']
                })

        except IntegrityError as e:
            erros.append({'linha': prof_data['linha'], 'erro': f'Erro ao criar: {str(e)}'})
        except Exception as e:
            erros.append({'linha': prof_data['linha'], 'erro': f'Erro inesperado: {str(e)}'})

    if importados:
        LogAuditoria.registrar(
            usuario=user,
            tipo_acao=TipoAcao.PROFISSIONAL_CRIADO,
            descricao=f'Importação Excel: {len(importados)} profissionais criados, {len(ignorados)} já cadastrados, {len(erros)} erros',
            empresa=empresa,
            dados_adicionais={
                'total_importados': len(importados),
                'total_ignorados': len(ignorados),
                'total_erros': len(erros),
                'arquivo': arquivo.name
            },
            request=request
        )

    return {
        'total_importados': len(importados),
        'total_ignorados': len(ignorados),
        'total_erros': len(erros),
        'importados': importados,
        'ignorados': ignorados[:10],
        'erros': erros[:10]
    }, status.HTTP_201_CREATED


class EmpresaViewSet(viewsets.ModelViewSet):
    """ViewSet para Empresa"""
    queryset = Empresa.objects.select_related('usuario').all()
    serializer_class = EmpresaSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'usuario'  # Usar usuario como PK
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EmpresaListSerializer
        return EmpresaSerializer
    
    def get_object(self):
        logger.debug(f"EmpresaViewSet.get_object: kwargs={self.kwargs}, lookup_field={self.lookup_field}")
        obj = super().get_object()
        logger.debug(f"EmpresaViewSet.get_object: found object id={obj.usuario_id}")
        return obj
    
    def get_queryset(self):
        user = self.request.user
        queryset = Empresa.objects.select_related('usuario').all()
        
        logger.debug(f"EmpresaViewSet.get_queryset: user={user}, tipo_usuario={getattr(user, 'tipo_usuario', None)}, is_staff={user.is_staff}")
        
        if user.is_staff or user.tipo_usuario == 'gerente':
            queryset = Empresa.objects.select_related('usuario').all()
            logger.debug(f"EmpresaViewSet.get_queryset: gerente/staff, queryset count={queryset.count()}")
        elif user.tipo_usuario == 'empresa':
            queryset = Empresa.objects.filter(usuario=user)
            logger.debug(f"EmpresaViewSet.get_queryset: empresa user, queryset count={queryset.count()}")
        elif user.tipo_usuario == 'profissional':
            # Profissional pode ver empresa vinculada
            try:
                profissional = Profissional.objects.get(usuario=user)
                queryset = Empresa.objects.filter(usuario=profissional.empresa.usuario)
                logger.debug(f"EmpresaViewSet.get_queryset: profissional user, empresa vinculada={profissional.empresa.usuario_id}")
            except Profissional.DoesNotExist:
                logger.debug("EmpresaViewSet.get_queryset: profissional user, sem empresa vinculada")
                return Empresa.objects.none()
        else:
            logger.debug("EmpresaViewSet.get_queryset: other user type, returning empty queryset")
            return Empresa.objects.none()
        
        # Filtros
        # Filtro de status (is_active)
        params = get_request_params(self.request)
        is_active = params.get('is_active')
        if is_active is not None:
            if is_active.lower() == 'true':
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() == 'false':
                queryset = queryset.filter(is_active=False)
        
        # Filtro de busca (search)
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                razao_social__icontains=search
            ) | queryset.filter(
                cnpj__icontains=search
            )
        
        logger.debug(f"EmpresaViewSet.get_queryset: final queryset count={queryset.count()}")
        return queryset
    
    @action(detail=True, methods=['get'])
    def profissionais(self, request, pk=None):
        """Lista profissionais da empresa"""
        empresa = self.get_object()
        profissionais = empresa.profissionais.all()
        serializer = ProfissionalListSerializer(profissionais, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def departamentos(self, request, pk=None):
        """Lista departamentos da empresa"""
        empresa = self.get_object()
        departamentos = empresa.departamentos.all()
        serializer = DepartamentoListSerializer(departamentos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def estatisticas(self, request, pk=None):
        """Estatísticas da empresa"""
        empresa = self.get_object()
        return Response({
            'total_profissionais': empresa.profissionais.count(),
            'total_departamentos': empresa.departamentos.count(),
            'total_modelos': empresa.modelos.count(),
            'total_coletas': empresa.coletas.count(),
        })


class DepartamentoViewSet(viewsets.ModelViewSet):
    """ViewSet para Departamento"""
    queryset = Departamento.objects.select_related('empresa').all()
    serializer_class = DepartamentoSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DepartamentoListSerializer
        return DepartamentoSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Departamento.objects.select_related('empresa').all()
        
        if user.tipo_usuario == 'empresa':
            queryset = queryset.filter(empresa__usuario=user)
        elif user.tipo_usuario == 'profissional':
            return Departamento.objects.none()
        
        # Filtros
        params = get_request_params(self.request)
        empresa_id = params.get('empresa')
        if empresa_id:
            queryset = queryset.filter(empresa__usuario_id=empresa_id)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def profissionais(self, request, pk=None):
        """Lista profissionais do departamento"""
        departamento = self.get_object()
        profissionais = departamento.profissionais.all()
        serializer = ProfissionalListSerializer(profissionais, many=True)
        return Response(serializer.data)


class ProfissionalViewSet(viewsets.ModelViewSet):
    """ViewSet para Profissional"""
    queryset = Profissional.objects.select_related('empresa', 'departamento').all()
    serializer_class = ProfissionalSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    lookup_field = 'usuario'  # Usar usuario como PK
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProfissionalListSerializer
        elif self.action == 'import_excel':
            return ProfissionalImportSerializer
        elif self.action == 'bulk_create':
            return ProfissionalBulkCreateSerializer
        return ProfissionalSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Profissional.objects.select_related('empresa', 'departamento').all()
        
        if user.tipo_usuario == 'empresa':
            queryset = queryset.filter(empresa__usuario=user)
        elif user.tipo_usuario == 'profissional':
            # Profissional pode ver apenas seus próprios dados
            queryset = queryset.filter(usuario=user)
        
        # Filtros
        params = get_request_params(self.request)
        empresa_id = params.get('empresa')
        departamento_id = params.get('departamento')
        
        if empresa_id:
            queryset = queryset.filter(empresa__usuario_id=empresa_id)
        if departamento_id:
            queryset = queryset.filter(departamento_id=departamento_id)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def import_excel(self, request):
        """Importar profissionais via Excel - OTIMIZADO"""
        arquivo = request.FILES.get('arquivo')
        empresa_id = request.data.get('empresa')

        # Debugging: log incoming params to help diagnose "Empresa não encontrada"
        try:
            logger.debug('import_excel called: user=%s tipo_usuario=%s', getattr(request, 'user', None), getattr(request.user, 'tipo_usuario', None))
            logger.debug('import_excel: received empresa_id=%r', empresa_id)
            # Log request.data keys and files keys
            try:
                logger.debug('import_excel: request.data keys=%s', list(request.data.keys()))
            except Exception:
                logger.debug('import_excel: could not read request.data keys')
            try:
                logger.debug('import_excel: request.FILES keys=%s', list(request.FILES.keys()))
            except Exception:
                logger.debug('import_excel: could not read request.FILES keys')
        except Exception:
            logger.exception('import_excel: error while logging request details')
        
        if not arquivo:
            return Response({'erro': 'Arquivo não fornecido'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not empresa_id:
            return Response({'erro': 'Empresa não fornecida'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            empresa = Empresa.objects.get(usuario_id=empresa_id)
        except Empresa.DoesNotExist:
            # Tentar fallback: talvez o campo recebido esteja incorreto; buscar Empresa pelo usuário da request
            logger.warning('import_excel: Empresa lookup falhou para empresa_id=%r. Tentando fallback pelo request.user=%s', empresa_id, getattr(request.user, 'id', None))
            try:
                fallback_empresa = Empresa.objects.filter(usuario=request.user).first()
                if fallback_empresa:
                    logger.info('import_excel: Usando empresa fallback vinculada ao usuário: %s', getattr(request.user, 'id', None))
                    empresa = fallback_empresa
                else:
                    # Reunir informações de debug para retorno ao cliente (ajuda no frontend)
                    try:
                        data_keys = list(request.data.keys())
                    except Exception:
                        data_keys = []
                    try:
                        files_keys = list(request.FILES.keys())
                    except Exception:
                        files_keys = []

                    logger.debug('import_excel: empresa não encontrada; request.user.id=%s request.user.tipo=%s request.data_keys=%s request.files_keys=%s',
                                 getattr(request.user, 'id', None), getattr(request.user, 'tipo_usuario', None), data_keys, files_keys)

                    return Response({
                        'erro': 'Empresa não encontrada',
                        'empresa_recebida': empresa_id,
                        'request_user_id': getattr(request.user, 'id', None),
                        'request_user_tipo': getattr(request.user, 'tipo_usuario', None),
                        'request_data_keys': data_keys,
                        'request_files_keys': files_keys
                    }, status=status.HTTP_404_NOT_FOUND)
            except Exception:
                logger.exception('import_excel: erro durante fallback da busca de Empresa')
                return Response({'erro': 'Empresa não encontrada', 'empresa_recebida': empresa_id}, status=status.HTTP_404_NOT_FOUND)

        data, response_status = _process_profissionais_excel_import(
            arquivo=arquivo,
            empresa=empresa,
            user=request.user,
            request=request,
        )
        return Response(data, status=response_status)
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Resetar senha do profissional para padrão (últimos 4 dígitos do CPF)"""
        profissional = self.get_object()
        senha_padrao = profissional.gerar_senha_padrao()
        
        # Resetar senha no usuário
        profissional.usuario.set_password(senha_padrao)
        profissional.usuario.save()
        
        # Marcar que precisa alterar senha
        profissional.senha_alterada = False
        profissional.save()
        
        return Response({
            'message': 'Senha resetada com sucesso',
            'senha_padrao': senha_padrao
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def bulk_create(self, request):
        """Criar múltiplos profissionais"""
        serializer = ProfissionalBulkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        profissionais_data = serializer.validated_data['profissionais']
        criados = []
        erros = []
        
        for idx, prof_data in enumerate(profissionais_data):
            try:
                profissional = Profissional.objects.create(**prof_data)
                criados.append(ProfissionalSerializer(profissional).data)
            except Exception as e:
                erros.append({
                    'indice': idx,
                    'dados': prof_data,
                    'erro': str(e)
                })
        
        return Response({
            'total_criados': len(criados),
            'total_erros': len(erros),
            'criados': criados,
            'erros': erros
        }, status=status.HTTP_201_CREATED if criados else status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def import_dados_adicionais(self, request):
        """Importar dados adicionais de profissionais via Excel (ex: CREA, RG, etc)"""
        import openpyxl
        from io import BytesIO
        
        arquivo = request.FILES.get('arquivo')
        empresa_id = request.data.get('empresa')
        
        if not arquivo:
            return Response({'erro': 'Arquivo não fornecido'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not empresa_id:
            return Response({'erro': 'Empresa não fornecida'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            empresa = Empresa.objects.get(usuario_id=empresa_id)
        except Empresa.DoesNotExist:
            return Response({'erro': 'Empresa não encontrada', 'empresa_recebida': empresa_id}, status=status.HTTP_404_NOT_FOUND)
        
        # Ler arquivo Excel
        try:
            wb = openpyxl.load_workbook(BytesIO(arquivo.read()))
            ws = wb.active
        except Exception as e:
            return Response({'erro': f'Erro ao ler arquivo Excel: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Buscar TODOS os profissionais da empresa de uma vez (otimização)
        profissionais_dict = {
            prof.cpf: prof 
            for prof in Profissional.objects.filter(empresa=empresa).select_related('usuario')
        }
        
        print(f"\n=== IMPORTAÇÃO DE DADOS ADICIONAIS ===")
        print(f"Total de profissionais na empresa: {len(profissionais_dict)}")
        
        atualizados = []
        nao_encontrados = []
        erros = []
        campos_extras = {}  # Para armazenar campos encontrados no Excel
        
        # Ler cabeçalho para identificar campos
        header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
        headers = [str(h).strip().lower() if h else '' for h in header_row]
        
        print(f"Campos encontrados no Excel: {headers}")
        
        # Identificar índice do CPF
        cpf_index = None
        for idx, h in enumerate(headers):
            if 'cpf' in h:
                cpf_index = idx
                break
        
        if cpf_index is None:
            return Response({'erro': 'Coluna CPF não encontrada no Excel'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Processar linhas
        for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if not any(row):
                continue
            
            cpf = str(row[cpf_index]).replace('.', '').replace('-', '').strip() if row[cpf_index] else None
            
            if not cpf:
                erros.append({
                    'linha': idx,
                    'erro': 'CPF não informado'
                })
                continue
            
            # Buscar profissional
            profissional = profissionais_dict.get(cpf)
            
            if not profissional:
                nao_encontrados.append({
                    'linha': idx,
                    'cpf': cpf
                })
                continue
            
            # Coletar dados extras (todos os campos exceto CPF)
            dados_extras = {}
            for col_idx, valor in enumerate(row):
                if col_idx == cpf_index or not valor:
                    continue
                
                campo_nome = headers[col_idx] if col_idx < len(headers) else f'campo_{col_idx}'
                dados_extras[campo_nome] = str(valor).strip()
            
            # Atualizar dados_extras do profissional (JSON field)
            try:
                if not profissional.dados_extras:
                    profissional.dados_extras = {}
                
                profissional.dados_extras.update(dados_extras)
                profissional.save(update_fields=['dados_extras'])
                
                atualizados.append({
                    'linha': idx,
                    'cpf': cpf,
                    'nome': profissional.nome,
                    'campos_atualizados': list(dados_extras.keys())
                })
                
                # Guardar campos para estatísticas
                for campo in dados_extras.keys():
                    campos_extras[campo] = campos_extras.get(campo, 0) + 1
                
            except Exception as e:
                erros.append({
                    'linha': idx,
                    'cpf': cpf,
                    'erro': str(e)
                })
        
        print(f"\nResultado:")
        print(f"  Atualizados: {len(atualizados)}")
        print(f"  Não encontrados: {len(nao_encontrados)}")
        print(f"  Erros: {len(erros)}")
        print(f"  Campos importados: {list(campos_extras.keys())}")
        print(f"================================\n")
        
        # Registrar auditoria
        if atualizados:
            from auditoria.models import LogAuditoria, TipoAcao
            LogAuditoria.registrar(
                usuario=request.user,
                tipo_acao=TipoAcao.PROFISSIONAL_ATUALIZADO,
                descricao=f'Importação de dados adicionais: {len(atualizados)} profissionais atualizados',
                empresa=empresa,
                dados_adicionais={
                    'total_atualizados': len(atualizados),
                    'total_nao_encontrados': len(nao_encontrados),
                    'total_erros': len(erros),
                    'campos_importados': list(campos_extras.keys()),
                    'arquivo': arquivo.name
                },
                request=request
            )
        
        return Response({
            'total_atualizados': len(atualizados),
            'total_nao_encontrados': len(nao_encontrados),
            'total_erros': len(erros),
            'campos_importados': campos_extras,
            'atualizados': atualizados[:10],
            'nao_encontrados': nao_encontrados[:10],
            'erros': erros[:10]
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def resetar_senha(self, request, pk=None):
        """Resetar senha para padrão"""
        profissional = self.get_object()
        profissional.senha_alterada = False
        profissional.save()
        
        return Response({
            'message': 'Senha resetada para padrão.',
            'senha_padrao': profissional.gerar_senha_padrao()
        })
    
    @action(detail=True, methods=['get'])
    def coletas(self, request, pk=None):
        """Lista coletas do profissional"""
        profissional = self.get_object()
        coletas_prof = profissional.coletas_atribuidas.select_related('coleta').all()
        
        from coletas.serializers import ColetaProfissionalSerializer
        serializer = ColetaProfissionalSerializer(coletas_prof, many=True)
        return Response(serializer.data)

