"""
Created on 2024-10-06

@author: wf
"""

import sys
from argparse import ArgumentParser
from pathlib import Path

from ngwidgets.cmd import WebserverCmd

from nomina.converter import Converter
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
        parser.add_argument(
            "--convert",
            type=Path,
            help="Convert the specified file to the desired format",
        )
        parser.add_argument(
            "--format",
            choices=["LB-YAML", "GC-XML", "BEAN"],
            default="LB-YAML",
            help="Output format for conversion [default: %(default)s]",
        )
        parser.add_argument(
            "-o",
            "--output",
            type=Path,
            help="Output file",
        )
        return parser

    def handle_args(self) -> bool:
        """
        handle the command line args
        """
        # Call the superclass handle_args to maintain base class behavior
        handled = super().handle_args()
        self.debug = self.args.debug
        args = self.args
        if args.convert:
            if not args.output:
                print("Error: --output must be specified when using --convert.")
                self.parser.print_help()  # Print usage
                self.exit_code = 1
            else:
                converter = Converter(args)
                converter.convert()
            handled = True
        return handled


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
