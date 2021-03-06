from django.db import models
from django.db.models.query import QuerySet


class AuditQuerySet(QuerySet):
    def _get_content_type(self, obj):
        from django.contrib.contenttypes.models import ContentType
        return ContentType.objects.get_for_model(obj)

    def for_(self, obj):
        return self.filter(
            content_type=self._get_content_type(obj),
            object_id=obj.id
        )


class AuditManager(models.Manager):
    def get_query_set(self):
        return AuditQuerySet(self.model)

    def __getattr__(self, attr, *args):
        # see https://code.djangoproject.com/ticket/15062 for details
        if attr.startswith("_"):
            raise AttributeError
        return getattr(self.get_query_set(), attr, *args)
