#!/bin/bash

KEY_DIR="/home/root/.ssh"

# Make directories
mkdir -p "$KEY_DIR"

# Generate an RSA key using dropbear
dropbearkey -t rsa -f "${KEY_DIR}/id_rsa"

# Output Public Key
dropbearkey -y -f "${KEY_DIR}/id_rsa" | grep "^ssh-rsa " > "${KEY_DIR}/id_rsa.pub"

# Show Public Key
cat "${KEY_DIR}/id_rsa.pub"
