import os
import re
import xml.etree.ElementTree as ElementTree

from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseBadRequest
from django.test import Client, TestCase, RequestFactory
from django.urls import reverse

from djangosaml2.conf import get_config_loader, get_config

from .conf import config_settings_loader
from .utils import repr_saml


def samlrequest_from_html_form(htmlstr):
    regexp = 'name="SAMLRequest" value="(?P<value>[a-zA-Z0-9+=]*)"'
    authn_request = re.findall(regexp, htmlstr)
    if not authn_request:
        raise Exception('AuthnRequest not found in htmlform')
    
    return authn_request[0]


def repr_samlrequest(authnreqstr, **kwargs):
    return repr_saml(authnreqstr, **kwargs)


def dummy_loader():
    return


class TestSpidConfig(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_get_config_loader(self):
        func = get_config_loader('djangosaml2_spid.tests.dummy_loader')
        self.assertIs(func, dummy_loader)

        func = get_config_loader('djangosaml2_spid.conf.config_settings_loader')
        self.assertIs(func, config_settings_loader)

    def test_get_config(self):
        saml_config = get_config()
        self.assertEqual(saml_config.entityid, 'http://localhost:8000/spid/metadata')

        request = self.factory.get('')
        saml_config = get_config(request=request)
        self.assertEqual(saml_config.entityid, 'http://localhost:8000/spid/metadata')

        request = self.factory.get('/spid/metadata')
        saml_config = get_config(request=request)
        self.assertEqual(saml_config.entityid, 'http://testserver/spid/metadata')
        self.assertEqual(
            saml_config.organization,
            {'name': [('Example', 'it'), ('Example', 'en')],
             'display_name': [('Example', 'it'), ('Example', 'en')],
             'url': [('http://www.example.it', 'it'), ('http://www.example.it', 'en')]}
        )


class TestStaticFiles(TestCase):

    def test_spid_logo(self):
        abs_path = finders.find('spid/logo.jpg')
        self.assertTrue(os.path.isfile(abs_path))

        # For using staticfiles_storage you have to configure STATIC_ROOT setting
        with self.assertRaises(ImproperlyConfigured):
            staticfiles_storage.exists(abs_path)

    def test_idp_logos(self):
        abs_path = finders.find('spid/spid-idp-intesaid.svg')
        self.assertTrue(os.path.isfile(abs_path))

        abs_path = finders.find('spid/spid-idp-posteid.svg')
        self.assertTrue(os.path.isfile(abs_path))

    def test_css_files(self):
        abs_path = finders.find('spid/spid-sp-access-button.css')
        self.assertTrue(os.path.isfile(abs_path))

    def test_scripts(self):
        abs_path = finders.find('spid/brython.js')
        self.assertTrue(os.path.isfile(abs_path))

        abs_path = finders.find('spid/spid_button.js')
        self.assertTrue(os.path.isfile(abs_path))

        abs_path = finders.find('spid/spid-sp-access-button.js')
        self.assertTrue(os.path.isfile(abs_path))


class TestSpid(TestCase):

    def setUp(self):
        self.create_user()

    @classmethod
    def create_user(cls, **kwargs):
        data = {'username': 'foo',
                'first_name': 'foo',
                'last_name': 'bar',
                'email': 'that@mail.org'}
        for k, v in kwargs.items():
            data[k] = v
        user = get_user_model().objects.create(**data)
        return user

    def test_metadata_endpoint(self):
        url = reverse('djangosaml2_spid:spid_metadata')
        client = Client()
        res = client.get(url)

        self.assertEqual(res.status_code, 200)

        # TODO: here validation with spid saml tests
        # ...
        #

        metadata_xml = ElementTree.fromstring(res.content)
        namespaces = dict(
            md="urn:oasis:names:tc:SAML:2.0:metadata",
            spid="https://spid.gov.it/saml-extensions",
            fpa="https://spid.gov.it/invoicing-extensions",
        )
        self.assertEqual(
            metadata_xml.tag, '{urn:oasis:names:tc:SAML:2.0:metadata}EntityDescriptor')
        self.assertEqual(
            metadata_xml.find('.//spid:VATNumber', namespaces).text, 'IT12345678901')
        self.assertEqual(
            metadata_xml.find('.//spid:FiscalCode', namespaces).text, 'XYZABCAAMGGJ000W')

    def test_authnreq(self):
        url = reverse('djangosaml2_spid:spid_login')
        client = Client()
        res = client.get(f'{url}?idp=http://localhost:54321')
        self.assertEqual(res.status_code, 200)
        
        html_form = res.content.decode()
        encoded_authn_req = samlrequest_from_html_form(html_form)
        
        fancy_saml = repr_samlrequest(encoded_authn_req.encode(), b64=1)
        self.assertNotIn('ns0', fancy_saml)
        
        lines = fancy_saml.split('\n')
        self.assertEqual(lines[0], '<?xml version="1.0" ?>')
        self.assertTrue(lines[1].startswith('<samlp:AuthnRequest '))
        self.assertEqual(lines[-2], '</samlp:AuthnRequest>')

    def test_authnreq_already_logged_user(self):
        url = reverse('djangosaml2_spid:index')
        client = Client()
        user = get_user_model().objects.first()
        client.force_login(user)
        res = client.get(f'{url}')

        self.assertEqual(res.status_code, 200)
        self.assertIn(b'LOGGED IN:', res.content)
        self.assertIn(b'first_name: foo', res.content)
        self.assertIn(b'last_name: bar', res.content)
        self.assertIn(b'is_active: True', res.content)
        self.assertIn(b'is_superuser: False', res.content)
        self.assertIn(b'is_staff: False', res.content)

    def test_logout(self):
        logout_url = reverse('djangosaml2_spid:spid_logout')
        client = Client()
        user = get_user_model().objects.first()
        client.force_login(user)

        with self.assertLogs('djangosaml2', level='WARNING') as ctx:
            res = client.get(logout_url)

        self.assertEqual(res.status_code, 400)
        self.assertIsInstance(res, HttpResponseBadRequest)

        self.assertEqual(len(ctx.output), 2)
        self.assertIn('WARNING:djangosaml2:The session does not contain '
                      'the subject id for user AnonymousUser', ctx.output)
        self.assertIn('ERROR:djangosaml2:Looks like the user None is not '
                      'logged in any IdP/AA', ctx.output)

    def test_echo_attributes(self):
        url = reverse('djangosaml2_spid:spid_echo_attributes')
        client = Client()
        user = get_user_model().objects.first()
        client.force_login(user)
        res = client.get(f'{url}')

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, b'No active SAML identity found. Are you '
                                      b'sure you have logged in via SAML?')
