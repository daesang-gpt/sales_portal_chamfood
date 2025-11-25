from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from .models import User, AuditLog
import logging

logger = logging.getLogger(__name__)

def get_client_ip(request):
    """클라이언트 IP 주소 가져오기"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_user_agent(request):
    """User Agent 가져오기"""
    return request.META.get('HTTP_USER_AGENT', '')[:500]

def create_audit_log(user, action_type, description='', request=None, target_user=None, old_value=None, new_value=None, resource_type=None, resource_id=None):
    """감사 로그 생성 헬퍼 함수"""
    try:
        username = user.username if user else None
        ip_address = get_client_ip(request) if request else None
        user_agent = get_user_agent(request) if request else None
        
        AuditLog.objects.create(
            user=user,
            username=username,
            action_type=action_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            target_user=target_user,
            old_value=old_value,
            new_value=new_value,
            resource_type=resource_type,
            resource_id=resource_id,
        )
    except Exception as e:
        logger.error(f"Audit log creation failed: {str(e)}")

@receiver(pre_save, sender=User)
def log_user_permission_change(sender, instance, **kwargs):
    """사용자 권한 변경 감지"""
    if instance.pk:  # 기존 사용자 업데이트
        try:
            old_user = User.objects.get(pk=instance.pk)
            if old_user.role != instance.role:
                # 권한 변경 로그는 post_save에서 생성 (request 정보 필요)
                instance._role_changed = True
                instance._old_role = old_user.role
        except User.DoesNotExist:
            pass

@receiver(post_save, sender=User)
def save_user_permission_change_log(sender, instance, created, **kwargs):
    """사용자 권한 변경 로그 저장"""
    if not created and hasattr(instance, '_role_changed') and instance._role_changed:
        try:
            # request 정보는 views.py에서 직접 로깅하도록 함
            # 여기서는 기본 로그만 생성
            create_audit_log(
                user=instance,
                action_type='permission_change',
                description=f'권한이 {instance._old_role}에서 {instance.role}로 변경되었습니다.',
                old_value=instance._old_role,
                new_value=instance.role,
            )
        except Exception as e:
            logger.error(f"Permission change log failed: {str(e)}")
        finally:
            # 임시 속성 제거
            if hasattr(instance, '_role_changed'):
                delattr(instance, '_role_changed')
            if hasattr(instance, '_old_role'):
                delattr(instance, '_old_role')


