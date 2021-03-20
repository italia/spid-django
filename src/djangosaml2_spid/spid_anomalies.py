import re
import saml2


class SpidAnomaly:
    find_error_code_regexp = re.compile(r'ErrorCode nr(\d+)')

    def __init__(self, *, code, message, troubleshoot=None):
        self.code = code
        self.status_message = f'ErrorCode nr{self.code}'
        self.message = message
        self.troubleshoot = troubleshoot

    @classmethod
    def from_saml2_exception(cls, exception):
        if not isinstance(exception, saml2.response.StatusAuthnFailed):
            return None

        saml2_error_message = exception.args[0]
        codes = set(cls.find_error_code_regexp.findall(saml2_error_message))
        if len(codes) != 1:
            return None

        code = int(codes.pop())
        return spid_anomalies_by_code[code]


spid_anomalies = [
    SpidAnomaly(
        code=19,
        message='Autenticazione fallita per ripetuta sottomissione di credenziali errate',
        troubleshoot='Inserire credenziali corrette'
    ),
    SpidAnomaly(
        code=20,
        message='Utente privo di credenziali compatibili con il livello di autenticazione richiesto',
        troubleshoot='Acquisire credenziali di livello idoneo all\'accesso al servizio'
    ),
    SpidAnomaly(
        code=21,
        message='Timeout durante l\'autenticazione utente',
        troubleshoot='Si ricorda che l\'operazione di autenticazione deve essere completata entro un determinato periodo di tempo'
    ),
    SpidAnomaly(
        code=22,
        message='L\'utente nega il consenso all\'invio di dati al fornitore del servizio',
        troubleshoot='È necessario dare il consenso per poter accedere al servizio'
    ),
    SpidAnomaly(
        code=23,
        message='Utente con identità sospesa/revocata o con credenziali bloccate'
    ),
    SpidAnomaly(
        code=25,
        message='Processo di autenticazione annullato dall\'utente'
    )
]

spid_anomalies_by_code = {anomaly.code: anomaly for anomaly in spid_anomalies}
