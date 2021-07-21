from xml.etree import ElementTree

import saml2
import saml2.md
from django.conf import settings
from saml2.metadata import entity_descriptor, sign_entity_descriptor
from saml2.sigver import security_context


def italian_sp_metadata(conf, md_type: str = "spid"):
    metadata = entity_descriptor(conf)

    # this will renumber acs starting from 0 and set index=0 as is_default
    cnt = 0
    for (
        attribute_consuming_service
    ) in metadata.spsso_descriptor.attribute_consuming_service:
        attribute_consuming_service.index = str(cnt)
        cnt += 1

    cnt = 0
    for (
        assertion_consumer_service
    ) in metadata.spsso_descriptor.assertion_consumer_service:
        assertion_consumer_service.is_default = "true" if not cnt else ""
        assertion_consumer_service.index = str(cnt)
        cnt += 1

    # nameformat patch
    for reqattr in metadata.spsso_descriptor.attribute_consuming_service[
        0
    ].requested_attribute:
        reqattr.name_format = (
            None  # "urn:oasis:names:tc:SAML:2.0:attrname-format:basic"
        )
        reqattr.friendly_name = None

    metadata.extensions = None

    # attribute consuming service service name patch
    service_name = metadata.spsso_descriptor.attribute_consuming_service[
        0
    ].service_name[0]
    service_name.lang = "it"
    service_name.text = conf._sp_name

    if md_type == 'spid':
        spid_contacts_29_v3(metadata)
    elif md_type == 'cie':
        cie_contacts(metadata)

    # metadata signature
    secc = security_context(conf)
    sign_dig_algs = dict(
        sign_alg=conf._sp_signing_algorithm, digest_alg=conf._sp_digest_algorithm
    )
    eid, xmldoc = sign_entity_descriptor(metadata, None, secc, **sign_dig_algs)
    return xmldoc


def spid_contacts_29_v3(metadata):
    """
    https://www.agid.gov.it/sites/default/files/repository_files/spid-avviso-n29v3-specifiche_sp_pubblici_e_privati_0.pdf
    """

    for prefix, uri in settings.SPID_PREFIXES.items():
        ElementTree.register_namespace(prefix, uri)

    contact_map = settings.SPID_CONTACTS
    metadata.contact_person = []
    for contact in contact_map:
        spid_contact = saml2.md.ContactPerson()
        spid_contact.contact_type = contact["contact_type"]
        contact_kwargs = {
            "email_address": [contact["email_address"]],
            "telephone_number": [contact["telephone_number"]],
        }
        spid_extensions = saml2.ExtensionElement(
            "Extensions", namespace="urn:oasis:names:tc:SAML:2.0:metadata"
        )

        if contact["contact_type"] == "other":
            spid_contact.loadd(contact_kwargs)
            contact_kwargs["contact_type"] = contact["contact_type"]
            for k, v in contact.items():
                if k in contact_kwargs:
                    continue
                ext = saml2.ExtensionElement(
                    k, namespace=settings.SPID_PREFIXES["spid"], text=v
                )
                # Avviso SPID n. 19 v.4 per enti AGGREGATORI il tag ContactPerson deve
                # avere l’attributo spid:entityType valorizzato come spid:aggregator
                if k == "PublicServicesFullOperator":
                    spid_contact.extension_attributes = {
                        "spid:entityType": "spid:aggregator"
                    }

                spid_extensions.children.append(ext)

        elif contact["contact_type"] == "billing":
            contact_kwargs["company"] = contact["company"]
            spid_contact.loadd(contact_kwargs)

            elements = {}
            for k, v in contact.items():
                if k in contact_kwargs:
                    continue
                ext = saml2.ExtensionElement(
                    k, namespace=settings.SPID_PREFIXES["fpa"], text=v
                )
                elements[k] = ext

            # DatiAnagrafici
            IdFiscaleIVA = saml2.ExtensionElement(
                "IdFiscaleIVA",
                namespace=settings.SPID_PREFIXES["fpa"],
            )
            Anagrafica = saml2.ExtensionElement(
                "Anagrafica",
                namespace=settings.SPID_PREFIXES["fpa"],
            )
            Anagrafica.children.append(elements["Denominazione"])

            IdFiscaleIVA.children.append(elements["IdPaese"])
            IdFiscaleIVA.children.append(elements["IdCodice"])
            DatiAnagrafici = saml2.ExtensionElement(
                "DatiAnagrafici",
                namespace=settings.SPID_PREFIXES["fpa"],
            )
            if elements.get("CodiceFiscale"):
                DatiAnagrafici.children.append(elements["CodiceFiscale"])
            DatiAnagrafici.children.append(IdFiscaleIVA)
            DatiAnagrafici.children.append(Anagrafica)
            CessionarioCommittente = saml2.ExtensionElement(
                "CessionarioCommittente",
                namespace=settings.SPID_PREFIXES["fpa"],
            )
            CessionarioCommittente.children.append(DatiAnagrafici)

            # Sede
            Sede = saml2.ExtensionElement(
                "Sede",
                namespace=settings.SPID_PREFIXES["fpa"],
            )
            Sede.children.append(elements["Indirizzo"])
            Sede.children.append(elements["NumeroCivico"])
            Sede.children.append(elements["CAP"])
            Sede.children.append(elements["Comune"])
            Sede.children.append(elements["Provincia"])
            Sede.children.append(elements["Nazione"])
            CessionarioCommittente.children.append(Sede)

            spid_extensions.children.append(CessionarioCommittente)

        spid_contact.extensions = spid_extensions
        metadata.contact_person.append(spid_contact)


def cie_contacts(metadata):
    """
    """

    for prefix, uri in settings.CIE_PREFIXES.items():
        ElementTree.register_namespace(prefix, uri)

    contact_map = settings.CIE_CONTACTS
    metadata.contact_person = []
    for contact in contact_map:
        cie_contact = saml2.md.ContactPerson()
        cie_contact.contact_type = contact["contact_type"]
        contact_kwargs = {
            "email_address": [contact["email_address"]],
            "telephone_number": [contact["telephone_number"]],
        }
        cie_extensions = saml2.ExtensionElement(
            "Extensions", namespace="urn:oasis:names:tc:SAML:2.0:metadata"
        )

        if contact["contact_type"] == "administrative":
            cie_contact.loadd(contact_kwargs)
            contact_kwargs["contact_type"] = contact["contact_type"]
            for k, v in contact.items():
                if k in contact_kwargs:
                    continue
                ext = saml2.ExtensionElement(
                    k, namespace=settings.CIE_PREFIXES["cie"], text=v
                )
                cie_extensions.children.append(ext)

        elif contact["contact_type"] == "technical":
            cie_contact.loadd(contact_kwargs)
            contact_kwargs["contact_type"] = contact["contact_type"]
            elements = {}
            for k, v in contact.items():
                if k in contact_kwargs:
                    continue
                ext = saml2.ExtensionElement(
                    k, namespace=settings.CIE_PREFIXES["cie"], text=v
                )
                elements[k] = ext

        cie_contact.extensions = cie_extensions
        metadata.contact_person.append(cie_contact)
