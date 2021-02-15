CERTIFICATES_DIR="`pwd`/example/certificates/"
OPENSSL_DOCKER_IMAGE="frapsoft/openssl"

OPENSSL_CMD="docker run --rm -v $CERTIFICATES_DIR:/export/ $OPENSSL_DOCKER_IMAGE"

PRIVATE_KEY_PEM_FILE="private.key"
CERTIFICATE_PEM_FILE="public.cert"

SUBJ_C="IT"
SUBJ_ST="State"
SUBJ_L="City"
SUBJ_O="Acme Inc."
SUBJ_OU="IT Department"
SUBJ_CN="spid-django.selfsigned.example"

DAYS="730"

set -e

ls $CERTIFICATES_DIR > /dev/null

$OPENSSL_CMD req \
  -nodes \
  -new \
  -x509 \
  -sha256 \
  -days $DAYS \
  -newkey rsa:2048 \
  -subj "/C=$SUBJ_C/ST=$SUBJ_ST/L=$SUBJ_L/O=$SUBJ_O/OU=$SUBJ_OU/CN=$SUBJ_CN" \
  -keyout "/export/$PRIVATE_KEY_PEM_FILE" \
  -out "/export/$CERTIFICATE_PEM_FILE"
