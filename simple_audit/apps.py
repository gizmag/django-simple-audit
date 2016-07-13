"""Django Simple Audit app config."""
# -*- coding:utf-8 -*-
from __future__ import absolute_import, unicode_literals

# stdlib
import logging

# requirements
from django.apps import AppConfig
from django.core.cache import cache
from django.db import models

# project
from . import MODEL_LIST, settings

LOG = logging.getLogger(__name__)

class DjangoSimpleAuditConfig(AppConfig):

    """Django app config for simple_audit."""

    name = 'simple_audit'
    verbose_name = 'Django Simple Audit'

    def ready(self):
        """Initialisation for simple_audit (setup lookups and signal handlers)."""
        from . import signal
        for model in MODEL_LIST:
            models.signals.pre_save.connect(signal.audit_pre_save, sender=model)
            models.signals.post_save.connect(signal.audit_post_save, sender=model)
            models.signals.pre_delete.connect(signal.audit_pre_delete, sender=model)

            # signals for m2m fields
            if settings.DJANGO_SIMPLE_AUDIT_M2M_FIELDS or settings.DJANGO_SIMPLE_AUDIT_M2M_RELATIONS:
                m2ms = model._meta.get_m2m_with_model()
                if m2ms:
                    for m2m in m2ms:
                        try:
                            sender_m2m = getattr(model, m2m[0].name).through
                            if sender_m2m.__name__ == "{}_{}".format(model.__name__, m2m[0].name):
                                if settings.DJANGO_SIMPLE_AUDIT_M2M_FIELDS:
                                    models.signals.m2m_changed.connect(signal.audit_m2m_change, sender=sender_m2m)
                                if settings.DJANGO_SIMPLE_AUDIT_M2M_RELATIONS:
                                    models.signals.m2m_changed.connect(signal.audit_m2m_change_relation, sender=sender_m2m)
                                LOG.debug("Attached signal to: %s" % sender_m2m)
                        except Exception as err:
                            raise
                            LOG.warning("could not create signal for m2m field: %s" % err)
