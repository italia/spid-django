import os
import unittest
import xml.etree.ElementTree as ElementTree
from xml.parsers.expat import ExpatError
import zlib
import binascii
import base64
import pathlib

from saml2 import BINDING_HTTP_REDIRECT, BINDING_HTTP_POST
from saml2.saml import NAMEID_FORMAT_TRANSIENT, NAMEID_FORMAT_ENCRYPTED
from saml2.xmldsig import DIGEST_SHA256, DIGEST_SHA512, SIG_RSA_SHA256, SIG_RSA_SHA512

from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseBadRequest
from django.test import Client, TestCase, RequestFactory, override_settings
from django.urls import reverse
from django.conf import settings

from djangosaml2.conf import get_config_loader, get_config

from .conf import config_settings_loader
from .utils import repr_saml_request, saml_request_from_html_form


base_dir = pathlib.Path(settings.BASE_DIR)


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
        self.assertEqual(saml_config.entityid, 'http://testserver/spid/metadata/')

    def test_default_spid_saml_config(self):
        request = self.factory.get('/spid/metadata')
        saml_config = get_config(request=request)
        self.assertEqual(saml_config.entityid, 'http://testserver/spid/metadata/')

        self.assertEqual(saml_config.name_qualifier, '')  # ???

        self.assertEqual(saml_config._sp_name, 'http://testserver/spid/metadata/')
        self.assertEqual(saml_config._sp_name_id_format, [NAMEID_FORMAT_TRANSIENT])
        self.assertEqual(saml_config._sp_digest_algorithm, DIGEST_SHA256)
        self.assertEqual(saml_config._sp_signing_algorithm, SIG_RSA_SHA256)

        self.assertEqual(saml_config._sp_endpoints, {
            'assertion_consumer_service': [
                ('http://testserver/spid/acs/',
                 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST')
            ],
            'single_logout_service': [
                ('http://testserver/spid/ls/post/',
                 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST')]
        })

        metadata_files = list(saml_config.metadata.metadata)

        if base_dir.name == 'example':
            self.assertEqual(saml_config.cert_file,
                             str(base_dir.joinpath('certificates/public.cert')))
            self.assertEqual(saml_config.key_file,
                             str(base_dir.joinpath('certificates/private.key')))

            self.assertIn(str(base_dir.joinpath('spid_config/metadata/satosa-spid.xml')),
                          metadata_files),
            self.assertIn(str(base_dir.joinpath('spid_config/metadata/spid-saml-check.xml')),
                          metadata_files)
        else:
            self.assertEqual(saml_config.cert_file, 'tests/certificates/public.cert')
            self.assertEqual(saml_config.key_file, 'tests/certificates/private.key')
            self.assertIn('tests/metadata/satosa-spid.xml', metadata_files)
            self.assertIn('tests/metadata/spid-saml-check.xml', metadata_files)

        self.assertEqual(
            saml_config.organization,
            {'name': [('Example', 'it'), ('Example', 'en')],
             'display_name': [('Example', 'it'), ('Example', 'en')],
             'url': [('http://www.example.it', 'it'), ('http://www.example.it', 'en')]}
        )

    @override_settings(SPID_NAMEID_FORMAT=NAMEID_FORMAT_ENCRYPTED)
    def test_spid_public_cert(self):
        request = self.factory.get('/spid/metadata')
        saml_config = get_config(request=request)
        self.assertEqual(saml_config._sp_name_id_format, [NAMEID_FORMAT_ENCRYPTED])

    @override_settings(SPID_DIG_ALG=DIGEST_SHA512, SPID_SIG_ALG=SIG_RSA_SHA512)
    def test_spid_digest_and_signing_algorithms(self):
        request = self.factory.get('/spid/metadata')
        saml_config = get_config(request=request)
        self.assertEqual(saml_config._sp_digest_algorithm, DIGEST_SHA512)
        self.assertEqual(saml_config._sp_signing_algorithm, SIG_RSA_SHA512)

    @unittest.skipIf(base_dir.name == 'example', "Skip for demo project")
    @override_settings(SPID_PRIVATE_KEY='example/certificates/private.key')
    def test_spid_private_key(self):
        request = self.factory.get('/spid/metadata')
        saml_config = get_config(request=request)
        self.assertEqual(saml_config.key_file, 'example/certificates/private.key')
        self.assertEqual(saml_config.cert_file, 'tests/certificates/public.cert')
        self.assertListEqual(saml_config.encryption_keypairs, [{
            'key_file': 'example/certificates/private.key',
            'cert_file': 'tests/certificates/public.cert'
        }])

    @unittest.skipIf(base_dir.name == 'example', "Skip for demo project")
    @override_settings(SPID_PUBLIC_CERT='example/certificates/public.cert')
    def test_spid_public_cert(self):
        request = self.factory.get('/spid/metadata')
        saml_config = get_config(request=request)
        self.assertEqual(saml_config.key_file, 'tests/certificates/private.key')
        self.assertEqual(saml_config.cert_file, 'example/certificates/public.cert')
        self.assertListEqual(saml_config.encryption_keypairs, [{
            'key_file': 'tests/certificates/private.key',
            'cert_file': 'example/certificates/public.cert'
        }])


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


class TestUtils(unittest.TestCase):

    def test_repr_saml_request(self):
        xml_str = repr_saml_request('PGZvby8+', b64=True)
        self.assertEqual(xml_str, '<?xml version="1.0" ?>\n<foo/>\n')

        xml_str = repr_saml_request(b'PGZvby8+', b64=True)
        self.assertEqual(xml_str, '<?xml version="1.0" ?>\n<foo/>\n')

        xml_str = repr_saml_request('<foo/>')
        self.assertEqual(xml_str, '<?xml version="1.0" ?>\n<foo/>\n')

        xml_str = repr_saml_request(b'<foo/>')
        self.assertEqual(xml_str, '<?xml version="1.0" ?>\n<foo/>\n')

        with self.assertRaises(ExpatError):
            repr_saml_request(b'PGZvby8+')

        with self.assertRaises(ExpatError):
            repr_saml_request('foo')

        with self.assertRaises(binascii.Error):
            repr_saml_request('foo', b64=True)

    def test_repr_saml_request_with_compressed_data(self):
        compressor = zlib.compressobj(wbits=-15)
        zipped_data = compressor.compress(b'<foo/>')
        zipped_data += compressor.flush()

        xml_str = repr_saml_request(zipped_data)
        self.assertEqual(xml_str, '<?xml version="1.0" ?>\n<foo/>\n')

        with self.assertRaises(binascii.Error):
            repr_saml_request(zipped_data, b64=True)

        xml_str = repr_saml_request(base64.b64encode(zipped_data), b64=True)
        self.assertEqual(xml_str, '<?xml version="1.0" ?>\n<foo/>\n')

    def test_saml_request_from_html_form(self):
        with self.assertRaises(ValueError):
            saml_request_from_html_form('<empty/>')

        with self.assertRaises(ValueError):
            saml_request_from_html_form('<input name="SAMLRequest" value="???"/>')

        saml_str = saml_request_from_html_form('<input name="SAMLRequest" value="PGZvby8+"/>')
        self.assertEqual(saml_str, 'PGZvby8+')


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

    @override_settings(SAML2_DEFAULT_BINDING = BINDING_HTTP_POST)
    def test_authnreq_post(self):
        url = reverse('djangosaml2_spid:spid_login')
        client = Client()
        res = client.get(f'{url}?idp=http://localhost:8080')
        self.assertEqual(res.status_code, 200)

        html_form = res.content.decode()
        encoded_authn_req = saml_request_from_html_form(html_form)

        fancy_saml = repr_saml_request(encoded_authn_req.encode(), b64=True)
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
