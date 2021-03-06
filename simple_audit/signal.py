# -*- coding:utf-8 -*-
from __future__ import absolute_import, unicode_literals

# stdlib
import logging
import re
import threading
from pprint import pprint

# requirements
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.cache import cache

# project
from . import MODEL_LIST, m2m_audit, settings
from .models import Audit, AuditChange


UNICODE = type('')  # unicode thanks to unicode_literals
STRING = type(b'')  # byte string in Python 3, or non-unicode string in Python 2.
STRING_TYPES = (UNICODE, STRING)
LOG = logging.getLogger(__name__)
DEFAULT_CACHE_TIMEOUT = 120

def get_cache_key_for_instance(instance, cache_prefix="django_simple_audit"):

    return "%s:%s:%s" % (cache_prefix, instance.__class__.__name__, instance.pk)

def audit_m2m_change(sender, **kwargs):
    """
    audit m2m changes if the settings DJANGO_SIMPLE_AUDIT_M2M_FIELDS is set to True
    """
    if kwargs.get('action'):
        action = kwargs.get('action')
        instance = kwargs.get('instance')
        if kwargs['action'] == "post_add":
            cache_key = get_cache_key_for_instance(instance)
            dict_ = cache.get(cache_key)
            if not dict_:
                dict_ = {"old_state" : {}, "new_state": {}}

            dict_["new_state"] = m2m_audit.get_m2m_values_for(instance=instance)
            dict_["m2m_change"] = True
            cache.set(cache_key, dict_, DEFAULT_CACHE_TIMEOUT)
            save_audit(instance, Audit.CHANGE, kwargs=dict_)
        elif kwargs['action'] == "post_remove":
            save_audit(kwargs['instance'], Audit.DELETE, kwargs=kwargs)


def audit_m2m_change_relation(sender, **kwargs):
    """
    audit m2m relation changes is settings.DJANGO_SIMPLE_AUDIT_M2M_RELATIONS is True
    """
    if kwargs.get('action'):
        action = kwargs.get('action')
        instance = kwargs.get('instance')
        if kwargs['action'] in {'post_add', 'post_clear'}:
            cache_key = get_cache_key_for_instance(instance)
            dict_ = cache.get(cache_key)
            if not dict_:
                dict_ = {"old_state_m2m": {}, "new_state_m2m": {}}
            new_m2ms = m2m_audit.get_m2m_values_for(instance=instance)
            for k,v in new_m2ms.items():
                dict_['new_state_m2m'][k] = [item['id'] for item in v]
            dict_["m2m_change_relation"] = True
            save_audit(instance, Audit.CHANGE, kwargs=dict_)
        elif kwargs['action'] == 'pre_clear':
            cache_key = get_cache_key_for_instance(instance)
            dict_ = {"old_state_m2m": {}, "new_state_m2m": {}}
            old_m2ms = m2m_audit.get_m2m_values_for(instance=instance)
            for k,v in old_m2ms.items():
                dict_['old_state_m2m'][k] = [item['id'] for item in v]
            cache.set(cache_key, dict_, DEFAULT_CACHE_TIMEOUT)
            LOG.debug("old_state saved in cache with key %s for m2m relation auditing" % cache_key)

def audit_post_save(sender, **kwargs):
    if kwargs['created'] and not kwargs.get('raw', False):
        save_audit(kwargs['instance'], Audit.ADD)


def audit_pre_save(sender, **kwargs):
    instance=kwargs.get('instance')

    if instance.pk and not kwargs.get('raw', False):
        if settings.DJANGO_SIMPLE_AUDIT_M2M_FIELDS:
            if m2m_audit.get_m2m_fields_for(instance): #has m2m fields?
                cache_key = get_cache_key_for_instance(instance)
                dict_ = {"old_state" : {}, "new_state": {}}
                dict_["old_state"] = m2m_audit.get_m2m_values_for(instance=instance)
                cache.set(cache_key, dict_, DEFAULT_CACHE_TIMEOUT)
                LOG.debug("old_state saved in cache with key %s for m2m auditing" % cache_key)
        save_audit(kwargs['instance'], Audit.CHANGE)


def audit_pre_delete(sender, **kwargs):
    save_audit(kwargs['instance'], Audit.DELETE)


