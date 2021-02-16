import logging
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase

from django.urls import reverse
from djangosaml2_spid.utils import repr_saml

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


def samlrequest_from_html_form(htmlstr):
    regexp = 'name="SAMLRequest" value="(?P<value>[a-zA-Z0-9+=]*)"'
    authn_request = re.findall(regexp, htmlstr)
    if not authn_request:
        raise Exception('AuthnRequest not found in htmlform')
    
    return authn_request[0]

def repr_samlrequest(authnreqstr, **kwargs):
    return repr_saml(authnreqstr, **kwargs)
    

class SpidTest(TestCase):

    def setUp(self):
        self.create_user()

    @classmethod
    def create_user(cls, **kwargs):
        data =  {'username': 'foo',
                 'first_name': 'foo',
                 'last_name': 'bar',
                 'email': 'that@mail.org'}
        for k,v in kwargs.items():
            data[k] = v
        user = get_user_model().objects.create(**data)
        return user


    def test_metadata_endpoint(self):
        url = reverse('djangosaml2_spid:spid_metadata')
        req = Client()
        res = req.get(url)
        
        self.assertEqual(res.status_code, 200)
        # TODO: here validation with spid saml tests
        # ...
        #
        logger.debug(res.content.decode())


    def test_authnreq(self):
        url = reverse('djangosaml2_spid:spid_login')
        req = Client()
        res = req.get(f'{url}?idp=http://localhost:8088')
        self.assertEqual(res.status_code, 200)
        
        htmlform = res.content.decode()
        encoded_authn_req = samlrequest_from_html_form(htmlform)
        
        fancy_saml = repr_samlrequest(encoded_authn_req.encode(), b64=1)
        logger.debug(fancy_saml)


    def test_authnreq_already_logged_user(self):
        url = reverse('djangosaml2_spid:index')
        req = Client()
        user = get_user_model().objects.first()
        req.force_login(user)
        res = req.get(f'{url}')
        self.assertEqual(res.status_code, 200)
        self.assertTrue('LOGGED' in res.content.decode())
        logger.debug(res.content.decode())
        
        url = reverse('djangosaml2_spid:spid_login')
        res = req.get(f'{url}')
    
    def test_logout(self):
        url = reverse('djangosaml2_spid:spid_logout')
        req = Client()
        user = get_user_model().objects.first()
        req.force_login(user)
        res = req.get(f'{url}')

    def test_logout(self):
        url = reverse('djangosaml2_spid:spid_echo_attributes')
        req = Client()
        user = get_user_model().objects.first()
        req.force_login(user)
        res = req.get(f'{url}')
