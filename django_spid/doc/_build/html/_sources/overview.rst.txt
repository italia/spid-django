Django SPID Plugin
==================

Il plugin SPID per Django si basa sull'applicazione Django 
`django-saml2-auth <https://github.com/fangli/django-saml2-auth>`__

Di tale applicazione è stato fatto un fork su
https://github.com/pdpfsug/django-saml2-auth per consentire il supporto
di multipli IdentityProvider.

Poi è stata creata l'app 
`django-spid <https://github.com/pdpfsug/django-spid>`__
che include le fixtures con i valori degli IdP SPID italiani supportati
dal bottone `SPID SP access button <https://github.com/italia/spid-sp-access-button>`__


Cosa è necessario fare
----------------------

Attestare il proprio SP sugli IdP di cui si vuole supportare l'autenticazione

Per ulteriori opzioni di configurazione vedere il repository github della app.
