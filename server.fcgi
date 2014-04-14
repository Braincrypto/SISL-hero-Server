#!/usr/bin/python
import sys
sys.path.insert(0, 'env/lib/python2.6/site-packages')

from flup.server.fcgi import WSGIServer
from api import app

if __name__ == '__main__':
    WSGIServer(app).run()
