# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('identity_client', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='identity',
            options={'verbose_name': 'usu\xe1rio do passaporte web', 'verbose_name_plural': 'usu\xe1rios do passaporte web'},
        ),
    ]
