import base64
import logging
import random
import saml2
import string

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.dispatch import receiver
from django.http import (HttpResponse, 
                         HttpResponseRedirect, 
                         HttpResponseBadRequest,
                         HttpResponseNotFound)
from django.shortcuts import render
from django.template import TemplateDoesNotExist
from django.urls import reverse
from djangosaml2.conf import get_config
from djangosaml2.cache import IdentityCache, OutstandingQueriesCache
from djangosaml2.cache import StateCache
from djangosaml2.conf import get_config
from djangosaml2.overrides import Saml2Client
from djangosaml2.signals import post_authenticated, pre_user_save
from djangosaml2.utils import (
    available_idps, get_custom_setting,
    get_idp_sso_supported_bindings, get_location,
    validate_referral_url
)
from djangosaml2.views import finish_logout, _get_subject_id
from saml2 import BINDING_HTTP_REDIRECT, BINDING_HTTP_POST
from saml2.authn_context import requested_authn_context
from saml2.mdstore import UnknownSystemEntity
from saml2.metadata import entity_descriptor, sign_entity_descriptor
from saml2.sigver import security_context

from .utils import repr_saml


logger = logging.getLogger('djangosaml2')


def index(request):
    """ Barebone 'diagnostics' view, print user attributes if logged in + login/logout links.
    """
    if request.user.is_authenticated:
        out = "LOGGED IN: <a href={0}>LOGOUT</a><br>".format(settings.LOGOUT_URL)
        out += "".join(['%s: %s</br>' % (field.name, getattr(request.user, field.name))
                    for field in request.user._meta.get_fields()
                    if field.concrete])
        return HttpResponse(out)
    else:
        return HttpResponse("LOGGED OUT: <a href={0}>LOGIN</a>".format(settings.LOGIN_URL))


# @receiver(pre_user_save, sender=User)
# def custom_update_user(sender, instance, attributes, user_modified, **kargs):
    # """ Default behaviour does not play nice with booleans encoded in SAML as u'true'/u'false'.
        # This will convert those attributes to real booleans when saving.
    # """
    # for k, v in attributes.items():
        # u = set.intersection(set(v), set([u'true', u'false']))
        # if u:
            # setattr(instance, k, u.pop() == u'true')
    # return True  # I modified the user object


def spid_sp_authn_request(conf, selected_idp, binding, 
                          name_id_format, authn_context, 
                          sig_alg, dig_alg, next_url=''):
    client = Saml2Client(conf)

    logger.debug(f'Redirecting user to the IdP via {binding} binding.')
    # use the html provided by pysaml2 if no template was specified or it didn't exist
    # SPID want the fqdn of the IDP, not the SSO endpoint
    location_fixed = selected_idp
    location = client.sso_location(selected_idp, binding)

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
    authn_req.version = saml2.VERSION # "2.0"
    authn_req.issue_instant = saml2.time_util.instant()

    name_id_policy = saml2.samlp.NameIDPolicy()
    # del(name_id_policy.allow_create)
    name_id_policy.format = name_id_format # settings.SPID_NAMEID_FORMAT
    authn_req.name_id_policy  = name_id_policy

    # settings.SPID_AUTH_CONTEXT
    authn_context = requested_authn_context(class_ref=authn_context)
    authn_req.requested_authn_context = authn_context

    # force_auth = true only if SpidL >= 2
    # if 'SpidL1' in authn_context.authn_context_class_ref[0].text:
        # force_authn = 'false'
    # else:
    force_authn = 'true'
    authn_req.force_authn = force_authn
    # end force authn
    
    # settings.SPID_DEFAULT_BINDING
    authn_req.protocol_binding = binding

    assertion_consumer_service_url = client.config._sp_endpoints['assertion_consumer_service'][0][0]
    authn_req.assertion_consumer_service_url = assertion_consumer_service_url

    authn_req_signed = client.sign(authn_req, sign_prepare=False,
                                   sign_alg=sig_alg, 
                                   digest_alg=dig_alg,
    )
    logger.debug(f'AuthRequest to {selected_idp}: {authn_req_signed}')
    relay_state = next_url or reverse('djangosaml2:saml2_echo_attributes')
    http_info = client.apply_binding(binding,
                                     authn_req_signed, location,
                                     sign=True,
                                     sigalg=sig_alg,
                                     relay_state = relay_state)
    return dict(http_response = http_info,
                authn_request = authn_req_signed,
                relay_state = relay_state,
                session_id = authn_req.id
    )


