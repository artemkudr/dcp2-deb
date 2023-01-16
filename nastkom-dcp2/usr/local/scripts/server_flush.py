#! /usr/bin/python3
import shutil
import os
from datetime import datetime

SRC_DIR="/usr/local/dcp-rx/"
DST_DIR="/usr/local/dcp-tx/"


utc = datetime.utcnow()
for id in ["22","23","25"]:
	files = os.listdir(SRC_DIR + id)
	for f in files:
		shutil.move( os.path.join(SRC_DIR, id, f),  os.path.join(DST_DIR, id, f + utc.strftime(".%y%m%d_%H%M%S")))
