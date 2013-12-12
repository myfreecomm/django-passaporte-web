# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'AccountMember'
        db.create_table('identity_client_accountmember', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('identity', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['identity_client.Identity'])),
            ('account', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['identity_client.ServiceAccount'])),
            ('_roles', self.gf('django.db.models.fields.CharField')(max_length=720)),
        ))
        db.send_create_signal('identity_client', ['AccountMember'])

        # Adding model 'ServiceAccount'
        db.create_table('identity_client_serviceaccount', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36)),
            ('plan_slug', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('expiration', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
        ))
        db.send_create_signal('identity_client', ['ServiceAccount'])


    def backwards(self, orm):
        
        # Deleting model 'AccountMember'
        db.delete_table('identity_client_accountmember')

        # Deleting model 'ServiceAccount'
        db.delete_table('identity_client_serviceaccount')


    models = {
        'identity_client.accountmember': {
            'Meta': {'object_name': 'AccountMember'},
            '_roles': ('django.db.models.fields.CharField', [], {'max_length': '720'}),
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['identity_client.ServiceAccount']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['identity_client.Identity']"})
        },
        'identity_client.identity': {
            'Meta': {'object_name': 'Identity'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36'})
        },
        'identity_client.serviceaccount': {
            'Meta': {'object_name': 'ServiceAccount'},
            'expiration': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['identity_client.Identity']", 'through': "orm['identity_client.AccountMember']", 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'plan_slug': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36'})
        }
    }

    complete_apps = ['identity_client']
