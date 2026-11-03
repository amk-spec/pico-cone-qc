"""Hosted transport/auth safeguards. Run separately with hosted settings enabled."""
import contextlib
import io
import os
from pathlib import Path
from unittest.mock import patch
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, Client, override_settings
from qc.models import Organization, Profile, Attachment

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class HostedPreviewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        org=Organization.objects.create(code='PICOGRID',name='Picogrid')
        cls.user=get_user_model().objects.create_user('preview-reviewer',password='synthetic-login-fixture-123')
        Profile.objects.create(user=cls.user,organization=org)

    def test_hosted_mode_is_explicit_and_not_debug(self):
        self.assertTrue(settings.HOSTED_PREVIEW)
        self.assertFalse(settings.DEBUG)
        self.assertTrue(settings.SESSION_COOKIE_SECURE)
        self.assertTrue(settings.CSRF_COOKIE_SECURE)
        self.assertTrue(settings.AXES_ENABLED)

    def test_http_redirects_to_https(self):
        response=self.client.get('/login/',HTTP_HOST='preview.test')
        self.assertEqual(response.status_code,301)
        self.assertEqual(response['Location'],'https://preview.test/login/')

    def test_record_routes_and_downloads_are_password_protected(self):
        for path in ['/', '/records/','/sources/','/decisions/','/authority/','/evidence/00000000-0000-0000-0000-000000000001/']:
            with self.subTest(path=path):
                response=self.client.get(path,secure=True,HTTP_HOST='preview.test')
                self.assertEqual(response.status_code,302)
                self.assertTrue(response['Location'].startswith('/login/?next='))

    def test_named_login_uses_secure_cookie_and_opens_workspace(self):
        response=self.client.post('/login/',{'username':'preview-reviewer','password':'synthetic-login-fixture-123'},secure=True,HTTP_HOST='preview.test')
        self.assertEqual(response.status_code,302)
        self.assertTrue(response.cookies['sessionid']['secure'])
        self.assertEqual(self.client.get('/',secure=True,HTTP_HOST='preview.test').status_code,200)

    def test_brute_force_lockout_blocks_correct_password_after_limit(self):
        for _ in range(5):
            self.client.post('/login/',{'username':'preview-reviewer','password':'wrong'},secure=True,HTTP_HOST='preview.test')
        response=self.client.post('/login/',{'username':'preview-reviewer','password':'synthetic-login-fixture-123'},secure=True,HTTP_HOST='preview.test')
        self.assertEqual(response.status_code,429)
        self.assertContains(response,'Try again in 15 minutes',status_code=429)

    def test_secure_post_requires_csrf(self):
        client=Client(enforce_csrf_checks=True)
        response=client.post('/login/',{'username':'preview-reviewer','password':'synthetic-login-fixture-123'},secure=True,HTTP_HOST='preview.test')
        self.assertEqual(response.status_code,403)

    def test_health_exposes_no_qc_records_or_database_identity(self):
        response=self.client.get('/health/',HTTP_HOST='preview.test')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json(),{'status':'ok','mode':'prototype'})

    def test_unknown_host_rejected(self):
        self.assertEqual(self.client.get('/login/',secure=True,HTTP_HOST='untrusted.example').status_code,400)

    def test_hosted_seeding_requires_secret_before_writing_records(self):
        with patch.dict(os.environ,{'LANDER_PREVIEW_OWNER_PASSWORD':''}):
            with self.assertRaises(CommandError):call_command('seed_demo',stdout=io.StringIO())
        self.assertFalse(get_user_model().objects.filter(username='owner').exists())

    def test_hosted_seed_has_no_source_uploads_or_plaintext_credential_file(self):
        password='synthetic-preview-seed-fixture-123'
        local=Path(settings.LOCAL_DIR)/'demo-accounts.txt'
        existed=local.exists()
        output=io.StringIO()
        with patch.dict(os.environ,{'LANDER_PREVIEW_OWNER_PASSWORD':password}):
            call_command('seed_demo',stdout=output)
            owner=get_user_model().objects.get(username='owner')
            self.assertTrue(owner.check_password(password))
            self.assertEqual(Attachment.objects.count(),0)
            call_command('seed_demo',stdout=output)
        self.assertNotIn(password,output.getvalue())
        self.assertEqual(local.exists(),existed)

    def test_hosted_password_rotation_preserves_records(self):
        first='synthetic-first-preview-fixture-123'
        second='synthetic-second-preview-fixture-456'
        with patch.dict(os.environ,{'LANDER_PREVIEW_OWNER_PASSWORD':first}):call_command('seed_demo',stdout=io.StringIO())
        from qc.models import WorkOrder
        before=WorkOrder.objects.count()
        with patch.dict(os.environ,{'LANDER_PREVIEW_OWNER_PASSWORD':second}):call_command('seed_demo',stdout=io.StringIO())
        self.assertTrue(get_user_model().objects.get(username='owner').check_password(second))
        self.assertEqual(WorkOrder.objects.count(),before)
