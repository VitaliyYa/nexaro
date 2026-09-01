#!/usr/bin/env bash
# Generate Local Development / Testing TLS Certificates for Mosquitto Broker
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERTS_DIR="${SCRIPT_DIR}/certs"

echo "Generating development certificates in ${CERTS_DIR}..."
mkdir -p "${CERTS_DIR}"

DAYS_VALID=365

# 1. Certificate Authority (CA)
echo "Creating Root CA with OpenSSL 3.x compliant extensions..."
rm -f "${CERTS_DIR}/ca.key" "${CERTS_DIR}/ca.crt"
openssl req -new -x509 -days ${DAYS_VALID} \
    -keyout "${CERTS_DIR}/ca.key" -out "${CERTS_DIR}/ca.crt" \
    -subj "/C=US/ST=Dev/L=Local/O=SmartRent/OU=IoT/CN=SmartRent-Dev-RootCA" \
    -addext "basicConstraints=critical,CA:TRUE" \
    -addext "keyUsage=critical,keyCertSign,cRLSign" \
    -addext "subjectKeyIdentifier=hash" \
    -nodes


# 2. Server Certificate
echo "Creating Mosquitto Server Key and CSR..."
openssl req -new -nodes \
    -out "${CERTS_DIR}/server.csr" \
    -keyout "${CERTS_DIR}/server.key" \
    -subj "/C=US/ST=Dev/L=Local/O=SmartRent/OU=IoT/CN=localhost"

# Create SAN configuration for server
cat > "${CERTS_DIR}/server.ext" <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = broker.local
DNS.3 = mosquitto
IP.1 = 127.0.0.1
EOF

echo "Signing Mosquitto Server Certificate with CA..."
openssl x509 -req -in "${CERTS_DIR}/server.csr" \
    -CA "${CERTS_DIR}/ca.crt" -CAkey "${CERTS_DIR}/ca.key" \
    -CAcreateserial \
    -out "${CERTS_DIR}/server.crt" \
    -days ${DAYS_VALID} \
    -extfile "${CERTS_DIR}/server.ext"

# 3. Client Certificate (for Edge Node / Backend testing)
echo "Creating Test Client Certificate..."
openssl req -new -nodes \
    -out "${CERTS_DIR}/client.csr" \
    -keyout "${CERTS_DIR}/client.key" \
    -subj "/C=US/ST=Dev/L=Local/O=SmartRent/OU=IoT/CN=test-client"

cat > "${CERTS_DIR}/client.ext" <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
EOF

openssl x509 -req -in "${CERTS_DIR}/client.csr" \
    -CA "${CERTS_DIR}/ca.crt" -CAkey "${CERTS_DIR}/ca.key" \
    -CAcreateserial \
    -out "${CERTS_DIR}/client.crt" \
    -days ${DAYS_VALID} \
    -extfile "${CERTS_DIR}/client.ext"

# Cleanup temporary CSRs and ext files
rm -f "${CERTS_DIR}/server.csr" "${CERTS_DIR}/server.ext" "${CERTS_DIR}/client.csr" "${CERTS_DIR}/client.ext" "${CERTS_DIR}/ca.srl"

chmod 600 "${CERTS_DIR}"/*.key
chmod 644 "${CERTS_DIR}"/*.crt

echo "Development certificates generated successfully in ${CERTS_DIR}!"
