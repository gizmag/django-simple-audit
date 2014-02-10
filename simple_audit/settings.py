"""Settings for django-simple-audit"""
import logging
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

LOG = logging.getLogger(__name__)

DJANGO_SIMPLE_AUDIT_ACTIVATED = getattr(settings, 'DJANGO_SIMPLE_AUDIT_ACTIVATED', False)
DJANGO_SIMPLE_AUDIT_M2M_FIELDS = getattr(settings, 'DJANGO_SIMPLE_AUDIT_M2M_FIELDS', False)
DJANGO_SIMPLE_AUDIT_M2M_RELATIONS = getattr(settings, 'DJANGO_SIMPLE_AUDIT_M2M_RELATIONS', False)

if not hasattr(settings, 'CACHES'):
    LOG.warning("no cache backend set in django! m2m auditing will be disabled")
    DJANGO_SIMPLE_AUDIT_M2M_FIELDS = False

if DJANGO_SIMPLE_AUDIT_M2M_FIELDS and DJANGO_SIMPLE_AUDIT_M2M_RELATIONS:
    raise ImproperlyConfigured("You cannot audit both M2M field changes and relations - choose one or the other")
