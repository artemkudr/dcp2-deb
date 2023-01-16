#!/bin/bash

cd /var/dcp/data/

for f in *
do
	unzip -p '/var/dcp/archive/'$f'*.zip'  >> '/var/dcp/data/'$f
done
