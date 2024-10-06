"""
Created on 2024-10-06

@author: wf
"""

import sys
from argparse import ArgumentParser

from ngwidgets.cmd import WebserverCmd

from nomina.webserver import NominaWebServer


class NominaCmd(WebserverCmd):
    """
    command line handling for nomina
    """

    def __init__(self):
        """
        constructor
        """
        config = NominaWebServer.get_config()
        WebserverCmd.__init__(self, config, NominaWebServer, DEBUG)
        pass

    def getArgParser(self, description: str, version_msg) -> ArgumentParser:
        """
        override the default argparser call
        """
        parser = super().getArgParser(description, version_msg)
        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="show verbose output [default: %(default)s]",
        )
        parser.add_argument(
            "-rp",
            "--root_path",
            default=NominaWebServer.examples_path(),
            help="path to nomina files [default: %(default)s]",
        )
        return parser


def main(argv: list = None):
    """
    main call
    """
    cmd = NominaCmd()
    exit_code = cmd.cmd_main(argv)
    return exit_code


DEBUG = 0
if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-d")
    sys.exit(main())
