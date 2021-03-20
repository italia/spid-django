from .spid_anomalies import SpidAnomaly
from .utils import repr_saml
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseRedirect
)
from django.shortcuts import render
from django.urls import reverse
from djangosaml2.cache import IdentityCache, OutstandingQueriesCache
from djangosaml2.cache import StateCache
from djangosaml2.conf import get_config
from djangosaml2.overrides import Saml2Client
from djangosaml2.utils import (
    available_idps,
    get_idp_sso_supported_bindings,
    validate_referral_url
)
from saml2 import BINDING_HTTP_REDIRECT, BINDING_HTTP_POST
from saml2.authn_context import requested_authn_context
from saml2.mdstore import UnknownSystemEntity
from saml2.metadata import entity_descriptor, sign_entity_descriptor
from saml2.s_utils import UnsupportedBinding
from saml2.sigver import security_context
import djangosaml2.views as djangosaml2_views
import logging
import saml2


SPID_DEFAULT_BINDING = settings.SPID_DEFAULT_BINDING


logger = logging.getLogger('djangosaml2')


def index(request):
    "Barebone 'diagnostics' view, print user attributes if logged in + login/logout links."

    if request.user.is_authenticated:
        out = f"LOGGED IN: <a href={settings.LOGOUT_URL}>LOGOUT</a><br>"
        out += "".join([
            f'{field.name}: {getattr(request.user, field.name)}</br>'
            for field in request.user._meta.get_fields()
            if field.concrete]
        )
        return HttpResponse(out)
    else:
        return HttpResponse(f"LOGGED OUT: <a href={settings.LOGIN_URL}>LOGIN</a>")


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

    assertion_consumer_service_url = client.config._sp_endpoints['assertion_consumer_service'][settings.SPID_CURRENT_INDEX][0]
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


def spid_login(request, config_loader_path=None, wayf_template='wayf.html', authorization_error_template='djangosaml2/auth_error.html'):
    """SAML Authorization Request initiator

    This view initiates the SAML2 Authorization handshake
    using the pysaml2 library to create the AuthnRequest.
    It uses the SAML 2.0 Http POST protocol binding.
    """

    logger.debug('SPID Login process started')

    next_url = request.GET.get('next', settings.LOGIN_REDIRECT_URL)
    if not next_url:
        logger.warning('The next parameter exists but is empty')
        next_url = settings.LOGIN_REDIRECT_URL

    # Ensure the user-originating redirection url is safe.
    if not validate_referral_url(request, next_url):
        next_url = settings.LOGIN_REDIRECT_URL

    if request.user.is_authenticated:
        redirect_authenticated_user = getattr(settings, 'SAML_IGNORE_AUTHENTICATED_USERS_ON_LOGIN', True)
        if redirect_authenticated_user:
            return HttpResponseRedirect(next_url)
        else:  # pragma: no cover
            logger.debug('User is already logged in')
            return render(request, authorization_error_template, {'came_from': next_url})

    # this works only if request came from wayf
    selected_idp = request.GET.get('idp', None)

    conf = get_config(config_loader_path, request)

    # is a embedded wayf needed?
    idps = available_idps(conf)
    if selected_idp is None and len(idps) > 1:
        logger.debug('A discovery process is needed')
        return render(request, wayf_template, {
            'available_idps': idps.items(),
            'next_url': next_url
        })
    else:
        # otherwise is the first one
        _msg = 'Unable to know which IdP to use'
        try:
            selected_idp = selected_idp or list(idps.keys())[0]
        except TypeError as e:  # pragma: no cover
            logger.error(f'{_msg}: {e}')
            return HttpResponseNotFound(_msg)
        except IndexError as e:  # pragma: no cover
            logger.error(f'{_msg}: {e}')
            return HttpResponseNotFound(_msg)

    # ensure our selected binding is supported by the IDP
    logger.debug(f'Trying binding {SPID_DEFAULT_BINDING} for IDP {selected_idp}')
    supported_bindings = get_idp_sso_supported_bindings(selected_idp, config=conf)
    if SPID_DEFAULT_BINDING not in supported_bindings:
        _msg = (
            f"Requested: {SPID_DEFAULT_BINDING} but the selected "
            f"IDP [{selected_idp}] doesn't support "
            f"{BINDING_HTTP_POST} or {BINDING_HTTP_REDIRECT}. "
            f"Check if IdP Metadata is correctly loaded and updated."
        )
        logger.error(_msg)
        raise UnsupportedBinding(_msg)

    # SPID things here
    try:
        login_response = spid_sp_authn_request(conf, selected_idp, next_url)
    except UnknownSystemEntity as e:  # pragma: no cover
        _msg = f'Unknown IDP Entity ID: {selected_idp}'
        logger.error(f'{_msg}: {e}')
        return HttpResponseNotFound(_msg)

    session_id = login_response['session_id']
    http_response = login_response['http_response']

    # success, so save the session ID and return our response
    logger.debug(f'Saving session-id {session_id} in the OutstandingQueries cache')
    oq_cache = OutstandingQueriesCache(request.saml_session)
    oq_cache.set(session_id, next_url)

    if SPID_DEFAULT_BINDING == saml2.BINDING_HTTP_POST:
        return HttpResponse(http_response['data'])
    elif SPID_DEFAULT_BINDING == saml2.BINDING_HTTP_REDIRECT:
        headers = dict(login_response['http_response']['headers'])
        return HttpResponseRedirect(headers['Location'])


