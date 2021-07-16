import re
import base64
import xml.dom.minidom
import zlib

from xml.parsers.expat import ExpatError


def repr_saml_request(saml_str, b64=False):
    """Decode SAML request from b64 and b64 deflated
    and return a pretty printed representation
    """
    try:
        msg = base64.b64decode(saml_str).decode() if b64 else saml_str
        dom = xml.dom.minidom.parseString(msg)
    except (UnicodeDecodeError, ExpatError) as err:
        # in HTTP-REDIRECT the base64 must be inflated
        msg = base64.b64decode(saml_str) if b64 else saml_str
        try:
            inflated = zlib.decompress(msg, -15)
        except (zlib.error, TypeError):
            raise err from None

        dom = xml.dom.minidom.parseString(inflated.decode())
    return dom.toprettyxml()


def encode_http_redirect_saml(saml_envelope):
    return base64.b64encode(zlib.compress(saml_envelope.encode()))


def saml_request_from_html_form(html_str):
    regexp = 'name="SAMLRequest" value="(?P<value>[a-zA-Z0-9+=]*)"'
    authn_request = re.findall(regexp, html_str)
    if not authn_request:
        raise ValueError("AuthnRequest not found in htmlform")

    return authn_request[0]