def unregister(*my_models):
    if not settings.DJANGO_SIMPLE_AUDIT_ACTIVATED:
        return False
    for model in my_models:
        models.signals.pre_save.disconnect(audit_pre_save, sender=model)
        models.signals.post_save.disconnect(audit_post_save, sender=model)
        models.signals.pre_delete.disconnect(audit_pre_delete, sender=model)

        if settings.DJANGO_SIMPLE_AUDIT_M2M_FIELDS:
            m2ms = model._meta.get_m2m_with_model()
            if m2ms:
                for m2m in m2ms:
                    try:
                        sender_m2m = getattr(model, m2m[0].name).through
                        if sender_m2m.__name__ == "{}_{}".format(model.__name__, m2m[0].name):
                            models.signals.m2m_changed.disconnect(audit_m2m_change, sender=sender_m2m)
                    except Exception as err:
                        LOG.warning("could not disconnect signal for m2m field: %s" % err)

NOT_ASSIGNED = object()


def get_value(obj, attr):
    """
    Returns the value of an attribute. First it tries to return the unicode value.
    """
    if hasattr(obj, attr):
        value = getattr(obj, attr)
        if hasattr(value, '__unicode__'):
            return value.__unicode__()
        else:
            if hasattr(value, 'all'):
                return [v.__unicode__() for v in value.all()]
            else:
                return value
    else:
        return None


def to_dict(obj):
    if obj is None:
        return {}

    if isinstance(obj, dict):
        return dict.copy()

    state = {}

    for key in obj._meta.get_all_field_names():
        state[key] = get_value(obj, key)

    return state


def dict_diff(old, new):

    keys = set(old)
    keys.update(new)
    diff = {}
    for key in keys:
        old_value = old.get(key, None)
        new_value = new.get(key, None)
        if old_value != new_value:
            if re.match(key, 'password'):
                old_value = 'xxxxxxxx'
                new_value = "*" * len(new.get(key))
            diff[key] = (old_value, new_value)

    if diff:
        LOG.debug("dict_diff: %s" % diff)
    return diff


def format_value(v):
    if isinstance(v, STRING_TYPES):
        return "'%s'" % v
    return '%s' % v


def save_audit(instance, operation, kwargs={}):
    """
    Saves the audit.
    However, the variable persist_audit controls if the audit should be really
    saved to the database or not. This variable is only affected in a change operation. If no
    change is detected than it is setted to False.

    Keyword arguments:
    instance -- instance
    operation -- operation type (add, change, delete)
    kwargs -- kwargs dict sent from m2m signal
    """

    m2m_change = kwargs.get('m2m_change', False)
    m2m_change_relation = kwargs.get('m2m_change_relation', False)

    persist_audit = True

    new_state = to_dict(instance)
    old_state = {}
    if operation == Audit.CHANGE and instance.pk:
        if m2m_change:
            #m2m change
            LOG.debug("m2m change detected")
            new_state = kwargs.get("new_state", {})
            old_state = kwargs.get("old_state", {})
        elif m2m_change_relation:
            #m2m relation change
            LOG.debug("m2m relation change detected")
            new_state = kwargs.get("new_state_m2m", {})
            old_state = kwargs.get("old_state_m2m", {})
        else:
            old_state = to_dict(instance.__class__.objects.get(pk=instance.pk))

    if m2m_change:
        #m2m_change returns a list of changes
        changed_fields = m2m_audit.m2m_dict_diff(old_state, new_state)
    else:
        changed_fields = dict_diff(old_state, new_state)

    if operation == Audit.CHANGE:
        #is there any change?
        if not changed_fields:
            persist_audit = False

        if m2m_change:
            descriptions = []
            for changed_field in changed_fields:
                description = "\n".join(["%s %s %s" %
                    (
                        _("field"),
                        k,
                        _("was changed"),
                    ) for k, v in changed_field.items()])
                descriptions.append(description)
        else:
            description = "\n".join(["%s %s %s" %
                (
                    _("field"),
                    k,
                    _("was changed"),
                ) for k, v in changed_fields.items()])

    elif operation == Audit.DELETE:
        description = _('Deleted %s') % instance
    elif operation == Audit.ADD:
        description = _('Added %s') % instance
    LOG.debug("called audit with operation=%s instance=%s persist=%s" % (operation, instance, persist_audit))
    if persist_audit:
        if m2m_change:
            for description in descriptions:
                audit = Audit.register(instance, description, operation)
                changed_field = changed_fields.pop(0)

                for field, (old_value, new_value) in changed_field.items():
                    change = AuditChange()
                    change.audit = audit
                    change.field = field
                    change.new_value = handle_unicode(new_value)
                    change.old_value = handle_unicode(old_value)
                    change.save()
        else:
            audit = Audit.register(instance, description, operation)

            for field, (old_value, new_value) in changed_fields.items():
                change = AuditChange()
                change.audit = audit
                change.field = field
                change.new_value = handle_unicode(new_value)
                change.old_value = handle_unicode(old_value)
                change.save()


def handle_unicode(val):
    if not val:
        return None
    elif isinstance(val, UNICODE):
        return val.encode('utf-8')
    return val
