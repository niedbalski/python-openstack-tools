#!/usr/bin/env python

__author__ = "Jorge Niedbalski R. <jorge@pyrosome.org>"
__license__ = "BSD"


import yaml
import subprocess
import optparse
import os
import collections
import tempfile

from string import Template


_HERE = os.path.abspath(os.path.dirname(__file__))


class   Environment:

    def __init__(self, options):

        self.options = options
        self.args = []

        for option, value in self.options.items():
            if hasattr(self, option):
                method = getattr(self, option)
                if method:
                    method(value)

    def template(self, name):
        t_name = os.path.join(_HERE, "templates", name)
        if os.path.exists(t_name):
            with open(t_name) as fd:
                return Template(fd.read())
        return None

    def flatten(self, d, parent_key=''):
        items = []
        for k, v in d.items():
            new_key = parent_key + '_' + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(self.flatten(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def console(self, console):
            return self.args.append\
                ('--extra-args="priority=critical locale=en_US interface=auto"')

    def preseed(self, preseed):
        return self.args\
                .append('--initrd-inject=%s' % preseed)

    def virt_install(self, name=None):

        if not name:
            name = self.options['name']

        args = " ".join(self.args)
        command = self.template("virt-install.tpl")
        virt_install = command.safe_substitute({'location': self.options['iso'],\
                                                'name': name, \
                                                'args': args})
        return virt_install

    def compute_nodes(self):
        settings = self.options['compute']
        self.args.append("--ram=%s --vcpus=%s" % \
                                    (settings['memory'], settings['vcpu']))
        for node in range(0, settings['nodes']):
            yield virt_install()

    def controller_node(self):
        settings = self.options['controller']
        self.args.append("--ram=%s --vcpus=%s" % \
                                    (settings['memory'], settings['vcpu']))
        return self.virt_install()

    def disk(self, options):
        """
            Creates options for disk image initialization
        """
        for name, volume in options['volumes'].items():
            self.args.append("--disk path=%s/%s-%s.img,size=%s" % \
                        (self.options['path'], self.options['name'],\
                                            name, volume['size']))
        return self.args

    def network(self, options):
        """
            Creates options for network configuration
        """
        for interface, config in options['interfaces'].items():

            network_template = self.template('network.xml')
            config = self.flatten(config)
            config['network_name'] = interface
            network_template = \
                        network_template.safe_substitute(config)
            try:
                f = tempfile.NamedTemporaryFile(delete=False)
                f.write(network_template)
                ret = \
                    subprocess.Popen(["virsh", "net-create", f.name], \
                               shell=False, stderr=subprocess.STDOUT, \
                                              stdout=subprocess.PIPE)
                f.close()
            except Exception as ex:
                raise

            self.args.append("--network=bridge:%s" % config['interface'])

        return self.args


class   StackLibvirt:

    def __init__(self, options):
        if options.config:
            with open(options.config) as fd:
                self.config = yaml.load(fd.read())
            self.options = options
        self.run()

    def environment(self, env_config):
        self.env = Environment(env_config)

    def run(self):
        for option, value in self.config.items():
            if hasattr(self, option):
                attr = getattr(self, option)
                if attr:
                    attr(value)

        controller = self.env.controller_node()
        #(nodes, params) = self.compute_params()
        self.start(controller)

    def start(self, command):
        print "Running %s" % command
        subprocess.Popen(command, shell=True)

class Config:
    def __init__(self):
        self.config = "./config/stack-libvirt.yml"


def main():
    virt = StackLibvirt(Config())

if __name__ == "__main__":
    main()