@login_required
def spid_logout(request, config_loader_path=None, **kwargs):
    """SAML Logout Request initiator

    This view initiates the SAML2 Logout request
    using the pysaml2 library to create the LogoutRequest.
    """
    state = StateCache(request.saml_session)
    conf = get_config(config_loader_path, request)
    client = Saml2Client(
        conf,
        state_cache=state,
        identity_cache=IdentityCache(request.saml_session)
    )

    # whatever happens, however, the user will be logged out of this sp
    auth.logout(request)
    state.sync()

    subject_id = djangosaml2_views._get_subject_id(request.saml_session)
    if subject_id is None:
        logger.warning(f'The session does not contain the subject id for user {request.user}')
        logger.error("Looks like the user %s is not logged in any IdP/AA", subject_id)
        return HttpResponseBadRequest("You are not logged in any IdP/AA")

    slo_req = saml2.samlp.LogoutRequest()

    slo_req.destination = subject_id.name_qualifier
    # spid-testenv2 preleva l'attribute consumer service dalla authnRequest (anche se questo sta già nei metadati...)
    slo_req.attribute_consuming_service_index = "0"

    issuer = saml2.saml.Issuer()
    issuer.name_qualifier = client.config.entityid
    issuer.text = client.config.entityid
    issuer.format = "urn:oasis:names:tc:SAML:2.0:nameid-format:entity"
    slo_req.issuer = issuer

    # message id
    slo_req.id = saml2.s_utils.sid()
    slo_req.version = saml2.VERSION  # "2.0"
    slo_req.issue_instant = saml2.time_util.instant()

    # oggetto
    slo_req.name_id = subject_id

    try:
        session_info = client.users.get_info_from(
            slo_req.name_id,
            subject_id.name_qualifier,
            False
        )
    except KeyError as e:
        logger.error(f'SPID Logout error: {e}')
        return HttpResponseRedirect('/')

    session_indexes = [session_info['session_index']]

    # aggiungere session index
    if session_indexes:
        sis = []
        for si in session_indexes:
            if isinstance(si, saml2.samlp.SessionIndex):
                sis.append(si)
            else:
                sis.append(saml2.samlp.SessionIndex(text=si))
        slo_req.session_index = sis

    slo_req.protocol_binding = SPID_DEFAULT_BINDING

    assertion_consumer_service_url = client.config._sp_endpoints['assertion_consumer_service'][settings.SPID_CURRENT_INDEX][0]
    slo_req.assertion_consumer_service_url = assertion_consumer_service_url

    slo_req_signed = client.sign(
        slo_req,
        sign_prepare=False,
        sign_alg=settings.SPID_SIG_ALG,
        digest_alg=settings.SPID_DIG_ALG
    )

    _req_str = slo_req_signed
    logger.debug(f'LogoutRequest to {subject_id.name_qualifier}: {repr_saml(_req_str)}')

    slo_location = client.metadata.single_logout_service(
        subject_id.name_qualifier,
        SPID_DEFAULT_BINDING,
        "idpsso"
    )[0]['location']

    if not slo_location:
        error_message = f'Unable to know SLO endpoint in {subject_id.name_qualifier}'
        logger.error(error_message)
        return HttpResponse(error_message)

    http_info = client.apply_binding(
        SPID_DEFAULT_BINDING,
        _req_str,
        slo_location,
        sign=True,
        sigalg=settings.SPID_SIG_ALG
    )
    state.sync()
    return HttpResponse(http_info['data'])


