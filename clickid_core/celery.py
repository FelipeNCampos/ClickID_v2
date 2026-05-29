import os

from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clickid_core.settings')

app = Celery('clickid_core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()