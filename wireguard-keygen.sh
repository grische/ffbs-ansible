#!/bin/sh

set -e

tempdir=$(mktemp -d)

wg genkey > "${tempdir}/privatekey"
wg pubkey < "${tempdir}/privatekey" > "${tempdir}/publickey"

# ansible-vault encrypt < "${tempdir}/privatekey" > "${tempdir}/privatekey.encrypted"

# Read encrypted keys into variables
private_key_yaml=$(ansible-vault encrypt_string --stdin-name 'wg_private_key' < "${tempdir}/privatekey")
public_key=$(cat "${tempdir}/publickey")

# Output in YAML format using printf
echo "${private_key_yaml}"
echo "wg_public_key: '${public_key}'"

rm -r "${tempdir}"
