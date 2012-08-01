#!/usr/bin/env python

__author__ = "Jorge Niedbalski R. <jorge@pyrosome.org>"
__license__ = "BSD"

import yaml
import os

_HERE = os.path.abspath(os.path.dirname(__file__))


class   StackLoaderException(Exception):
    pass


class   StackLoader:

    backends = {}
    options = None

    def __init__(self, options):
        try:
            self._load_backend()
            with open(options.config) as fd:
                self.config = yaml.load(fd.read())
            self.options = options
        except Exception as ex:
            raise StackLoaderException(ex)

    def _load_backend(self):
        module = __import__("backend", fromlist="*")
        for name in dir(module):
            attr = getattr(module, name)
            if hasattr(attr, "__backend__"):
                for k_name in attr.__backend__:
                    klass = getattr(attr, k_name)
                    if not k_name in self.backends:
                        self.backends[k_name] = klass

    def run(self):
        for backend, config in self.config.items():
            if backend in self.backends:
                backend = self.backends[backend]
                for machine in config['machines']:
                    backend(machine, config, self.options)

