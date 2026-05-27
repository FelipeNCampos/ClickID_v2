"""
Context processors para disponibilizar dados globalmente nos templates
"""
import logging
from django.db.utils import InterfaceError
from django.db import connection
from empresas.models import Empresa, Profissional

logger = logging.getLogger(__name__)


def empresa_info(request):
    """
    Adiciona informações da empresa ao contexto quando o usuário é do tipo empresa
    """
    context = {}
    
    if request.user.is_authenticated:
        tipo = getattr(request.user, 'tipo_usuario', None)
        logger.debug('empresa_info context processor running for user=%s tipo=%s', getattr(request.user, 'email', None), tipo)
        # Empresa user: provide empresa object and name
        if tipo == 'empresa':
            try:
                empresa = Empresa.objects.get(usuario=request.user)
                context['empresa'] = empresa
                context['empresa_nome'] = empresa.nome_fantasia or empresa.razao_social
                logger.debug('empresa_info found empresa for empresa user: %s', context['empresa_nome'])
            except Empresa.DoesNotExist:
                context['empresa'] = None
                context['empresa_nome'] = None
                logger.debug('empresa_info: Empresa.DoesNotExist for user %s', getattr(request.user, 'email', None))
            except InterfaceError as ie:
                # Connection may be stale/closed; try to recover by closing and retrying once
                logger.exception('Database InterfaceError in context processor empresa_info: %s - attempting reconnect and retry', ie)
                try:
                    connection.close()
                    empresa = Empresa.objects.get(usuario=request.user)
                    context['empresa'] = empresa
                    context['empresa_nome'] = empresa.nome_fantasia or empresa.razao_social
                    logger.debug('empresa_info recovered after reconnect: %s', context['empresa_nome'])
                except Empresa.DoesNotExist:
                    context['empresa'] = None
                    context['empresa_nome'] = None
                    logger.debug('empresa_info: Empresa.DoesNotExist on retry for user %s', getattr(request.user, 'email', None))
                except Exception as e:
                    logger.exception('Retry failed in context processor empresa_info: %s', e)
                    context['empresa'] = None
                    context['empresa_nome'] = None
            except Exception as e:
                logger.exception('Unexpected error in context processor empresa_info: %s', e)
                context['empresa'] = None
                context['empresa_nome'] = None
        # Profissional user: provide the related empresa via Profissional relation
        elif tipo == 'profissional':
            try:
                prof = Profissional.objects.select_related('empresa').get(usuario=request.user)
                context['empresa'] = prof.empresa
                context['empresa_nome'] = prof.empresa.nome_fantasia or prof.empresa.razao_social
                logger.debug('empresa_info found empresa via profissional: %s', context['empresa_nome'])
            except Profissional.DoesNotExist:
                context['empresa'] = None
                context['empresa_nome'] = None
                logger.debug('empresa_info: Profissional.DoesNotExist for user %s', getattr(request.user, 'email', None))
            except InterfaceError as ie:
                logger.exception('Database InterfaceError in context processor empresa_info (profissional): %s - attempting reconnect and retry', ie)
                try:
                    connection.close()
                    prof = Profissional.objects.select_related('empresa').get(usuario=request.user)
                    context['empresa'] = prof.empresa
                    context['empresa_nome'] = prof.empresa.nome_fantasia or prof.empresa.razao_social
                    logger.debug('empresa_info recovered after reconnect (profissional): %s', context['empresa_nome'])
                except Profissional.DoesNotExist:
                    context['empresa'] = None
                    context['empresa_nome'] = None
                    logger.debug('empresa_info: Profissional.DoesNotExist on retry for user %s', getattr(request.user, 'email', None))
                except Exception as e:
                    logger.exception('Retry failed in context processor empresa_info (profissional): %s', e)
                    context['empresa'] = None
                    context['empresa_nome'] = None
            except Exception as e:
                logger.exception('Unexpected error in context processor empresa_info (profissional): %s', e)
                context['empresa'] = None
                context['empresa_nome'] = None
    
    return context
