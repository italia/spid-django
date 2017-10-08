# django-spid-demo
Demo of a SPID authentication for Django,
based on [python3-saml](https://github.com/onelogin/python3-saml).


# Introduction
This is a django project with one demo app, that shows how to use
Single Sign On authentication through a SPID Identity Provider (SAML).

Technical documentation on SPID and SAML is available at:
https://github.com/italia/spid-docs and
https://github.com/umbros/spid-docs/blob/master/pages/documentazione-e-utilita.md


The identity provider can be installed on the development environment
following instructions at:
https://github.com/umbros/spid-docs/blob/master/pages/spid-ambiente-di-test.md


# Install

``` bash
pip install -r requirements.txt
````

# Execution

When the server is running, the home page shows a login button that
starts the SSO workflow.

Pressing the login button, a request is packed and sent to the IdP.

# Note
The request seems not to contain the <ds:Signature> tag, which is
[required in the documentation](https://spid-regole-tecniche.readthedocs.io/en/latest/regole-tecniche-idp.html#id4)

A modification to python3-saml library is thus required,
in order to put the signature within the request.

# Tools useful for debugging
- browser extensions to track SAML requests and response (they exist both for Chrome and Firefox)
- the "tools" tab within the `carbon` admin interface of the IdP, that allows the verification of the requests.

