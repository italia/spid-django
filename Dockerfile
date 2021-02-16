FROM alpine:3.13.0

RUN apk update
RUN apk add build-base git py3-pip python3 python3-dev libffi-dev openssl-dev cargo xmlsec-dev mysql-client py3-mysqlclient
RUN ln -s /usr/bin/python3 /usr/bin/python
RUN pip install -U setuptools pip

WORKDIR /run/spid-django/

COPY ./example/ ./example/
COPY ./src/ ./src/
COPY ./requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

ENV SPID_DJANGO_DOCKERIZED_EXAMPLE="True"

WORKDIR /run/spid-django/example/
CMD ./run.sh
