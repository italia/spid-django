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
from saml2.mdstore import UnknownSystemEntity
from saml2.s_utils import UnsupportedBinding
import djangosaml2.views as djangosaml2_views
import logging
import saml2

from .conf import settings
from .spid_anomalies import SpidAnomaly
from .spid_metadata import spid_sp_metadata
from .spid_request import spid_sp_authn_request
from .spid_validator import Saml2ResponseValidator
from .utils import repr_saml


SPID_DEFAULT_BINDING = settings.SPID_DEFAULT_BINDING

logger = logging.getLogger('djangosaml2')


def index(request):
    """
       Barebone 'diagnostics' view, print user attributes
       if logged in + login/logout links.
    """

    if request.user.is_authenticated:
        out = f"LOGGED IN: <a href={settings.LOGOUT_URL}>LOGOUT</a><br>"
        out += "".join([
            f'{field.name}: {getattr(request.user, field.name)}</br>'
            for field in request.user._meta.get_fields()
            if field.concrete]
        )
        return HttpResponse(out)
    else:
        return HttpResponse(
                f"LOGGED OUT: <a href={settings.LOGIN_URL}>LOGIN</a>"
        )


def spid_login(request, config_loader_path=None, wayf_template='wayf.html',
               authorization_error_template='djangosaml2/auth_error.html'):
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
        redirect_authenticated_user = getattr(
                    settings,
                    'SAML_IGNORE_AUTHENTICATED_USERS_ON_LOGIN',
                    True
        )
        if redirect_authenticated_user:
            return HttpResponseRedirect(next_url)
        else:  # pragma: no cover
            logger.debug('User is already logged in')
            return render(
                request,
                authorization_error_template,
                {'came_from': next_url}
            )

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
    logger.debug(
        f'Trying binding {SPID_DEFAULT_BINDING} for IDP {selected_idp}'
    )
    supported_bindings = get_idp_sso_supported_bindings(
                                                selected_idp,
                                                config=conf
                                            )
    if not supported_bindings:
        _msg = 'IdP Metadata not found or not valid'
        return HttpResponseNotFound(_msg)

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
        login_response = spid_sp_authn_request(
                                            conf,
                                            selected_idp,
                                            next_url
                                        )
    except UnknownSystemEntity as e:  # pragma: no cover
        _msg = f'Unknown IDP Entity ID: {selected_idp}'
        logger.error(f'{_msg}: {e}')
        return HttpResponseNotFound(_msg)

    session_id = login_response['session_id']
    http_response = login_response['http_response']

    # success, so save the session ID and return our response
    logger.debug(
        f'Saving session-id {session_id} in the OutstandingQueries cache'
    )
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
        logger.warning(
            f'The session does not contain the subject id for user {request.user}'
        )
        logger.error(
            f"Looks like the user {subject_id} is not logged in any IdP/AA"
        )
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

    assertion_consumer_service_url = client.config._sp_endpoints['assertion_consumer_service'][0][0]
    slo_req.assertion_consumer_service_url = assertion_consumer_service_url

    slo_req_signed = client.sign(
        slo_req,
        sign_prepare=False,
        sign_alg=settings.SPID_SIG_ALG,
        digest_alg=settings.SPID_DIG_ALG
    )

    _req_str = slo_req_signed
    logger.debug(
        f'LogoutRequest to {subject_id.name_qualifier}: {repr_saml(_req_str)}'
    )

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


def metadata_spid(request, config_loader_path=None, valid_for=None):
    """Returns an XML with the SAML 2.0 metadata for this
    SP as configured in the settings.py file.
    """
    conf = get_config(config_loader_path, request)
    xmldoc = spid_sp_metadata(conf)
    return HttpResponse(content=str(xmldoc).encode('utf-8'), content_type="text/xml; charset=utf8")


class EchoAttributesView(LoginRequiredMixin,
                         djangosaml2_views.SPConfigMixin,
                         djangosaml2_views.View):
    """Example view that echo the SAML attributes of an user"""

    def get(self, request, *args, **kwargs):
        state, client = self.get_state_client(request)

        subject_id = djangosaml2_views._get_subject_id(request.saml_session)
        try:
            identity = client.users.get_identity(subject_id,
                                                 check_not_on_or_after=False)
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
    def custom_validation(self, response):
        conf = get_config(None, self.request)

        # Spid and SAML2 additional tests
        accepted_time_diff = conf.accepted_time_diff
        recipient = conf._sp_endpoints['assertion_consumer_service'][0][0]
        authn_context_classref = settings.SPID_AUTH_CONTEXT
        issuer = response.response.issuer
        # in_response_to = todo
        validator = Saml2ResponseValidator(authn_response = response.xmlstr,
                                           recipient = recipient,
                                           # in_response_to = in_response_to,
                                           # requester = requester,
                                           accepted_time_diff = accepted_time_diff,
                                           authn_context_class_ref = authn_context_classref,
                                           return_addrs = response.return_addrs)
        validator.run()


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
