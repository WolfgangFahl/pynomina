"""
Created on 2024-10-06

@author: wf
"""

import os

from ngwidgets.input_webserver import InputWebserver, InputWebSolution
from ngwidgets.webserver import WebserverConfig
from nicegui import Client, app, ui

from nomina.version import Version


class NominaWebServer(InputWebserver):
    """
    Nomina Webserver
    """

    @classmethod
    def get_config(cls) -> WebserverConfig:
        copy_right = "(c)2024 Wolfgang Fahl"
        config = WebserverConfig(
            copy_right=copy_right,
            version=Version(),
            default_port=9849,
            short_name="nomina",
        )
        server_config = WebserverConfig.get(config)
        server_config.solution_class = NominaSolution
        return server_config

    def __init__(self):
        """Constructs all the necessary attributes for the WebServer object."""
        InputWebserver.__init__(self, config=NominaWebServer.get_config())

    def configure_run(self):
        root_path = (
            self.args.root_path
            if self.args.root_path
            else NominaWebServer.examples_path()
        )
        self.root_path = os.path.abspath(root_path)
        self.allowed_urls = [
            self.examples_path(),
            self.root_path,
        ]

    @classmethod
    def examples_path(cls) -> str:
        # the root directory (default: examples)
        path = os.path.join(os.path.dirname(__file__), "../nomina_examples")
        path = os.path.abspath(path)
        return path


class NominaSolution(InputWebSolution):
    """
    the Nomina solution
    """

    def __init__(self, webserver: NominaWebServer, client: Client):
        """
        Initialize the solution

        Calls the constructor of the base solution
        Args:
            webserver (NiceScadWebServer): The webserver instance associated with this context.
            client (Client): The client instance this context is associated with.
        """
        super().__init__(webserver, client)  # Call to the superclass constructor
