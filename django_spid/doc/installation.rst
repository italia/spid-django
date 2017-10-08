Installazione
==================

1. L'installazione consiste nel clonare inizialmente la seguente `repo <https://github.com/pdpfsug/django-ex>`__ .

2. Successivamente si procederà con la creazione di un ambiente virtuale, mediante *virtual-env*, nella quale l'utente installerà le
dipendenze richieste dall'applicativo software attraverso il comando:

``python pip install -r requirements.txt``

3. Fatto ciò, occorrerà inizializzare il database affinché l'intero sistema cooperi al raggiungimento dello scopo, tramite il seguente comando:

``./manage.py migrate``

4. In seguito sarà necessario avviare il server:

``./manage.py runserver``

5. A questo punto, basterà visualizzare sul proprio browser il localhost puntandolo sulla porta **8000**, valore di default, visualizzando così l'interfaccia grafica prodotta dal software.

6. Infine sarà possibile tenere sotto controllo il log degli eventi nella bash da cui è stato lanciato il comando *runserver* per poter leggere eventuali errori.
