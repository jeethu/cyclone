# coding: utf-8
#
# Copyright 2010 Alexandre Fiori
# based on the original Tornado by Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Support for Bootle application style.

http://bottlepy.com

For more information see the bottle demo:
https://github.com/fiorix/cyclone/tree/master/demos/bottle
"""

import cyclone.web
import functools
import sys

from twisted.python import log
from twisted.internet import reactor

_handlers = []
_BaseHandler = None


class Router:
    def __init__(self):
        self.items = []

    def add(self, method, callback):
        self.items.append((method, callback))

    def __call__(self, *args, **kwargs):
        obj = _BaseHandler(*args, **kwargs)
        for (method, callback) in self.items:
            callback = functools.partial(callback, obj)
            setattr(obj, method.lower(), callback)
        return obj


def route(path=None, method="GET", callback=None, **kwargs):
    """Use this decorator to route requests to the handler.

    Example::

        @route("/")
        def index(cli):
            cli.write("Hello, world")

        @route("/foobar", method="post")
        def whatever(cli):
            ...
    """
    if callable(path):
        path, callback = None, path

    def decorator(callback):
        _handlers.append((path, method.lower(), callback, kwargs))
        return callback

    return decorator


def run(**settings):
    """Start the application.

    Parameters:

    host: Interface to listen on. [default: 0.0.0.0]

    port: TCP port to listen on. [default: 8888]

    more_handlers: A regular list of tuples containing regex -> handler

    All other parameters are passed directly to the `cyclone.web.Application`
    constructor.
    """

    global _handlers, _BaseHandler
    port = settings.get("port", 8888)
    interface = settings.get("host", "0.0.0.0")
    log.startLogging(settings.pop("log", sys.stdout))
    _BaseHandler = settings.pop("base_handler", cyclone.web.RequestHandler)

    handlers = {}
    for (path, method, callback, kwargs) in _handlers:
        if path not in handlers:
            handlers[path] = Router()
        handlers[path].add(method, callback)

    _handlers = None

    handlers = handlers.items() + settings.pop("more_handlers", [])
    application = cyclone.web.Application(handlers, **settings)
    reactor.listenTCP(port, application, interface=interface)
    reactor.run()
