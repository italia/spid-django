Disclaimer
==========

Siamo a pochi minuti dalla PR:

Il progetto django-spid, è ovviamente in versione 0.1, si riassumono
per praticità in questo spazio i risultati raggiunti:

* Documentazione del plugin con tema integrato Italia `sphinx_italia_theme` con hook da Github -> ReadTheDocs: http://spid-django-plugin-documentation.readthedocs.io
* La Django app django-spid (nel repo spid-django) contenitore per implementazioni specifiche di SAML SP per SPID https://github.com/pdpfsug/spid-django/
* Il fork della app django `django-saml2-auth` per consentire il supporto di IDP multipli https://github.com/pdpfsug/django-saml2-auth

* Un mockup di una API REST per il recupero delle informazioni degli IDP (metadata, logo, cert, attributes_map) https://idpapi.azurewebsites.net/api/IdentityProviders ospitata su VM MS Azure
* Un servizio (implementato in django-spid, runserver di Django) attivo su hackamerino.labs.befair.it su VM MS Azure comprende:
  * integrazione bottone ufficiale SPID http://hackamerino.labs.befair.it/
  * prova URL di autenticazione presso un IDP http://hackamerino.labs.befair.it/accounts/login/?idp_metadata=https://idp.spid.gov.it:9443/samlsso
  * un modello per il salvataggio delle info degli IdP (ma se si va avanti con la API REST dedicata mi sembra meglio)
* Un progetto su RH OpenShift http://spid-django-pdp-spid-django.apps.justcodeon.it/saml2_auth/ abbozzato per il continuous delivery

insomma, il codice è qui, le configurazioni di GitHub ovviamente rimangono sul nostro repo...
