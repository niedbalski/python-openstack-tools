#!/usr/bin/env python

__author__ = "Jorge Niedbalski R. <jorge@pyrosome.org>"
__license__ = "BSD"

from novaclient.v1_1 import client
from optparse import OptionParser
from fabric.api import settings, sudo

import sys
import yaml
import logging
import os
import time

_HERE = os.path.abspath(os.path.dirname(__file__))


logger = logging.getLogger(name=__file__)


class OpenStackImageBuildException(Exception):
    pass


class OpenStackImageBuild:

    def __init__(self, options, **kwargs):
        """
            Image building process
        """
        api_options = ( 'username', 'password', 'auth_url', 'tenant')
        try:
            with open(options.config) as config:
                self.config = yaml.load(config.read())

            logger.info("Loaded configuration file: %s" % options.config)
            self.options = options

            for option in api_options:
                has_option = getattr(self.options, option)

                if not has_option and 'api' in self.config:
                    if option in self.config['api']:
                        setattr(self.options, option, \
                                        self.config['api'][option])
                    else:
                        raise Exception("Not defined %s api option" % option)

            self.client = client.Client(self.options.username, \
                                        self.options.password, \
                                        self.options.tenant, \
                                        self.options.auth_url,\
                                        service_type="compute")
        except Exception as ex:
            logger.error(ex)
            raise OpenStackImageBuildException(ex)

        logger.info("Starting image building process")
        self.build()

    def build(self):
        """
        """
        try:
            connection = self.instance()
            with connection:

                if self.config['upgrade']:
                    logger.info("Upgrading base %s system" % \
                                    self.config['instance']['base'])
                    self.upgrade()

                if self.config['packages']:
                    logger.info("Installing packages")
                    self.install(self.config['packages'])

                if self.config['commands']:
                    logger.info("Running user defined commands")
                    for command in self.config['commands']:
                        self.run(command)

            image_id = self.snapshot()

            if self.config['wait_snapshot']:
                message = "Image: %s is waiting for creation, Image ID: %s" % \
                                                (self.config['name'], image_id)
            else:
                message = "Image: %s is now available. Image ID: %s" % \
                                (self.config['name'], image_id)

            logger.info(message)

        except Exception as ex:
            logger.error(ex)
            raise OpenStackImageBuildException(ex)
        finally:
            self.finish()

        logger.info("Finished image creation")
        return image_id

    def run(self, command):
        """
        """
        sudo(command)

    def upgrade(self):
        """
            Only debian based is supported
        """
        sudo("apt-get -y update")
        sudo("apt-get -y dist-upgrade")

    def package(self, package):
        return "apt-get -yy install %s" % package

    def easy_install(self, package):
        return "easy_install %s" % package

    def install(self, packages):
        """
        """
        for pkg_type, package in packages.items():
            attr = getattr(self, pkg_type)
            if attr:
                install = attr(package)
                sudo(install)

    def snapshot(self):
        self.server.create_image(self.config['name'])
        image = self.client.images.find(name=self.config['name'])

        if self.config['wait_snapshot']:
            while image.status != 'ACTIVE':
                logger.info("Waiting for instance snapshot to be ready")
                time.sleep(5)
                image = self.client.images.find(name=self.config['name'])
        return image.id

    def finish(self):
        self.client.keypairs.delete(self.key_name)
        os.remove(self.key_filename)
        self.server.delete()

    def is_server_ready(self):

        while not 'novanetwork' in self.server.addresses or \
            not len(self.server.addresses['novanetwork']) >= 2:
                time.sleep(2)
                self.server = self.client.servers.get(self.server.id)

        return [address['addr'] for address in \
                        self.server.addresses['novanetwork']]

    def instance(self, warn_only=True):
        """
        """
        try:
            image = \
                self.client.images.find(name=self.config['instance']['base'])

            if not image:
                raise Exception("Image %s not found" % \
                                self.config['instance']['base'])

            flavor = \
                self.client.flavors.find(name=self.config['instance']['type'])

            if not flavor:
                raise Exception("Flavor %s not found" % \
                                self.config['instance']['type'])

            key_name = "image_build-%d" % int(time.time())
            keypair = self.client.keypairs.create(key_name)

            if key_name:
                self.key_name = key_name

            if keypair:
                self.key_filename = os.path.join(_HERE, "%s.pem" % \
                                                        self.key_name)
                with open(self.key_filename, "w+") as fd:
                    fd.write(keypair.private_key)
                    logger.info("Generated temporary key %s" % \
                                                self.key_filename)

            self.server = self.client\
                    .servers.create('image_build', image=image,
                            key_name=self.key_name, flavor=flavor)
            logger.info("Created new server instance, name:%s - id:%s\n "\
                        "Waiting for server ..." % \
                                (self.server.name, self.server.hostId))

            (self.private_ip, self.public_ip) = self.is_server_ready()
            logger.info("Server is ready ip_addr: %s" % self.public_ip)

        except Exception as ex:
            logger.error(ex)
            raise

        username = self.config['instance'].get('username', 'ubuntu')

        return settings(user=username,
                        key_filename=self.key_filename,
                        warn_only=warn_only,
                        host_string=self.public_ip)


def main():
    parser = OptionParser()
    parser.add_option("-c", "--config", help="Node configuration file", \
                                            metavar="config")
    parser.add_option("-v", "--verbose", help="Verbose mode", \
                                            metavar="verbose", default=False)
    parser.add_option("-u", "--username", help="Nova API username", \
                                            metavar="username")
    parser.add_option("-p", "--password", help="Nova API password", \
                                            metavar="password")
    parser.add_option("-t", "--tenant", help="Nova API Tenant",
                                            metavar="tenant")
    parser.add_option("-a", "--auth-url", help="Nova API Auth URL",
                                            metavar="auth")

    (options, args) = parser.parse_args()

    if not options.config:
        sys.stderr.write("You MUST specify a config file [-c|--config]\n")
        sys.exit(-1)

    if options.verbose:
        level = logging.DEBUG | logging.INFO
    else:
        level = logging.INFO

    logging.basicConfig(level=level,
                        format='%(levelname)s: %(message)s', filemode="w")
    OpenStackImageBuild(options)


if __name__ == "__main__":
    main()
