Installazione
=============

Il plugin è installabile a livello utente oppure a livello sistema qualora si possiedano
privilegi di amministratore. Il consiglio è comunque quello di usare un *ambiente virtuale*
a livello utente, come ad esempio *virtualenv* (o *pyvenv* per Python 3) per non andare in
conflitto con le dipendenze di altre applicazioni Python.

Per l'installazione è necessario clonare il repository:

.. code-block:: bash

  pip install https://github.com/spid-django-hack17/spid-django/archive/master.zip

eseguire poi l'installazione delle dipendenze:

.. code-block:: bash

  pip install -e git+https://github.com/spid-django-hack17/python3-saml.git#egg=python3-saml
  pip install -e git+https://github.com/mehcode/python-xmlsec.git@15e6ce62658cc707dbdce94a13b6bfce8352a7ac#egg=xmlsec


Requisiti
---------

Il plugin è basato sulla libreria `python3-saml <https://github.com/onelogin/python3-saml>`_ di OneLogin.
Questa libreria ha una serie di dipendenze, da installare prima dell'installazione del plugin per SPID.

Su Linux Debian il comando per installare le dipendenze sarebbe:

.. code-block:: bash

  apt-get install libxml2-dev libxmlsec1-dev libxmlsec1-openssl

Su una CentOS Linux i prerequisiti vengono installati con il comando:

.. code-block:: bash

  yum install libxml2-devel xmlsec1-devel xmlsec1-openssl-devel libtool-ltdl-devel

Per ulteriori dettagli consultare la documentazione della libreria
`python-xmlsec <https://github.com/mehcode/python-xmlsec>`_.

Demo
------------------------------

Per eseguire la demo con il server di development di Django:

.. code-block:: bash

  cd example
  pip install -r requirements.txt
  python manage.py migrate
  python manage.py runserver

Accedere poi con un browser all'indirizzo `https://127.0.0.1:8000 <https://127.0.0.1:8000>`_
per verificare il funzionamento della demo.

Per accedere all'`admin della demo <https://127.0.0.1:8000/admin/>`_ usare *demospid* sia per il nome
utente che per la password.