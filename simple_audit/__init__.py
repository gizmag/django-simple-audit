from . import settings

MODEL_LIST = set()

default_app_config = 'simple_audit.apps.DjangoSimpleAuditConfig'


def register(*my_models):
    if not settings.DJANGO_SIMPLE_AUDIT_ACTIVATED:
        return False
    for model in my_models:
        if model is not None:
            MODEL_LIST.add(model)
