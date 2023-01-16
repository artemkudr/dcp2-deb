#! /bin/bash

systemctl stop aserver.service
sleep 1
#python3 /usr/local/scripts/server_flush.py
systemctl start aserver.service

