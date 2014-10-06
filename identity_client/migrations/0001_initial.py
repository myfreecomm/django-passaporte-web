# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AccountMember',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('_roles', models.CharField(max_length=720)),
            ],
            options={
                'verbose_name': 'membro da conta do passaporte web',
                'verbose_name_plural': 'membros de contas do passaporte web',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Identity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=50, null=True, verbose_name='first name')),
                ('last_name', models.CharField(max_length=100, null=True, verbose_name='last name')),
                ('email', models.EmailField(max_length=75, verbose_name='e-mail address')),
                ('uuid', models.CharField(unique=True, max_length=36, verbose_name='universally unique id')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('last_login', models.DateTimeField(default=datetime.datetime.now, verbose_name='last login')),
            ],
            options={
                'verbose_name': 'usuario do passaporte web',
                'verbose_name_plural': 'usuarios do passaporte web',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ServiceAccount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('uuid', models.CharField(max_length=36)),
                ('plan_slug', models.CharField(max_length=50)),
                ('expiration', models.DateTimeField(null=True)),
                ('url', models.CharField(max_length=1024, null=True)),
                ('members', models.ManyToManyField(to='identity_client.Identity', through='identity_client.AccountMember')),
            ],
            options={
                'verbose_name': 'conta do passaporte web',
                'verbose_name_plural': 'contas do passaporte web',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='accountmember',
            name='account',
            field=models.ForeignKey(to='identity_client.ServiceAccount'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='accountmember',
            name='identity',
            field=models.ForeignKey(to='identity_client.Identity'),
            preserve_default=True,
        ),
    ]