def spid_sp_metadata(conf):
    """

    """
    from saml2.saml import NAME_FORMAT_BASIC
    from saml2.md import AttributeConsumingService, AssertionConsumerService, EntityDescriptor, RequestedAttribute, \
        ServiceDescription, ServiceName, SPSSODescriptor
    from django.conf import settings

    metadata: EntityDescriptor = entity_descriptor(conf)
    _spsso_descriptor: SPSSODescriptor = metadata.spsso_descriptor

    # this will renumber acs starting from 0 and set index=0 as is_default
    for (cnt, assertion_consumer_service) in enumerate(
            _spsso_descriptor.assertion_consumer_service):  # type: int, AssertionConsumerService
        assertion_consumer_service.is_default = 'true' if 0 == cnt else 'false'
        assertion_consumer_service.index = str(cnt)

        if cnt == 0:
            _attribute_consuming_service: AttributeConsumingService = _spsso_descriptor.attribute_consuming_service[cnt]
            _attribute_consuming_service.index = str(cnt)
        else:
            _attribute_consuming_service: AttributeConsumingService = AttributeConsumingService(index=str(cnt))
            _spsso_descriptor.attribute_consuming_service.append(_attribute_consuming_service)

        _attribute_consuming_service.service_name = list()
        _attribute_consuming_service.service_description = list()

        _attributes = settings.SAML_ATTRIBUTE_CONSUMING_SERVICE_LIST[cnt]

        for item in _attributes.get("serviceNames"):
            _attribute_consuming_service.service_name.append(ServiceName(**item))

        for item in _attributes.get("serviceDescriptions"):
            _attribute_consuming_service.service_description.append(ServiceDescription(**item))

        # _attribute_consuming_service.requested_attribute = list(
        #    RequestedAttribute(name=_name, name_format=NAME_FORMAT_BASIC, is_required="true") for _name in
        #    _attributes.get("attributes"))

        _attribute_consuming_service.requested_attribute = list(
            RequestedAttribute(name=_name, name_format=NAME_FORMAT_BASIC) for _name in _attributes.get("attributes"))

    metadata.extensions = None

    # attribute consuming service service name patch
    service_name = metadata.spsso_descriptor.attribute_consuming_service[0].service_name[0]
    service_name.lang = 'it'
    service_name.text = conf._sp_name

    avviso_29_v3(metadata)

    # metadata signature
    secc = security_context(conf)
    sign_dig_algs = dict(
        sign_alg=conf._sp_signing_algorithm,
        digest_alg=conf._sp_digest_algorithm
    )
    eid, xmldoc = sign_entity_descriptor(metadata, None, secc, **sign_dig_algs)
    return xmldoc


