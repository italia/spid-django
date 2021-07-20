import os
import io
import glob
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ElementTree
from xml.parsers.expat import ExpatError
import zlib
import binascii
import base64
import pathlib

from saml2 import BINDING_HTTP_POST  # , BINDING_HTTP_REDIRECT
from saml2.saml import NAMEID_FORMAT_TRANSIENT, NAMEID_FORMAT_ENCRYPTED
from saml2.xmldsig import DIGEST_SHA256, DIGEST_SHA512, SIG_RSA_SHA256, SIG_RSA_SHA512

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.http import HttpResponseBadRequest
from django.test import (
    SimpleTestCase,
    Client,
    TestCase,
    RequestFactory,
    override_settings,
)
from django.urls import reverse
from django.conf import settings

from djangosaml2.conf import get_config_loader, get_config

from .conf import config_settings_loader
from .utils import repr_saml_request, saml_request_from_html_form
from .spid_errors import SpidError

base_dir = pathlib.Path(settings.BASE_DIR)


def dummy_loader():
    return


# noinspection PyTypeChecker
class TestSpidError(SimpleTestCase):
    def test_initialization(self):
        error = SpidError(19)
        self.assertEqual(error.code, 19)
        self.assertEqual(error.status_message, "ErrorCode nr19")
        self.assertEqual(
            error.description,
            "Autenticazione fallita per ripetuta sottomissione di credenziali "
            "errate - superato numero tentativi secondo le policy adottate",
        )
        self.assertEqual(
            error.message,
            "Autenticazione fallita per ripetuta sottomissione di credenziali errate",
        )
        self.assertEqual(error.troubleshoot, "Inserire credenziali corrette")

        with self.assertRaises(ValueError) as ctx:
            SpidError(-1)
        self.assertEqual(str(ctx.exception), "-1 is not a SPID error code")

        with self.assertRaises(TypeError) as ctx:
            SpidError("19")
        self.assertEqual(str(ctx.exception), "'19' is not a SPID error code")

    def test_from_error(self):
        error = SpidError.from_error("ErrorCode nr19")
        self.assertEqual(error.code, 19)

        error = SpidError.from_error(ValueError("ErrorCode nr19"))
        self.assertEqual(error.code, 19)
        self.assertIs(SpidError.from_error(error), error)

        with self.assertRaises(ValueError) as ctx:
            SpidError.from_error("19")
        self.assertEqual(
            str(ctx.exception), "cannot create a SpidError instance from '19'"
        )

        with self.assertRaises(TypeError) as ctx:
            SpidError.from_error(19)
        self.assertEqual(
            str(ctx.exception), "cannot create a SpidError instance from 19"
        )

    def test_from_saml2_error(self):
        error = SpidError.from_saml2_error(SpidError(19))
        self.assertEqual(error.code, 19)
        self.assertIs(SpidError.from_saml2_error(error), error)

        with self.assertRaises(TypeError) as ctx:
            SpidError.from_saml2_error("ErrorCode nr19")
        self.assertEqual(
            str(ctx.exception), "'ErrorCode nr19' is not a SAML2 authentication error"
        )

    def test_repr(self):
        error = SpidError(25)
        self.assertEqual(repr(error), "SpidError(code=25)")

    def test_string_repr(self):
        error = SpidError(25)
        self.assertEqual(str(error), "Processo di autenticazione annullato dall'utente")

        error = SpidError(19)
        self.assertEqual(
            str(error),
            "Autenticazione fallita per ripetuta sottomissione di credenziali errate"
            "\n\nInserire credenziali corrette",
        )
        error = SpidError(17)
        self.assertEqual(str(error), "Accesso negato")


