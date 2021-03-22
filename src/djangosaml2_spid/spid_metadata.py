import saml2
from django.conf import settings
from saml2.metadata import entity_descriptor, sign_entity_descriptor
from saml2.sigver import security_context
import logging

logger = logging.getLogger(__name__)


def spid_sp_metadata(conf):
    from saml2.saml import NAME_FORMAT_BASIC
    from saml2.md import AttributeConsumingService, AssertionConsumerService, EntityDescriptor, RequestedAttribute, \
        ServiceDescription, ServiceName, SPSSODescriptor
    from django.conf import settings

    metadata: EntityDescriptor = entity_descriptor(conf)
    _spsso_descriptor: SPSSODescriptor = metadata.spsso_descriptor

    # this will renumber acs starting from 0 and set index=0 as is_default
    _n_assertion_consumer_service: int = len(_spsso_descriptor.assertion_consumer_service)
    _check: bool = _n_assertion_consumer_service > settings.SPID_CURRENT_INDEX
    if _check is False:
        message: str = f"Number of assertion_consumer_service: {_n_assertion_consumer_service}." \
                       f" Expected at least {_n_assertion_consumer_service + 1} "
        logger.error(message)
        raise Exception(message)

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

        # with is_required attribute
        # _attribute_consuming_service.requested_attribute = list(
        #    RequestedAttribute(name=_name, is_required="true") for _name in
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
    """
    https://www.agid.gov.it/sites/default/files/repository_files/spid-avviso-n29v3-specifiche_sp_pubblici_e_privati_0.pdf
    """

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
        spid_extensions = saml2.ExtensionElement(
            'Extensions',
            namespace='urn:oasis:names:tc:SAML:2.0:metadata'
        )

        if contact['contact_type'] == 'other':
            spid_contact.loadd(contact_kwargs)
            contact_kwargs['contact_type'] = contact['contact_type']
            for k, v in contact.items():
                if k in contact_kwargs:
                    continue
                ext = saml2.ExtensionElement(
                    k,
                    namespace=settings.SPID_PREFIXES['spid'],
                    text=v
                )
                # Avviso SPID n. 19 v.4 per enti AGGREGATORI il tag ContactPerson deve avere l’attributo spid:entityType valorizzato come spid:aggregator
                if k == "PublicServicesFullOperator":
                    spid_contact.extension_attributes= {"spid:entityType": "spid:aggregator"}

                spid_extensions.children.append(ext)

            spid_contact.extensions = spid_extensions

        elif contact['contact_type'] == 'billing':
            contact_kwargs['company'] = contact['company']
            spid_contact.loadd(contact_kwargs)

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
