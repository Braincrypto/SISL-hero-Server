#!/usr/bin/python
import sys
sys.path.insert(0, 'venv/lib/python2.7/site-packages')

from wsgiref.handlers import CGIHandler
from api import app

CGIHandler().run(app)
