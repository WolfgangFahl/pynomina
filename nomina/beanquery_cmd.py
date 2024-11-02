"""
Created on 2024-11-02

@author: wf
"""

import sys
from argparse import ArgumentParser, Namespace
from nomina.bean_query import BeanQueryHandler
from lodstorage.query_cmd import QueryCmd, Format


class BeanQueryCmd(QueryCmd):
    """
    Extended version of QueryCmd to support
    named parameterized queries for beanquery
    """

    def __init__(self, args: Namespace):
        args.language="sql"
        super().__init__(args, with_default_queries=False)

    def handle_args(self) -> bool:
        """
        Handle the command line arguments, ensure the query is loaded and parameters are parsed.
        """
        # Call the superclass method to handle basic argument parsing
        handled = super().handle_args()

        if self.queryCode:
            # Parameters should have already been parsed and applied in the base class
            if self.args.debug or self.args.showQuery:
                print(f"Final query after parameter substitution:\n{self.query.query}")
            endpoint=self.endpoints.get(self.args.endpointName)
            if not endpoint:
                raise ValueError(f"unknown endpoint {self.args.endpointName}")
            query_handler=BeanQueryHandler(beancount_file=endpoint.endpoint)
            qlod=query_handler.execute_query(self.queryCode)
            self.format_output(qlod)
        return handled


def main(argv: list = None):
    """
    Main entry point for the npbeanquery script.
    """
    parser = ArgumentParser(
        description="BeanQuery command-line tool with extended features"
    )
    BeanQueryCmd.add_args(parser)
    # @FIXME - redundannt argument handling
    parser.add_argument(
            "-en",
            "--endpointName",
            default="example_beancount",
            help=f"Name of the endpoint to use for queries. - use -el option to list available endpoints",
    )
    parser.add_argument("-f", "--format", type=Format, choices=list(Format))

    args = parser.parse_args(argv)

    cmd = BeanQueryCmd(args)
    handled = cmd.handle_args()

    # Query execution should be done by handle_args() or subsequent method calls
    return 0 if handled else 1


if __name__ == "__main__":
    sys.exit(main())
