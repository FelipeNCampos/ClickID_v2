"""
Serializers for usuarios app
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Usuario, Gerente, LogAuditoria


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer para modelo Usuario"""
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'tipo_usuario', 'password',
            'is_active', 'is_staff', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        usuario = Usuario(**validated_data)
        if password:
            usuario.set_password(password)
        usuario.save()
        return usuario
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class GerenteSerializer(serializers.ModelSerializer):
    """Serializer para modelo Gerente"""
    usuario = UsuarioSerializer(read_only=True)
    usuario_id = serializers.UUIDField(write_only=True, required=False)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = Gerente
        fields = [
            'usuario', 'email', 'password',
            'nome', 'cpf', 'telefone', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['usuario', 'created_at', 'updated_at']
    
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
                tipo_usuario='gerente'
            )
        
        gerente = Gerente.objects.create(usuario=usuario, **validated_data)
        return gerente
    
    def update(self, instance, validated_data):
        validated_data.pop('email', None)
        validated_data.pop('password', None)
        validated_data.pop('usuario_id', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class GerenteDetailSerializer(GerenteSerializer):
    """Serializer detalhado para Gerente com dados do usuário"""
    usuario = UsuarioSerializer(read_only=True)
    
    class Meta(GerenteSerializer.Meta):
        fields = GerenteSerializer.Meta.fields
        read_only_fields = GerenteSerializer.Meta.read_only_fields


class LogAuditoriaSerializer(serializers.ModelSerializer):
    """Serializer para modelo LogAuditoria"""
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)
    
    class Meta:
        model = LogAuditoria
        fields = [
            'id', 'timestamp', 'usuario', 'usuario_email', 'acao',
            'descricao', 'ip_address', 'user_agent', 'dados_alterados'
        ]
        read_only_fields = fields


class LoginSerializer(serializers.Serializer):
    """Serializer para login de usuários"""
    email = serializers.EmailField(required=False)
    cpf = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        cpf = data.get('cpf')
        password = data.get('password')

        user = None
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
        elif cpf and password:
            # Buscar usuário pelo CPF
            from empresas.models import Profissional
            try:
                profissional = Profissional.objects.select_related('usuario').get(cpf=cpf, is_active=True)
                user = authenticate(
                    request=self.context.get('request'),
                    username=profissional.usuario.email,
                    password=password
                )
            except Profissional.DoesNotExist:
                raise serializers.ValidationError('CPF não encontrado.')
        else:
            raise serializers.ValidationError('Email/CPF e senha são obrigatórios.')

        if not user:
            raise serializers.ValidationError('Credenciais inválidas.')
        if not user.is_active:
            raise serializers.ValidationError('Usuário inativo.')

        data['user'] = user
        return data


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer para alteração de senha"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'As senhas não coincidem.'
            })
        
        if len(data['new_password']) < 8:
            raise serializers.ValidationError({
                'new_password': 'A senha deve ter no mínimo 8 caracteres.'
            })
        
        return data
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Senha atual incorreta.')
        return value


class PasswordResetSerializer(serializers.Serializer):
    """Serializer para recuperação de senha"""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            Usuario.objects.get(email=value)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError('Usuário não encontrado.')
        return value