class TestSpidConfig(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_config_loader(self):
        func = get_config_loader("djangosaml2_spid.tests.dummy_loader")
        self.assertIs(func, dummy_loader)

        func = get_config_loader("djangosaml2_spid.conf.config_settings_loader")
        self.assertIs(func, config_settings_loader)

    def test_get_config(self):
        saml_config = get_config()
        self.assertIsNone(saml_config.entityid)

        # SPConfig for a SPID request
        request = self.factory.get("/spid/metadata")
        saml_config = get_config(request=request)
        if base_dir.name != "example":
            self.assertEqual(saml_config.entityid, "http://testserver/spid/metadata/")
        else:
            self.assertEqual(
                saml_config.entityid, "https://localhost:8000/spid/metadata/"
            )

    @unittest.skipIf(base_dir.name == "example", "Skip for demo project")
    def test_default_spid_saml_config(self):
        request = self.factory.get("/spid/metadata")
        saml_config = get_config(request=request)
        self.assertEqual(saml_config.entityid, "http://testserver/spid/metadata/")

        self.assertEqual(saml_config.name_qualifier, "")  # ???

        self.assertEqual(saml_config._sp_name, "http://testserver/spid/metadata/")
        self.assertEqual(saml_config._sp_name_id_format, [NAMEID_FORMAT_TRANSIENT])
        self.assertEqual(saml_config._sp_digest_algorithm, DIGEST_SHA256)
        self.assertEqual(saml_config._sp_signing_algorithm, SIG_RSA_SHA256)

        self.assertEqual(
            saml_config._sp_endpoints,
            {
                "assertion_consumer_service": [
                    (
                        "http://testserver/spid/acs/",
                        "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                    )
                ],
                "single_logout_service": [
                    (
                        "http://testserver/spid/ls/post/",
                        "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                    )
                ],
            },
        )

        metadata_files = list(saml_config.metadata.metadata)

        if base_dir.name == "example":
            self.assertEqual(
                saml_config.cert_file,
                str(base_dir.joinpath("certificates/public.cert")),
            )
            self.assertEqual(
                saml_config.key_file, str(base_dir.joinpath("certificates/private.key"))
            )

            self.assertIn(
                str(base_dir.joinpath("spid_config/metadata/satosa-spid.xml")),
                metadata_files,
            ),
            self.assertIn(
                str(base_dir.joinpath("spid_config/metadata/spid-saml-check.xml")),
                metadata_files,
            )
        else:
            self.assertEqual(saml_config.cert_file, "tests/certificates/public.cert")
            self.assertEqual(saml_config.key_file, "tests/certificates/private.key")
            self.assertIn("tests/metadata/spid-saml-check.xml", metadata_files)

        self.assertEqual(
            saml_config.organization,
            {
                "name": [("Example", "it"), ("Example", "en")],
                "display_name": [("Example", "it"), ("Example", "en")],
                "url": [
                    ("http://www.example.it", "it"),
                    ("http://www.example.it", "en"),
                ],
            },
        )

    @override_settings(
        SAML_CONFIG={
            "debug": True,
            "organization": settings.SAML_CONFIG["organization"],
        }
    )
    def test_saml_debug_mode(self):
        request = self.factory.get("/spid/metadata")
        saml_config = get_config(request=request)
        self.assertTrue(saml_config.debug)

    @override_settings(
        SAML_CONFIG={
            "organization": settings.SAML_CONFIG["organization"],
        }
    )
    def test_saml_no_debug_mode(self):
        request = self.factory.get("/spid/metadata")
        saml_config = get_config(request=request)
        self.assertFalse(saml_config.debug)

    @override_settings(SPID_NAMEID_FORMAT=NAMEID_FORMAT_ENCRYPTED)
    def test_spid_public_cert(self):
        request = self.factory.get("/spid/metadata")
        saml_config = get_config(request=request)
        self.assertEqual(saml_config._sp_name_id_format, [NAMEID_FORMAT_ENCRYPTED])

    @override_settings(SPID_DIG_ALG=DIGEST_SHA512, SPID_SIG_ALG=SIG_RSA_SHA512)
    def test_spid_digest_and_signing_algorithms(self):
        request = self.factory.get("/spid/metadata")
        saml_config = get_config(request=request)
        self.assertEqual(saml_config._sp_digest_algorithm, DIGEST_SHA512)
        self.assertEqual(saml_config._sp_signing_algorithm, SIG_RSA_SHA512)

    @unittest.skipIf(base_dir.name == "example", "Skip for demo project")
    @override_settings(SPID_PRIVATE_KEY="example/certificates/private.key")
    def test_spid_private_key(self):
        request = self.factory.get("/spid/metadata")
        saml_config = get_config(request=request)
        self.assertEqual(saml_config.key_file, "example/certificates/private.key")
        self.assertEqual(saml_config.cert_file, "tests/certificates/public.cert")
        self.assertListEqual(
            saml_config.encryption_keypairs,
            [
                {
                    "key_file": "example/certificates/private.key",
                    "cert_file": "tests/certificates/public.cert",
                }
            ],
        )

    @unittest.skipIf(base_dir.name == "example", "Skip for demo project")
    @override_settings(SPID_PUBLIC_CERT="example/certificates/public.cert")
    def test_spid_public_cert(self):
        request = self.factory.get("/spid/metadata")
        saml_config = get_config(request=request)
        self.assertEqual(saml_config.key_file, "tests/certificates/private.key")
        self.assertEqual(saml_config.cert_file, "example/certificates/public.cert")
        self.assertListEqual(
            saml_config.encryption_keypairs,
            [
                {
                    "key_file": "tests/certificates/private.key",
                    "cert_file": "example/certificates/public.cert",
                }
            ],
        )


class TestUtils(unittest.TestCase):
    def test_repr_saml_request(self):
        xml_str = repr_saml_request("PGZvby8+", b64=True)
        self.assertEqual(xml_str, '<?xml version="1.0" ?>\n<foo/>\n')

        xml_str = repr_saml_request(b"PGZvby8+", b64=True)
        self.assertEqual(xml_str, '<?xml version="1.0" ?>\n<foo/>\n')

        xml_str = repr_saml_request("<foo/>")
        self.assertEqual(xml_str, '<?xml version="1.0" ?>\n<foo/>\n')

        xml_str = repr_saml_request(b"<foo/>")
        self.assertEqual(xml_str, '<?xml version="1.0" ?>\n<foo/>\n')

        with self.assertRaises(ExpatError):
            repr_saml_request(b"PGZvby8+")

        with self.assertRaises(ExpatError):
            repr_saml_request("foo")

        with self.assertRaises(binascii.Error):
            repr_saml_request("foo", b64=True)

    def test_repr_saml_request_with_compressed_data(self):
        compressor = zlib.compressobj(wbits=-15)
        zipped_data = compressor.compress(b"<foo/>")
        zipped_data += compressor.flush()

        xml_str = repr_saml_request(zipped_data)
        self.assertEqual(xml_str, '<?xml version="1.0" ?>\n<foo/>\n')

        with self.assertRaises(binascii.Error):
            repr_saml_request(zipped_data, b64=True)

        xml_str = repr_saml_request(base64.b64encode(zipped_data), b64=True)
        self.assertEqual(xml_str, '<?xml version="1.0" ?>\n<foo/>\n')

    def test_saml_request_from_html_form(self):
        with self.assertRaises(ValueError):
            saml_request_from_html_form("<empty/>")

        with self.assertRaises(ValueError):
            saml_request_from_html_form('<input name="SAMLRequest" value="???"/>')

        saml_str = saml_request_from_html_form(
            '<input name="SAMLRequest" value="PGZvby8+"/>'
        )
        self.assertEqual(saml_str, "PGZvby8+")


class TestCommands(TestCase):
    @patch("sys.stderr", new_callable=io.StringIO)
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_update_idps_command(self, mock_out, mock_err):
        metadata_dir = settings.SPID_IDENTITY_PROVIDERS_METADATA_DIR
        self.assertTrue(metadata_dir.endswith("metadata/"))
        self.assertTrue(os.path.isdir(metadata_dir))

        idp_files_wildcard = os.path.join(metadata_dir, "idp_*.xml")
        for filename in glob.glob(idp_files_wildcard):
            os.remove(filename)

        self.assertListEqual(glob.glob(idp_files_wildcard), [])
        call_command("update_idps")

        self.assertEqual(len(glob.glob(idp_files_wildcard)), 9)
        self.assertEqual(mock_err.getvalue(), "")

        success_message = "Successfully wrote all IdPs metadata XML files"
        self.assertIn(success_message, mock_out.getvalue().strip().split("\n")[-1])


class TestSpid(TestCase):
    def setUp(self):
        self.create_user()

    @classmethod
    def create_user(cls, **kwargs):
        data = {
            "username": "foo",
            "first_name": "foo",
            "last_name": "bar",
            "email": "that@mail.org",
        }
        for k, v in kwargs.items():
            data[k] = v
        user = get_user_model().objects.create(**data)
        return user

    def test_metadata_endpoint(self):
        url = reverse("djangosaml2_spid:spid_metadata")
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
            metadata_xml.tag, "{urn:oasis:names:tc:SAML:2.0:metadata}EntityDescriptor"
        )
        self.assertEqual(
            metadata_xml.find(".//spid:VATNumber", namespaces).text, "IT12345678901"
        )
        self.assertEqual(
            metadata_xml.find(".//spid:FiscalCode", namespaces).text, "XYZABCAAMGGJ000W"
        )

    @override_settings(SAML2_DEFAULT_BINDING=BINDING_HTTP_POST)
    def test_authnreq_post(self):
        url = reverse("djangosaml2_spid:spid_login")
        client = Client()
        res = client.get(f"{url}?idp=https://localhost:8080")
        self.assertEqual(res.status_code, 200)

        html_form = res.content.decode()
        encoded_authn_req = saml_request_from_html_form(html_form)

        fancy_saml = repr_saml_request(encoded_authn_req.encode(), b64=True)
        self.assertNotIn("ns0", fancy_saml)

        lines = fancy_saml.split("\n")
        self.assertEqual(lines[0], '<?xml version="1.0" ?>')
        self.assertTrue(lines[1].startswith("<samlp:AuthnRequest "))
        self.assertEqual(lines[-2], "</samlp:AuthnRequest>")

    def test_authnreq_already_logged_user(self):
        url = reverse("djangosaml2_spid:index")
        client = Client()
        user = get_user_model().objects.first()
        client.force_login(user)
        res = client.get(f"{url}")

        self.assertEqual(res.status_code, 200)
        self.assertIn(b"LOGGED IN:", res.content)
        self.assertIn(b"first_name: foo", res.content)
        self.assertIn(b"last_name: bar", res.content)
        self.assertIn(b"is_active: True", res.content)
        self.assertIn(b"is_superuser: False", res.content)
        self.assertIn(b"is_staff: False", res.content)

    def test_logout(self):
        logout_url = reverse("djangosaml2_spid:spid_logout")
        client = Client()
        user = get_user_model().objects.first()
        client.force_login(user)

        with self.assertLogs("djangosaml2", level="WARNING") as ctx:
            res = client.get(logout_url)

        self.assertEqual(res.status_code, 400)
        self.assertIsInstance(res, HttpResponseBadRequest)

        self.assertEqual(len(ctx.output), 2)
        self.assertIn(
            "WARNING:djangosaml2:The session does not contain "
            "the subject id for user AnonymousUser",
            ctx.output,
        )
        self.assertIn(
            "ERROR:djangosaml2:Looks like the user None is not " "logged in any IdP/AA",
            ctx.output,
        )

    def test_echo_attributes(self):
        url = reverse("djangosaml2_spid:spid_echo_attributes")
        client = Client()
        user = get_user_model().objects.first()
        client.force_login(user)
        res = client.get(f"{url}")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.content,
            b"No active SAML identity found. Are you "
            b"sure you have logged in via SAML?",
        )


class TestSaml2Patches(unittest.TestCase):

    def test_default_namespaces(self):
        oasis_default_nsmap = {
            'saml': 'urn:oasis:names:tc:SAML:2.0:assertion',
            'samlp': 'urn:oasis:names:tc:SAML:2.0:protocol',
            'ds': 'http://www.w3.org/2000/09/xmldsig#',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xs': 'http://www.w3.org/2001/XMLSchema',
            'mdui': 'urn:oasis:names:tc:SAML:metadata:ui',
            'md': 'urn:oasis:names:tc:SAML:2.0:metadata',
            'xenc': 'http://www.w3.org/2001/04/xmlenc#',
            'alg': 'urn:oasis:names:tc:SAML:metadata:algsupport',
            'mdattr': 'urn:oasis:names:tc:SAML:metadata:attribute',
            'idpdisc': 'urn:oasis:names:tc:SAML:profiles:SSO:idp-discovery-protocol',
        }

        for prefix, uri in oasis_default_nsmap.items():
            self.assertIn(uri, ElementTree._namespace_map)
            self.assertEqual(prefix, ElementTree._namespace_map[uri])

    def test_disable_weak_xmlsec_algorithms(self):
        import saml2.metadata
        from saml2.algsupport import algorithm_support_in_metadata

        self.assertIsNot(saml2.metadata.algorithm_support_in_metadata, algorithm_support_in_metadata)
        self.assertEqual(saml2.metadata.algorithm_support_in_metadata.__module__, 'djangosaml2_spid._saml2')

    def test_add_xsd_date_type(self):
        from saml2.saml import AttributeValueBase
        self.assertEqual(AttributeValueBase.set_text.__module__, 'djangosaml2_spid._saml2')

    def test_patch_response_verify(self):
        from saml2.response import StatusResponse
        self.assertEqual(StatusResponse._verify.__module__, 'djangosaml2_spid._saml2')
