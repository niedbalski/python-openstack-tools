#!/usr/bin/env python

__author__ = "Jorge Niedbalski R. <jorge@pyrosome.org>"
__license__ = "BSD"

from backend.loader import StackLoader
from optparse import OptionParser

import os

_HERE = os.path.abspath(os.path.dirname(__file__))

def main():
    parser = OptionParser()
    parser.add_option("-c", "--config", \
                    dest="config", help="Stack descriptor file")
    parser.add_option("-u", "--upgrade", \
                    dest="upgrade", help="Force upgrade the base system", \
                    default=False)
    parser.add_option("-n", "--nova-volumes", \
                    help="Create the associated nova-volumes label"\
                       ,default=False)
    parser.add_option("-m", "--puppet-master",\
                        help="Run the puppet master installation on this"\
                        ,default=False)
    parser.add_option("-o", "--openstack", dest="openstack",\
                        help="Download ubuntu image and add default firewall\
                                                                    rules",
                        default=False)
    parser.add_option("-r", "--reboot",
                    dest="reboot", help="Force reboot after installation", \
                            default=False)
    (options, args) = parser.parse_args()

    if not options.config:
        options.config = os.path.join(_HERE, 'config', 'stack.yml')

    l = StackLoader(options)
    l.run()

if __name__ == "__main__":
    main()

