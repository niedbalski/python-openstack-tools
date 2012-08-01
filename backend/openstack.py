#!/usr/bin/env python

__author__ = "Jorge Niedbalski R. <jorge@pyrosome.org>"
__license__ = "BSD"

from __future__ import absolute_import
from .base import BaseNode
from fabric.api import sudo, settings, put

import time
import os
import logging

logger = logging.getLogger(name=__file__)


__backend__ = [ 'OpenStackController', 'OpenStackCompute' ]


PUPPETLABS_OPENSTACK = \
            "git://github.com/puppetlabs/puppetlabs-openstack openstack"
_HERE = os.path.abspath(os.path.dirname(__file__))


class   OpenStackCompute(BaseNode):

    def __init__(self, machine, config, options):
        BaseNode.__init__(self, machine, config, options)

    def run(self):
        if self.options.nova_volumes:
            self.setup_volumes()
        self.puppet()

    def add_puppet_master(self):
        sudo('echo "%s %s" >> /etc/hosts' % \
                    (self.config['controller']['address'],\
                     self.config['controller']['name']))

    def puppet(self):
        self.install("qemu libvirt-bin libvirt-dev libvirt0")
        self.install("puppet augeas-tools")
        self.add_puppet_master()

        puppet_agent = self.template("puppet-agent")\
                           .substitute({'server_name':\
                                self.config['controller']['name']})
        sudo(puppet_agent)
        rand = int(time.time())
        self.setup_host(name="compute-%s" % rand)
        sudo("puppet agent -vt --waitforcert 20 --certname openstack_compute_%s"\
                                                                        % rand)
        logger.info("Completed installation of a new compute node")

    def nagios(self):
        #We should add to nagios, and start monitoring this new machine
        logger.info("Add to nagios")
        pass


class   OpenStackController(BaseNode):

    def __init__(self, machine, config, options):
        BaseNode.__init__(self, machine, config, options)

    def run(self):
        #setup the nova-volumes
        if self.options.nova_volumes:
            self.setup_volumes()
        self.setup_host()

        if self.options.puppet_master:
            self.puppet_master()
        self.puppet_agent()

        #setup basic openstack 
        if self.options.openstack:
            self.openstack()

    def puppet_master(self):
        """
            Install the puppet master service on the machine
        """
        self.install("puppet augeas-tools")
        self.install("puppetmaster sqlite3 libsqlite3-ruby git rake")
        self.install("libactiverecord-ruby")
        self.install("puppetlabs_spec_helper", gem=True)
        self.install("puppetmaster-common")

        puppet_master = self.template("puppet-master").substitute()
        sudo(puppet_master)

        sudo("cd /etc/puppet/modules; git clone %s; "\
             "cd openstack; rake modules:clone" % PUPPETLABS_OPENSTACK)

        self.manifest()
        self.puppet_restart()

    def puppet_agent(self):

        puppet_agent = self.template("puppet-agent")\
                .substitute({'server_name': self.config['name']})
        sudo(puppet_agent)
        sudo("puppet agent -vt --waitforcert 20 --certname openstack_controller")

    def puppet_restart(self):
        sudo("/etc/init.d/puppetmaster restart")


    def manifest(self):
        """
            Creates a valid openstack manifest
        """
        manifest = self.template('site')
        self.config['openstack']['d_controller_node_address'] = self.machine
        manifest = manifest.safe_substitute(**self.config['openstack'])

        if manifest:
            f_path = os.path.join(_HERE, '..', 'files')

            if not os.path.exists(f_path):
                os.mkdir(f_path)

            local = os.path.join(f_path, 'site.pp')

            with open(local, 'w+') as fd:
                fd.write(manifest)

            put(local, "site.pp")
            sudo("cp ~/site.pp /etc/puppet/manifests/site.pp")

    def openstack(self):
           sudo("cd; wget http://uec-images.ubuntu.com/releases/12.04/release/ubuntu-12.04-server-cloudimg-amd64-disk1.img")
           sudo('glance add name="Ubuntu 12.04 cloudimg amd64" is_public=true container_format=ovf disk_format=qcow2 < ubuntu-12.04-server-cloudimg-amd64-disk1.img')
           sudo("nova secgroup-add-rule default tcp 1 65535 0.0.0.0/0")
           sudo("nova secgroup-add-rule default udp 1 65535 0.0.0.0/0")
           sudo("nova secgroup-add-rule default icmp -1 255 0.0.0.0/0")
