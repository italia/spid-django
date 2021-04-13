import re
from saml2 import SAMLError
from saml2.response import StatusAuthnFailed

#
# Messaggi di Errore SPID
#
# Ref: https://docs.italia.it/italia/spid/spid-regole-tecniche/it/stabile/messaggi-errore.html
#
SPID_ANOMALIES = {
    19: {
        'message': 'Autenticazione fallita per ripetuta sottomissione di credenziali errate',
        'troubleshoot': 'Inserire credenziali corrette'
    },
    20: {
        'message': 'Utente privo di credenziali compatibili con '
                   'il livello di autenticazione richiesto',
        'troubleshoot': 'Acquisire credenziali di livello idoneo all\'accesso al servizio',
    },
    21: {
        'message': 'Timeout durante l\'autenticazione utente',
        'troubleshoot': 'Si ricorda che l\'operazione di autenticazione deve '
                        'essere completata entro un determinato periodo di tempo',
    },
    22: {
        'message': 'L\'utente nega il consenso all\'invio di dati al fornitore del servizio',
        'troubleshoot': 'È necessario dare il consenso per poter accedere al servizio',
    },
    23: {
        'message': 'Utente con identità sospesa/revocata o con credenziali bloccate'
    },
    25: {
        'message': 'Processo di autenticazione annullato dall\'utente'
    }
}


class SpidError(SAMLError):
    pass


class SpidAnomaly(SpidError):
    find_error_code_regexp = re.compile(r'ErrorCode nr(\d+)')

    def __init__(self, code: int):
        if not isinstance(code, int) or code < 0 or code > 25:
            raise ValueError(f'{code} non è un codice di messaggio di errore SPID')

        self.code = code
        self.status_message = f'ErrorCode nr{self.code}'

        try:
            self.message = SPID_ANOMALIES[code].get('message')
            self.troubleshoot = SPID_ANOMALIES[code].get('troubleshoot')
        except KeyError:
            self.message = self.troubleshoot = None

    @classmethod
    def from_saml2_exception(cls, exception):
        if not isinstance(exception, StatusAuthnFailed):
            return None

        saml2_error_message = exception.args[0]
        codes = set(cls.find_error_code_regexp.findall(saml2_error_message))
        if len(codes) != 1:
            return None

        code = int(codes.pop())
        return cls(code)

    def __repr__(self):
        return '%s(code=%r)' % (self.__class__.__name__, self.code)

    def __str__(self):
        if not self.message:
            return self.status_message
        elif not self.troubleshoot:
            return self.message
        return '{}\n\n{}'.format(self.message, self.troubleshoot)
