Introduzione
============

Questo documento descrive un plugin che permette di attivare l'autenticazione SPID su un sito web realizzato
con il framework Django.

SPID è basato sul framework SAML (Security Assertion Markup Language), sviluppato e manutenuto dal
`Security Services Technical Committee di OASIS <https://www.oasis-open.org/committees/tc_home.php?wg_abbrev=security>`_,
che permette la realizzazione di un sistema sicuro di Single Sign On (SSO) federato, ovvero, che
permette ad un utente di accedere ad una moltitudine di servizi, anche su domini differenti, effettuando
un solo accesso.

Il sistema è composto da 3 entità:

* **Gestore delle identità (Identity Provider o IdP)** che gestisce gli utenti e la procedura di autenticazione;
* **Fornitore di servizi (Service Provider o SP)** che, dopo aver richiesto l'autenticazione dell'utente all'Identity
  Provider, gestisce l'autorizzazione, sulla base degli attributi restituiti dall'IdP, erogando il servizio richiesto;
* **Gestore di attributi qualificati (Attribute Authority o AA)** che fornisce attributi certificati sulla base dell'utente autenticato.

Il plugin descritto in questo documento è dedicato all'implementazione di entità Service Provider.

Per una descrizione esaustiva del protocollo SAML e di SPID fare riferimento alle
`Regole tecniche pubblicate da AGID <https://spid-regole-tecniche.readthedocs.io/en/latest/introduzione.html>`_.

