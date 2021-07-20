#
# Patch pysaml2 library in order to be used within spid-django.
#
DISABLE_WEAK_XMLSEC_ALGORITHMS = True  # https://github.com/IdentityPython/pysaml2/pull/628
ADD_XSD_DATE_TYPE = True  # https://github.com/IdentityPython/pysaml2/pull/602
PATCH_RESPONSE_VERIFY = True  # https://github.com/IdentityPython/pysaml2/pull/812


def pysaml2_patch():
    import base64
    import datetime
    import logging

    import saml2.metadata

    from saml2 import SamlBase
    from saml2.algsupport import get_algorithm_support, DigestMethod, \
        DIGEST_METHODS, SigningMethod, SIGNING_METHODS
    from saml2.response import StatusResponse, RequestVersionTooLow, RequestVersionTooHigh
    from saml2.saml import AttributeValueBase

    if DISABLE_WEAK_XMLSEC_ALGORITHMS:
        from django.conf import settings

        # The additional parameter 'xmlsec_disabled_algs' is replaced with a setting
        # that is checked in a patched saml2.algsupport.algorithm_support_in_metadata.
        settings.SAML_XMLSEC_DISABLED_ALGS = getattr(settings, "SAML_XMLSEC_DISABLED_ALGS", [])

        def algorithm_support_in_metadata(xmlsec):
            if xmlsec is None:
                return []

            support = get_algorithm_support(xmlsec)
            element_list = []
            for alg in support["digest"]:
                if alg in settings.SAML_XMLSEC_DISABLED_ALGS:
                    continue
                element_list.append(DigestMethod(algorithm=DIGEST_METHODS[alg]))
            for alg in support["signing"]:
                if alg in settings.SAML_XMLSEC_DISABLED_ALGS:
                    continue
                element_list.append(SigningMethod(algorithm=SIGNING_METHODS[alg]))
            return element_list

        saml2.metadata.algorithm_support_in_metadata = algorithm_support_in_metadata

    if ADD_XSD_DATE_TYPE:
        def set_text(self, value, base64encode=False):
            def _wrong_type_value(xsd, value):
                msg = 'Type and value do not match: {xsd}:{type}:{value}'
                msg = msg.format(xsd=xsd, type=type(value), value=value)
                raise ValueError(msg)

            if isinstance(value, bytes):
                value = value.decode('utf-8')
            type_to_xsd = {
                str: 'string',
                int: 'integer',
                float: 'float',
                bool: 'boolean',
                type(None): '',
            }
            # entries of xsd-types each declaring:
            # - a corresponding python type
            # - a function to turn a string into that type
            # - a function to turn that type into a text-value
            xsd_types_props = {
                'string': {
                    'type': str,
                    'to_type': str,
                    'to_text': str,
                },
                'date': {
                    'type': datetime.date,
                    'to_type': lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').date(),
                    'to_text': str,
                },
                'integer': {
                    'type': int,
                    'to_type': int,
                    'to_text': str,
                },
                'short': {
                    'type': int,
                    'to_type': int,
                    'to_text': str,
                },
                'int': {
                    'type': int,
                    'to_type': int,
                    'to_text': str,
                },
                'long': {
                    'type': int,
                    'to_type': int,
                    'to_text': str,
                },
                'float': {
                    'type': float,
                    'to_type': float,
                    'to_text': str,
                },
                'double': {
                    'type': float,
                    'to_type': float,
                    'to_text': str,
                },
                'boolean': {
                    'type': bool,
                    'to_type': lambda x: {
                        'true': True,
                        'false': False,
                    }[str(x).lower()],
                    'to_text': lambda x: str(x).lower(),
                },
                'base64Binary': {
                    'type': str,
                    'to_type': str,
                    'to_text': (
                        lambda x: base64.encodebytes(x.encode()) if base64encode else x
                    ),
                },
                'anyType': {
                    'type': type(value),
                    'to_type': lambda x: x,
                    'to_text': lambda x: x,
                },
                '': {
                    'type': type(None),
                    'to_type': lambda x: None,
                    'to_text': lambda x: '',
                },
            }
            xsd_string = (
                'base64Binary' if base64encode
                else self.get_type()
                or type_to_xsd.get(type(value)))
            xsd_ns, xsd_type = (
                ['', type(None)] if xsd_string is None
                else ['', ''] if xsd_string == ''
                else [
                    'xs' if xsd_string in xsd_types_props else '',
                    xsd_string
                ] if ':' not in xsd_string
                else xsd_string.split(':', 1))
            xsd_type_props = xsd_types_props.get(xsd_type, {})
            valid_type = xsd_type_props.get('type', type(None))
            to_type = xsd_type_props.get('to_type', str)
            to_text = xsd_type_props.get('to_text', str)
            # cast to correct type before type-checking
            if type(value) is str and valid_type is not str:
                try:
                    value = to_type(value)
                except (TypeError, ValueError, KeyError):
                    # the cast failed
                    _wrong_type_value(xsd=xsd_type, value=value)
            if type(value) is not valid_type:
                _wrong_type_value(xsd=xsd_type, value=value)
            text = to_text(value)
            self.set_type(
                '{ns}:{type}'.format(ns=xsd_ns, type=xsd_type) if xsd_ns
                else xsd_type if xsd_type
                else '')
            SamlBase.__setattr__(self, 'text', text)
            return self

        AttributeValueBase.set_text = set_text

    if PATCH_RESPONSE_VERIFY:
        logger = logging.getLogger(StatusResponse.__module__)

        def _verify(self):
            if self.request_id and self.in_response_to and \
                    self.in_response_to != self.request_id:
                logger.error("Not the id I expected: %s != %s",
                             self.in_response_to, self.request_id)
                return None

            if self.response.version != "2.0":
                if float(self.response.version) < 2.0:
                    raise RequestVersionTooLow()
                else:
                    raise RequestVersionTooHigh()

            if self.asynchop:
                if not (
                     getattr(self.response, 'destination')
                ):
                    logger.error(
                        f"Invalid response destination in asynchop"
                    )
                    return None
                elif self.response.destination not in self.return_addrs:
                    logger.error(
                        f"{self.response.destination} not in {self.return_addrs}"
                    )
                    return None

            valid = self.issue_instant_ok() and self.status_ok()
            return valid

        StatusResponse._verify = _verify


def register_oasis_default_nsmap():
    """Register OASIS default prefix-namespace associations."""
    from xml.etree import ElementTree

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
        ElementTree.register_namespace(prefix, uri)
