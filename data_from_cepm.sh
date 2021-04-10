#!/bin/bash
cd `dirname ${BASH_SOURCE[0]}`

/usr/local/bin/wget --quiet http://106.37.208.233:20035/emcpublish/ClientBin/Env-CnemcPublish-RiaServices-EnvCnemcPublishDomainService.svc/binary/GetAQIDataPublishLives -O GetAQIDataPublishLives &&
touch lastcheck

/usr/local/bin/python3 python-wcfbin/wcf2xml.py GetAQIDataPublishLives > data.xml &&

#cp data.xml xml/$(date +%Y%m%d%H%M)_data.xml

/usr/local/bin/python3 xml2json.py


