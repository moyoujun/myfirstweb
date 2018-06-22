# -*- coding: utf-8 -*-

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from flaskWeb import app

http_server=HTTPServer(WSGIContainer(app))
http_server.listen(80)
IOLoop.instance().start()