def spid_login(request,
          config_loader_path=None,
          wayf_template='wayf.html',
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
        redirect_authenticated_user = getattr(settings,
                                              'SAML_IGNORE_AUTHENTICATED_USERS_ON_LOGIN',
                                              True)
        if redirect_authenticated_user:
            return HttpResponseRedirect(next_url)
        else: # pragma: no cover
            logger.debug('User is already logged in')
            return render(request, authorization_error_template, {
                    'came_from': next_url})
    
    # this works only if request came from wayf
    selected_idp = request.GET.get('idp', None)

    conf = get_config(config_loader_path, request)

    # is a embedded wayf needed?
    idps = available_idps(conf)
    if selected_idp is None and len(idps) > 1:
        logger.debug('A discovery process is needed')
        return render(request, wayf_template, 
            {
                'available_idps': idps.items(),
                'next_url': next_url
            }
        )
    else:
        # otherwise is the first one
        _msg = 'Unable to know which IdP to use'
        try:
            selected_idp = selected_idp or list(idps.keys())[0]
        except TypeError as e: # pragma: no cover
            logger.error(f'{_msg}: {e}')
            return HttpResponseError(_msg)
        except IndexError as e: # pragma: no cover
            logger.error(f'{_msg}: {e}')
            return HttpResponseNotFound(_msg)
        
    binding = BINDING_HTTP_POST
    logger.debug(f'Trying binding {binding} for IDP {selected_idp}')

    # ensure our selected binding is supported by the IDP
    supported_bindings = get_idp_sso_supported_bindings(selected_idp, config=conf)
    if binding != BINDING_HTTP_POST:
            raise UnsupportedBinding('IDP %s does not support %s or %s',
                                     selected_idp, BINDING_HTTP_POST, BINDING_HTTP_REDIRECT)
    
    # SPID things here
    try:
        login_response = spid_sp_authn_request(conf, 
                                               selected_idp, 
                                               binding, 
                                               settings.SPID_NAMEID_FORMAT,
                                               settings.SPID_AUTH_CONTEXT,
                                               settings.SPID_SIG_ALG,
                                               settings.SPID_DIG_ALG,
                                               next_url
        )
    except UnknownSystemEntity as e: # pragma: no cover
        _msg = f'Unknown IDP Entity ID: {selected_idp}'
        logger.error(f'{_msg}: {e}')
        return HttpResponseNotFound(_msg)
    
    session_id = login_response['session_id']
    http_response = login_response['http_response']
    
    # success, so save the session ID and return our response
    logger.debug(f'Saving session-id {session_id} in the OutstandingQueries cache')
    oq_cache = OutstandingQueriesCache(request.saml_session)
    oq_cache.set(session_id, next_url)
    return HttpResponse(http_response['data'])


@login_required
def spid_logout(request, config_loader_path=None, **kwargs):
    """SAML Logout Request initiator

    This view initiates the SAML2 Logout request
    using the pysaml2 library to create the LogoutRequest.
    """
    state = StateCache(request.saml_session)
    conf = get_config(config_loader_path, request)
    client = Saml2Client(conf, state_cache=state,
                         identity_cache=IdentityCache(request.saml_session))
    
    # whatever happens, however, the user will be logged out of this sp
    auth.logout(request)
    state.sync()
    
    subject_id = _get_subject_id(request.saml_session)
    if subject_id is None:
        logger.warning(
            'The session does not contain the subject id for user %s',
            request.user)
        logger.error("Looks like the user %s is not logged in any IdP/AA", subject_id)
        return HttpResponseBadRequest("You are not logged in any IdP/AA")
    
    slo_req = saml2.samlp.LogoutRequest()

    binding = settings.SPID_DEFAULT_BINDING
    location_fixed = subject_id.name_qualifier
    location = location_fixed
    slo_req.destination = location_fixed
    # spid-testenv2 preleva l'attribute consumer service dalla authnRequest (anche se questo sta già nei metadati...)
    slo_req.attribute_consuming_service_index = "0"

    issuer = saml2.saml.Issuer()
    issuer.name_qualifier = client.config.entityid
    issuer.text = client.config.entityid
    issuer.format = "urn:oasis:names:tc:SAML:2.0:nameid-format:entity"
    slo_req.issuer = issuer

    # message id
    slo_req.id = saml2.s_utils.sid()
    slo_req.version = saml2.VERSION # "2.0"
    slo_req.issue_instant = saml2.time_util.instant()

    # oggetto
    slo_req.name_id = subject_id
    
    try:
        session_info = client.users.get_info_from(slo_req.name_id,
                                                  subject_id.name_qualifier,
                                                  False)
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

    slo_req.protocol_binding = binding

    assertion_consumer_service_url = client.config._sp_endpoints['assertion_consumer_service'][0][0]
    slo_req.assertion_consumer_service_url = assertion_consumer_service_url

    slo_req_signed = client.sign(slo_req, sign_prepare=False,
                                 sign_alg=settings.SPID_SIG_ALG,
                                 digest_alg=settings.SPID_DIG_ALG)
    session_id = slo_req.id

    _req_str = slo_req_signed
    logger.debug('LogoutRequest to {}: {}'.format(subject_id.name_qualifier,
                                                  repr_saml(_req_str)))

    # get slo from metadata
    slo_location = None
    # for k,v in client.metadata.metadata.items():
        # idp_nq = v.entity.get(subject_id.name_qualifier)
        # if idp_nq:
            # slo_location = idp_nq['idpsso_descriptor'][0]['single_logout_service'][0]['location']

    slo_location = client.metadata.single_logout_service(subject_id.name_qualifier,
                                                         binding,
                                                         "idpsso")[0]['location']
    if not slo_location:
        logger.error('Unable to know SLO endpoint in {}'.format(subject_id.name_qualifier))
        return HttpResponse(text_type(e))
    
    http_info = client.apply_binding(binding,
                                     _req_str,
                                     slo_location,
                                     sign=True,
                                     sigalg=settings.SPID_SIG_ALG
    )
    state.sync()
    return HttpResponse(http_info['data'])


def spid_sp_metadata(conf):
    metadata = entity_descriptor(conf)

    # this will renumber acs starting from 0 and set index=0 as is_default
    cnt = 0
    for attribute_consuming_service in metadata.spsso_descriptor.attribute_consuming_service:
        attribute_consuming_service.index = str(cnt)
        cnt += 1

    cnt = 0
    for assertion_consumer_service in metadata.spsso_descriptor.assertion_consumer_service:
        assertion_consumer_service.is_default = 'true' if not cnt else ''
        assertion_consumer_service.index = str(cnt)
        cnt += 1

    # nameformat patch... non proprio standard
    for reqattr in metadata.spsso_descriptor.attribute_consuming_service[0].requested_attribute:
        reqattr.name_format = None #"urn:oasis:names:tc:SAML:2.0:attrname-format:basic"
        # reqattr.is_required = None
        reqattr.friendly_name = None

    # remove unecessary encryption and digest algs
    # supported_algs = ['http://www.w3.org/2009/xmldsig11#dsa-sha256',
    #                   'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256']
    # new_list = []
    # for alg in metadata.extensions.extension_elements:
        # if alg.attributes.get('Algorithm') in supported_algs:
            # new_list.append(alg)
    # metadata.extensions.extension_elements = new_list
    
    # ... Piuttosto non devo specificare gli algoritmi di firma/criptazione...
    metadata.extensions = None

    # attribute consuming service service name patch
    service_name = metadata.spsso_descriptor.attribute_consuming_service[0].service_name[0]
    service_name.lang = 'it'
    service_name.text = conf._sp_name
    
    ##############
    # avviso 29 v3
    #
    # https://www.agid.gov.it/sites/default/files/repository_files/spid-avviso-n29v3-specifiche_sp_pubblici_e_privati_0.pdf
    saml2.md.SamlBase.register_prefix(settings.SPID_PREFIXES)
    
    contact_map = settings.SPID_CONTACTS
    cnt = 0
    metadata.contact_person = []
    for contact in contact_map:
        spid_contact = saml2.md.ContactPerson()
        spid_contact.contact_type = contact['contact_type']
        contact_kwargs = {
            'email_address' : [contact['email_address']],
            'telephone_number' : [contact['telephone_number']]
        }
        if contact['contact_type'] == 'other':
            spid_contact.loadd(contact_kwargs)
            contact_kwargs['contact_type'] = contact['contact_type']
            spid_extensions = saml2.ExtensionElement(
                'Extensions', 
                namespace='urn:oasis:names:tc:SAML:2.0:metadata'
            )
            for k,v in contact.items():
                if k in contact_kwargs: continue
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
            for k,v in contact.items():
                if k in contact_kwargs: continue
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
        cnt += 1
    #
    # fine avviso 29v3
    ###################
    
    # metadata signature
    secc = security_context(conf)
    sign_dig_algs = dict(sign_alg = conf._sp_signing_algorithm,
                         digest_alg = conf._sp_digest_algorithm)
    eid, xmldoc = sign_entity_descriptor(metadata, None, secc, **sign_dig_algs)
    return xmldoc


def metadata_spid(request, config_loader_path=None, valid_for=None):
    """Returns an XML with the SAML 2.0 metadata for this
    SP as configured in the settings.py file.
    """
    conf = get_config(config_loader_path, request)
    xmldoc = spid_sp_metadata(conf)
    return HttpResponse(content=str(xmldoc).encode('utf-8'),
                        content_type="text/xml; charset=utf8")
