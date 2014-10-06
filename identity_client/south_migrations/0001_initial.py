# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Identity'
        db.create_table('identity_client_identity', (
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=50, null=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=36)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=75)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('identity_client', ['Identity'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Identity'
        db.delete_table('identity_client_identity')
    
    
    models = {
        'identity_client.identity': {
            'Meta': {'object_name': 'Identity'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36'})
        }
    }
    
    complete_apps = ['identity_client']
