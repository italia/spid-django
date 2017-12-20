# -*- coding: utf-8 -*-
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.logout_response import OneLogin_Saml2_Logout_Response
from onelogin.saml2.constants import OneLogin_Saml2_Constants
from onelogin.saml2.utils import OneLogin_Saml2_Utils, OneLogin_Saml2_Error
from onelogin.saml2.logout_request import OneLogin_Saml2_Logout_Request
from onelogin.saml2.xml_utils import OneLogin_Saml2_XML


class SpidSaml2LogoutResponse(OneLogin_Saml2_Logout_Response):
    """

    This class  handles a Logout Response. It Builds or parses a Logout Response object
    and validates it.

    """

    def __init__(self, settings, response=None, method='redirect'):
        """
        Constructs a Logout Response object (Initialize params from settings
        and if provided load the Logout Response.

        Arguments are:
            * (OneLogin_Saml2_Settings)   settings. Setting data
            * (string)                    response. An UUEncoded SAML Logout
                                                    response from the IdP.
        """
        if method == 'redirect':
            super(SpidSaml2LogoutResponse, self).__init__(settings, response)
        elif method == 'post':
            self.__settings = settings
            self.__error = None
            self.id = None

            if response is not None:
                self.__logout_response = OneLogin_Saml2_Utils.b64decode(response)
                self.document = OneLogin_Saml2_XML.to_etree(self.__logout_response)
                self.id = self.document.get('ID', None)
        else:
            raise ValueError("Wrong value %r for argument 'method'." % method)


class SpidSaml2Auth(OneLogin_Saml2_Auth):

    def process_slo(self, keep_local_session=False, request_id=None, delete_session_cb=None):
        """
        Process the SAML Logout Response / Logout Request sent by the IdP.

        :param keep_local_session: When false will destroy the local session, otherwise will destroy it
        :type keep_local_session: bool

        :param request_id: The ID of the LogoutRequest sent by this SP to the IdP
        :type request_id: string

        :returns: Redirection url
        """
        self.__errors = []
        self.__error_reason = None

        post_data = 'post_data' in self._OneLogin_Saml2_Auth__request_data and self._OneLogin_Saml2_Auth__request_data['post_data']
        get_data = 'get_data' in self._OneLogin_Saml2_Auth__request_data and self._OneLogin_Saml2_Auth__request_data['get_data']
        method = 'redirect'
        if post_data:
            get_data = post_data
            method = 'post'
        elif get_data and 'SAMLResponse' in get_data:
            logout_response = SpidSaml2LogoutResponse(self.__settings, get_data['SAMLResponse'], method)
            self._OneLogin_Saml2_Auth__last_response = logout_response.get_xml()
            if not self.validate_response_signature(get_data):
                self.__errors.append('invalid_logout_response_signature')
                self.__errors.append('Signature validation failed. Logout Response rejected')
            if not logout_response.is_valid(self.__request_data, request_id):
                self.__errors.append('invalid_logout_response')
                self.__error_reason = logout_response.get_error()
            elif logout_response.get_status() != OneLogin_Saml2_Constants.STATUS_SUCCESS:
                self.__errors.append('logout_not_success')
            else:
                self._OneLogin_Saml2_Auth__last_message_id = logout_response.id
                if not keep_local_session:
                    OneLogin_Saml2_Utils.delete_local_session(delete_session_cb)

        elif get_data and 'SAMLRequest' in get_data:
            logout_request = OneLogin_Saml2_Logout_Request(self.__settings, get_data['SAMLRequest'])
            self._OneLogin_Saml2_Auth__last_request = logout_request.get_xml()
            if not self.validate_request_signature(get_data):
                self.__errors.append("invalid_logout_request_signature")
                self.__errors.append('Signature validation failed. Logout Request rejected')
            elif not logout_request.is_valid(self.__request_data):
                self.__errors.append('invalid_logout_request')
                self.__error_reason = logout_request.get_error()
            else:
                if not keep_local_session:
                    OneLogin_Saml2_Utils.delete_local_session(delete_session_cb)

                in_response_to = logout_request.id
                self._OneLogin_Saml2_Auth__last_message_id = logout_request.id
                response_builder = OneLogin_Saml2_Logout_Response(self.__settings, method)
                response_builder.build(in_response_to)
                self._OneLogin_Saml2_Auth__last_response = response_builder.get_xml()
                logout_response = response_builder.get_response()

                parameters = {'SAMLResponse': logout_response}
                if 'RelayState' in self._OneLogin_Saml2_Auth__request_data['get_data']:
                    parameters['RelayState'] = self.__request_data['get_data']['RelayState']

                security = self._OneLogin_Saml2_Auth__settings.get_security_data()
                if security['logoutResponseSigned']:
                    self.add_response_signature(parameters, security['signatureAlgorithm'])

                return self.redirect_to(self.get_slo_url(), parameters)
        else:
            self.__errors.append('invalid_binding')
            raise OneLogin_Saml2_Error(
                'SAML LogoutRequest/LogoutResponse not found. Only supported HTTP_REDIRECT Binding',
                OneLogin_Saml2_Error.SAML_LOGOUTMESSAGE_NOT_FOUND
            )
