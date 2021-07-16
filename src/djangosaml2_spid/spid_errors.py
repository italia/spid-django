import re
from saml2 import SAMLError
from saml2.response import StatusAuthnFailed

#
# Messaggi di Errore SPID
#
# Ref: https://docs.italia.it/italia/spid/spid-regole-tecniche/it/stabile/messaggi-errore.html
#
SPID_ERRORS = {
    # Autenticazione corretta
    1: {
        "description": "Autenticazione corretta",
    },
    # Anomalie del sistema
    2: {
        "description": "Indisponibilità sistema",
    },
    3: {
        "description": "Errore di sistema",
    },
    # Anomalie delle richieste
    4: {
        "description": "Formato binding non corretto",
    },
    5: {
        "description": "Verifica della firma fallita",
    },
    6: {
        "description": "Binding su metodo HTTP errato",
    },
    7: {
        "description": "Errore sulla verifica della firma della richiesta",
    },
    8: {
        "description": "Formato della richiesta non conforme alle specifiche SAML",
    },
    9: {
        "description": "Parametro version non presente, malformato o diverso da 2.0",
    },
    10: {
        "description": "Issuer non presente, malformato o non corrispondete "
        "all'entità che sottoscrive la richiesta",
    },
    11: {
        "description": "ID non presente, malformato o non conforme",
    },
    12: {
        "description": "RequestAuthnContext non presente, malformato o non previsto da SPID",
    },
    13: {
        "description": "IssueInstant non presente, malformato o non coerente con l'orario di arrivo della richiesta",
    },
    14: {
        "description": "Destination non presente, malformata o non coincidente "
        "con il Gestore delle identità ricevente la richiesta",
    },
    15: {
        "description": "Attributo IsPassive presente e attualizzato al valore true",
    },
    16: {
        "description": "AssertionConsumerService non correttamente valorizzato",
    },
    17: {
        "description": "Attributo Format dell'elemento NameIDPolicy assente o "
        "non valorizzato secondo specifica",
    },
    18: {
        "description": "AttributeConsumerServiceIndex malformato o che riferisce "
        "a un valore non registrato nei metadati di SP",
    },
    # Anomalie derivanti dall’utente
    19: {
        "description": "Autenticazione fallita per ripetuta sottomissione di credenziali errate - "
        "superato numero tentativi secondo le policy adottate",
        "message": "Autenticazione fallita per ripetuta sottomissione di credenziali errate",
        "troubleshoot": "Inserire credenziali corrette",
    },
    20: {
        "description": "Utente privo di credenziali compatibili con il livello HTTP "
        "richiesto dal fornitore del servizio",
        "message": "Utente privo di credenziali compatibili con "
        "il livello di autenticazione richiesto",
        "troubleshoot": "Acquisire credenziali di livello idoneo all'accesso al servizio",
    },
    21: {
        "description": "Timeout durante l'autenticazione utente",
        "message": "Timeout durante l'autenticazione utente",
        "troubleshoot": "Si ricorda che l'operazione di autenticazione deve "
        "essere completata entro un determinato periodo di tempo",
    },
    22: {
        "description": "Utente nega il consenso all'invio di dati al SP in caso di sessione vigente",
        "message": "L'utente nega il consenso all'invio di dati al fornitore del servizio",
        "troubleshoot": "È necessario dare il consenso per poter accedere al servizio",
    },
    23: {
        "description": "Utente con identità sospesa/revocata o con credenziali bloccate",
        "message": "Utente con identità sospesa/revocata o con credenziali bloccate",
    },
    25: {
        "description": "Processo di autenticazione annullato dall'utente",
        "message": "Processo di autenticazione annullato dall'utente",
    },
    30: {
        # TODO: controllare conformità quando sarà emessa una tabella errori SPID aggiornata
        "description": "L'identità digitale utilizzata non è di tipo professionale",
        "message": "L'identità digitale utilizzata non è un'identità digitale del tipo atteso",
        "troubleshoot": "È necessario eseguire l'autenticazione con le credenziali "
        "del corretto tipo di identità digitale richiesto",
    },
}


class SpidError(SAMLError):

    _error_code_regexp = re.compile(r"ErrorCode nr(\d+)")

    def __init__(self, code: int):
        try:
            error_data = SPID_ERRORS[code]
        except KeyError:
            exception_class = ValueError if isinstance(code, int) else TypeError
            raise exception_class(f"{code!r} is not a SPID error code") from None

        self.code = code
        self.status_message = f"ErrorCode nr{self.code}"
        self.description = error_data.get("description", "")
        self.message = error_data.get("message", "Accesso negato")
        self.troubleshoot = error_data.get("troubleshoot", "")

    @classmethod
    def from_error(cls, error):
        if isinstance(error, cls):
            return error

        match = cls._error_code_regexp.search(str(error))
        if match is None:
            exception_class = (
                ValueError if isinstance(error, (str, Exception)) else TypeError
            )
            raise exception_class(
                f"cannot create a {cls.__name__} instance from {error!r}"
            )

        return cls(int(match.group(1)))

    @classmethod
    def from_saml2_error(cls, error):
        if not isinstance(error, (StatusAuthnFailed, cls)):
            raise TypeError(f"{error!r} is not a SAML2 authentication error")
        return cls.from_error(error)

    def __repr__(self):
        return "%s(code=%r)" % (self.__class__.__name__, self.code)

    def __str__(self):
        if self.troubleshoot:
            return "{}\n\n{}".format(self.message, self.troubleshoot)
        return self.message
