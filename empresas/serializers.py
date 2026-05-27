"""
Serializers for empresas app
"""
from rest_framework import serializers
from .models import Empresa, Departamento, Profissional
from usuarios.serializers import UsuarioSerializer
from usuarios.models import Usuario


class EmpresaSerializer(serializers.ModelSerializer):
    """Serializer para modelo Empresa"""
    usuario = UsuarioSerializer(read_only=True)
    usuario_id = serializers.UUIDField(write_only=True, required=False)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    total_profissionais = serializers.IntegerField(read_only=True)
    total_departamentos = serializers.IntegerField(read_only=True)
    cadastrado_por_email = serializers.EmailField(source='cadastrado_por.usuario.email', read_only=True)
    
    class Meta:
        model = Empresa
        fields = [
            'usuario', 'usuario_id', 'email', 'password',
            'razao_social', 'nome_fantasia', 'cnpj', 'url_personalizada', 'logo',
            'telefone', 'endereco', 'is_active', 'data_cadastro', 'cadastrado_por', 'cadastrado_por_email',
            'total_profissionais', 'total_departamentos'
        ]
        read_only_fields = ['usuario', 'data_cadastro', 'cadastrado_por']
    
    def create(self, validated_data):
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        usuario_id = validated_data.pop('usuario_id', None)
        
        # Criar ou usar usuário existente
        if usuario_id:
            usuario = Usuario.objects.get(id=usuario_id)
        else:
            usuario = Usuario.objects.create_user(
                email=email,
                password=password,
                tipo_usuario='empresa'
            )
        
        # Adicionar cadastrado_por automaticamente
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            try:
                from usuarios.models import Gerente
                gerente = Gerente.objects.get(usuario=request.user)
                validated_data['cadastrado_por'] = gerente
            except Gerente.DoesNotExist:
                pass
        
        empresa = Empresa.objects.create(usuario=usuario, **validated_data)
        return empresa
    
    def update(self, instance, validated_data):
        validated_data.pop('email', None)
        validated_data.pop('password', None)
        validated_data.pop('usuario_id', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['total_profissionais'] = instance.profissionais.count()
        representation['total_departamentos'] = instance.departamentos.count()
        return representation


class EmpresaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de empresas"""
    usuario_email = serializers.EmailField(source='usuario.email', read_only=True)
    total_profissionais = serializers.IntegerField(read_only=True)
    total_departamentos = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Empresa
        fields = [
            'usuario', 'usuario_email', 'razao_social', 'cnpj', 
            'url_personalizada', 'telefone', 'is_active', 'data_cadastro',
            'total_profissionais', 'total_departamentos'
        ]
        read_only_fields = ['usuario', 'data_cadastro']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['total_profissionais'] = instance.profissionais.count()
        representation['total_departamentos'] = instance.departamentos.count()
        return representation


class DepartamentoSerializer(serializers.ModelSerializer):
    """Serializer para modelo Departamento"""
    total_profissionais = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Departamento
        fields = [
            'id', 'empresa', 'nome', 'descricao',
            'total_profissionais',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['total_profissionais'] = instance.profissionais.count()
        return representation


class DepartamentoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de departamentos"""
    total_profissionais = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Departamento
        fields = ['id', 'nome', 'total_profissionais', 'created_at']
        read_only_fields = ['created_at']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['total_profissionais'] = instance.profissionais.count()
        return representation


class ProfissionalSerializer(serializers.ModelSerializer):
    """Serializer para modelo Profissional"""
    senha_padrao = serializers.CharField(read_only=True)
    precisa_alterar_senha = serializers.BooleanField(read_only=True)
    departamento_nome = serializers.CharField(source='departamento.nome', read_only=True)
    cadastrado_por_email = serializers.EmailField(source='cadastrado_por.email', read_only=True)
    
    class Meta:
        model = Profissional
        fields = [
            'usuario', 'empresa', 'departamento', 'departamento_nome',
            'nome', 'cpf', 'email', 'is_active',
            'senha_alterada', 'senha_padrao', 'precisa_alterar_senha',
            'data_primeiro_login',
            'data_cadastro', 'cadastrado_por', 'cadastrado_por_email'
        ]
        read_only_fields = [
            'usuario', 'senha_padrao', 'precisa_alterar_senha',
            'data_primeiro_login', 'data_cadastro', 'cadastrado_por'
        ]
        extra_kwargs = {
            'email': {'required': False, 'allow_blank': True, 'allow_null': True}
        }
    
    def create(self, validated_data):
        import re
        cpf = validated_data['cpf']
        nome = validated_data['nome']
        email = validated_data.get('email', '')
        
        # Limpar CPF
        cpf_limpo = re.sub(r'[^0-9]', '', cpf)
        
        # Criar usuário
        if not email:
            email = f'{cpf_limpo}@temp.clickid.com.br'
        
        # Senha padrão: últimos 4 dígitos do CPF
        senha_padrao = cpf_limpo[-4:]
        
        usuario = Usuario.objects.create_user(
            email=email,
            password=senha_padrao,
            tipo_usuario='profissional'
        )
        
        # Adicionar cadastrado_por automaticamente
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['cadastrado_por'] = request.user
        
        # Criar profissional
        profissional = Profissional.objects.create(
            usuario=usuario,
            **validated_data
        )
        
        return profissional
    
    def update(self, instance, validated_data):
        # Atualizar campos do profissional
        instance.nome = validated_data.get('nome', instance.nome)
        instance.cpf = validated_data.get('cpf', instance.cpf)  # Adicionar atualização de CPF
        instance.departamento = validated_data.get('departamento', instance.departamento)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        
        # Atualizar senha_alterada se fornecido
        if 'senha_alterada' in validated_data:
            instance.senha_alterada = validated_data.get('senha_alterada')
        
        # Atualizar email se fornecido
        email = validated_data.get('email')
        if email is not None:
            instance.email = email
            # Atualizar email do usuário também
            if instance.usuario:
                instance.usuario.email = email if email else instance.usuario.email
                instance.usuario.is_active = instance.is_active  # Sincronizar status de ativo
                instance.usuario.save()
        
        instance.save()
        return instance
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['senha_padrao'] = instance.gerar_senha_padrao()
        # Apenas precisa alterar se senha_alterada for False
        representation['precisa_alterar_senha'] = not instance.senha_alterada
        return representation


class ProfissionalListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de profissionais"""
    departamento_nome = serializers.CharField(source='departamento.nome', read_only=True)
    
    class Meta:
        model = Profissional
        fields = [
            'usuario', 'nome', 'cpf', 'email', 'departamento_nome',
            'is_active', 'data_cadastro'
        ]


class ProfissionalImportSerializer(serializers.Serializer):
    """Serializer para importação de profissionais via Excel"""
    arquivo = serializers.FileField()
    departamento_id = serializers.UUIDField(required=False, allow_null=True)
    
    def validate_arquivo(self, value):
        if not value.name.endswith(('.xlsx', '.xls')):
            raise serializers.ValidationError('Formato de arquivo inválido. Use Excel (.xlsx ou .xls).')
        
        max_size = 5 * 1024 * 1024  # 5 MB
        if value.size > max_size:
            raise serializers.ValidationError('Arquivo muito grande. Tamanho máximo: 5 MB.')
        
        return value


class ProfissionalBulkCreateSerializer(serializers.Serializer):
    """Serializer para criação em lote de profissionais"""
    profissionais = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )
    
    def validate_profissionais(self, value):
        required_fields = ['nome', 'cpf', 'email']
        for idx, profissional in enumerate(value):
            for field in required_fields:
                if field not in profissional:
                    raise serializers.ValidationError(
                        f'Profissional {idx + 1}: campo "{field}" é obrigatório.'
                    )
        return value


class ProfissionalLoginSerializer(serializers.Serializer):
    """Serializer para login de profissional"""
    cpf = serializers.CharField()
    senha = serializers.CharField(write_only=True)
    
    def validate_cpf(self, value):
        # Remove formatação do CPF
        cpf = ''.join(filter(str.isdigit, value))
        if len(cpf) != 11:
            raise serializers.ValidationError('CPF inválido.')
        return cpf
    
    def validate(self, data):
        cpf = data.get('cpf')
        senha = data.get('senha')
        
        try:
            profissional = Profissional.objects.get(cpf=cpf, is_active=True)
        except Profissional.DoesNotExist:
            raise serializers.ValidationError('CPF não encontrado.')
        
        # Validar senha
        senha_padrao = profissional.gerar_senha_padrao()
        if senha != senha_padrao:
            raise serializers.ValidationError('Senha incorreta.')
        
        data['profissional'] = profissional
        return data


class ProfissionalPasswordChangeSerializer(serializers.Serializer):
    """Serializer para alteração de senha do profissional"""
    senha_atual = serializers.CharField(write_only=True)
    senha_nova = serializers.CharField(write_only=True)
    confirmar_senha = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['senha_nova'] != data['confirmar_senha']:
            raise serializers.ValidationError({
                'confirmar_senha': 'As senhas não coincidem.'
            })
        
        if len(data['senha_nova']) < 4:
            raise serializers.ValidationError({
                'senha_nova': 'A senha deve ter no mínimo 4 caracteres.'
            })
        
        return data
    
    def validate_senha_atual(self, value):
        profissional = self.context['profissional']
        senha_padrao = profissional.gerar_senha_padrao()
        
        if value != senha_padrao:
            raise serializers.ValidationError('Senha atual incorreta.')
        
        return value
