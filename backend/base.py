#!/usr/bin/env python

__author__ = "Jorge Niedbalski R. <jorge@pyrosome.org>"
__license__ = "BSD"

from fabric.api import settings, sudo
from string import Template

import logging
import os

logger = logging.getLogger(name=__file__)
_HERE = os.path.abspath(os.path.dirname(__file__))

class   BaseNode():

    def __init__(self, machine, config, options=None):
        self.machine = machine
        self.username = config['username']
        self.key = config['key']
        self.config = config

        if options:
            self.options = options

        with self.settings(warn_only=True):
            if options.upgrade:
                self.upgrade()
            self.base()
            self.run()
            if options.reboot:
                self.reboot()

    def reboot(self):
        sudo("reboot")

    def template(self, name):
        t_name = os.path.join(_HERE, "templates", name + '.tpl')
        if os.path.exists(t_name):
            with open(t_name) as fd:
                return Template(fd.read())
        return None

    def setup_volumes(self):
        """
            Setup the basic nova-volumes
        """

        if not 'nova-volume' in self.config:
            raise Exception("No disk defined for nova-volumes")

        disk_template = self.template('sfdisk')\
                    .substitute({'volume': self.config['nova-volume']})
        sudo(disk_template)
        sudo("pvcreate -ff -y %s1" % self.config['nova-volume'])
        sudo("vgcreate nova-volumes %s1" % self.config['nova-volume'])

    def setup_bridged(self):
        if 'bridged' in self.config:
            template = self.template("bridged")\
                    .substitute({'interface': self.config['bridged']})
            sudo(template)

    def setup_kvm(self):
        sudo("echo 'kvm' >> /etc/modules")
        sudo("modprobe kvm")

    def setup_host(self, name=None):
        if not name:
            name = self.config['name']
        sudo('echo "%s %s" >> /etc/hosts' % (self.machine, name))
        sudo('echo "kernel.hostname=%s" >> /etc/sysctl.conf' % name)
        sudo('sysctl -w kernel.hostname=%s' % name)

    def base(self):
        sudo("apt-get -y install lvm2 qemu-kvm libvirt-bin")
        self.setup_bridged()
        self.setup_kvm()

    def upgrade(self):
        sudo("apt-get -y update")
        sudo("apt-get -y dist-upgrade")
        logger.info("Updated system")

    def configure(self, filename, key, value):
        with settings(warn_only=True):
            sudo("augtool set /files%s/%s %s" % (filename, key, value))
            sudo("augtool save")

    def install(self, packages, **kwargs):
        if 'gem' in kwargs and kwargs['gem']:
            sudo("gem install %s" % packages)
        else:
            sudo("apt-get -qq -y install %s"  % packages)

    def settings(self, warn_only=False):
        print self.key
        return settings(user=self.username, key_filename=self.key, \
                                warn_only=warn_only, host_string=self.machine)
