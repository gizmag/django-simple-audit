# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simple_audit', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditrequest',
            name='ip',
            field=models.GenericIPAddressField(),
        ),
    ]
