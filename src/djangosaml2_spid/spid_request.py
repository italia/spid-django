import logging

import saml2
from django.conf import settings
from django.urls import reverse
from djangosaml2.overrides import Saml2Client
from saml2.authn_context import requested_authn_context


SPID_DEFAULT_BINDING = settings.SPID_DEFAULT_BINDING

logger = logging.getLogger('djangosaml2')


def spid_sp_authn_request(conf, selected_idp, next_url=''):
    client = Saml2Client(conf)

    logger.debug(f'Redirecting user to the IdP via {SPID_DEFAULT_BINDING} binding.')

    # use the html provided by pysaml2 if no template was specified or it didn't exist
    # SPID want the fqdn of the IDP, not the SSO endpoint
    location_fixed = selected_idp
    location = client.sso_location(selected_idp, SPID_DEFAULT_BINDING)

    authn_req = saml2.samlp.AuthnRequest()
    authn_req.destination = location_fixed
    # spid-testenv2 preleva l'attribute consumer service dalla authnRequest (anche se questo sta già nei metadati...)
    authn_req.attribute_consuming_service_index = "0"

    # issuer
    issuer = saml2.saml.Issuer()
    issuer.name_qualifier = client.config.entityid
    issuer.text = client.config.entityid
    issuer.format = "urn:oasis:names:tc:SAML:2.0:nameid-format:entity"
    authn_req.issuer = issuer

    # message id
    authn_req.id = saml2.s_utils.sid()
    authn_req.version = saml2.VERSION  # "2.0"
    authn_req.issue_instant = saml2.time_util.instant()

    name_id_policy = saml2.samlp.NameIDPolicy()
    name_id_policy.format = settings.SPID_NAMEID_FORMAT
    authn_req.name_id_policy = name_id_policy

    authn_context = requested_authn_context(class_ref=settings.SPID_AUTH_CONTEXT)
    authn_req.requested_authn_context = authn_context

    # if SPID authentication level is > 1 then forceauthn must be True
    authn_req.force_authn = 'true'

    authn_req.protocol_binding = SPID_DEFAULT_BINDING

    assertion_consumer_service_url = client.config._sp_endpoints['assertion_consumer_service'][0][0]
    authn_req.assertion_consumer_service_url = assertion_consumer_service_url

    authn_req_signed = client.sign(
        authn_req,
        sign_prepare=False,
        sign_alg=settings.SPID_SIG_ALG,
        digest_alg=settings.SPID_DIG_ALG,
    )

    logger.debug(f'AuthRequest to {selected_idp}: {authn_req_signed}')

    relay_state = next_url or reverse('djangosaml2:saml2_echo_attributes')
    http_info = client.apply_binding(
        SPID_DEFAULT_BINDING,
        authn_req_signed,
        location,
        sign=True,
        sigalg=settings.SPID_SIG_ALG,
        relay_state=relay_state
    )

    return dict(
        http_response=http_info,
        authn_request=authn_req_signed,
        relay_state=relay_state,
        session_id=authn_req.id
    )