def avviso_29_v3(metadata):
    "https://www.agid.gov.it/sites/default/files/repository_files/spid-avviso-n29v3-specifiche_sp_pubblici_e_privati_0.pdf"

    saml2.md.SamlBase.register_prefix(settings.SPID_PREFIXES)

    contact_map = settings.SPID_CONTACTS
    metadata.contact_person = []
    for contact in contact_map:
        spid_contact = saml2.md.ContactPerson()
        spid_contact.contact_type = contact['contact_type']
        contact_kwargs = {
            'email_address': [contact['email_address']],
            'telephone_number': [contact['telephone_number']]
        }
        if contact['contact_type'] == 'other':
            spid_contact.loadd(contact_kwargs)
            contact_kwargs['contact_type'] = contact['contact_type']
            spid_extensions = saml2.ExtensionElement(
                'Extensions',
                namespace='urn:oasis:names:tc:SAML:2.0:metadata'
            )
            for k, v in contact.items():
                if k in contact_kwargs:
                    continue
                ext = saml2.ExtensionElement(
                    k,
                    namespace=settings.SPID_PREFIXES['spid'],
                    text=v
                )
                spid_extensions.children.append(ext)

        elif contact['contact_type'] == 'billing':
            contact_kwargs['company'] = contact['company']
            spid_contact.loadd(contact_kwargs)
            spid_extensions = saml2.ExtensionElement(
                'Extensions',
                namespace='urn:oasis:names:tc:SAML:2.0:metadata'
            )

            elements = {}
            for k, v in contact.items():
                if k in contact_kwargs:
                    continue
                ext = saml2.ExtensionElement(
                    k,
                    namespace=settings.SPID_PREFIXES['fpa'],
                    text=v
                )
                elements[k] = ext

            # DatiAnagrafici
            IdFiscaleIVA = saml2.ExtensionElement(
                'IdFiscaleIVA',
                namespace=settings.SPID_PREFIXES['fpa'],
            )
            Anagrafica = saml2.ExtensionElement(
                'Anagrafica',
                namespace=settings.SPID_PREFIXES['fpa'],
            )
            Anagrafica.children.append(elements['Denominazione'])

            IdFiscaleIVA.children.append(elements['IdPaese'])
            IdFiscaleIVA.children.append(elements['IdCodice'])
            DatiAnagrafici = saml2.ExtensionElement(
                'DatiAnagrafici',
                namespace=settings.SPID_PREFIXES['fpa'],
            )
            if elements.get('CodiceFiscale'):
                DatiAnagrafici.children.append(elements['CodiceFiscale'])
            DatiAnagrafici.children.append(IdFiscaleIVA)
            DatiAnagrafici.children.append(Anagrafica)
            CessionarioCommittente = saml2.ExtensionElement(
                'CessionarioCommittente',
                namespace=settings.SPID_PREFIXES['fpa'],
            )
            CessionarioCommittente.children.append(DatiAnagrafici)

            # Sede
            Sede = saml2.ExtensionElement(
                'Sede',
                namespace=settings.SPID_PREFIXES['fpa'],
            )
            Sede.children.append(elements['Indirizzo'])
            Sede.children.append(elements['NumeroCivico'])
            Sede.children.append(elements['CAP'])
            Sede.children.append(elements['Comune'])
            Sede.children.append(elements['Provincia'])
            Sede.children.append(elements['Nazione'])
            CessionarioCommittente.children.append(Sede)

            spid_extensions.children.append(CessionarioCommittente)

        spid_contact.extensions = spid_extensions
        metadata.contact_person.append(spid_contact)


def metadata_spid(request, config_loader_path=None, valid_for=None):
    """Returns an XML with the SAML 2.0 metadata for this
    SP as configured in the settings.py file.
    """
    conf = get_config(config_loader_path, request)
    xmldoc = spid_sp_metadata(conf)
    return HttpResponse(content=str(xmldoc).encode('utf-8'), content_type="text/xml; charset=utf8")


class EchoAttributesView(LoginRequiredMixin, djangosaml2_views.SPConfigMixin, djangosaml2_views.View):
    """Example view that echo the SAML attributes of an user"""

    def get(self, request, *args, **kwargs):
        state, client = self.get_state_client(request)

        subject_id = djangosaml2_views._get_subject_id(request.saml_session)
        try:
            identity = client.users.get_identity(subject_id, check_not_on_or_after=False)
        except AttributeError:
            return HttpResponse(
                "No active SAML identity found. "
                "Are you sure you have logged in via SAML?"
            )

        return render(
            request,
            'spid_echo_attributes.html',
            {'attributes': identity[0]}
        )


class AssertionConsumerServiceView(djangosaml2_views.AssertionConsumerServiceView):
    def handle_acs_failure(self, request, exception=None, status=403, **kwargs):
        return render(
            request,
            'spid_login_error.html', {
                'exception': exception,
                'spid_anomaly': SpidAnomaly.from_saml2_exception(exception)
            },
            status=status
        )


class LogoutView(djangosaml2_views.LogoutView):
    pass