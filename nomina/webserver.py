"""
Created on 2024-10-06

@author: wf
"""

import os

from ngwidgets.input_webserver import InputWebserver, InputWebSolution
from ngwidgets.webserver import WebserverConfig
from nicegui import Client, ui

from nomina.book_view import BookView
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
        """
        configure things before the server rung
        """
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
        self.book_view = None
        self.root_path = self.webserver.root_path
        self.input = "example.beancount"

    def prepare_ui(self):
        """
        prepare the user interface
        """
        InputWebSolution.prepare_ui(self)
        # try styling for account view
        ui.add_head_html(
            """<style>
.amount-negative {
    color: red;
}
.amount-positive {
    color: blue;
}
</style>
""",
            shared=True,
        )

    async def read_and_optionally_render(self, input_str, with_render: bool = False):
        """
        Reads the given input and optionally renders the given input

        Args:
            input_str (str): The input string representing a URL or local file.
            with_render(bool): if True also render
        """
        if self.book_view is not None:
            await self.book_view.read_and_optionally_render(input_str, with_render)

    def configure_menu(self):
        """
        configure additional non-standard menu entries
        """
        self.tool_button(
            tooltip="reload",
            icon="refresh",
            handler=self.reload_file,
        )
        if self.is_local:
            self.tool_button(
                tooltip="open",
                icon="file_open",
                handler=self.open_file,
            )

    def show_ui(self):
        """
        show the ui
        """
        with self.content_div:
            self.book_view = BookView(self)
            self.book_view.setup_ui()

    async def home(self):
        """
        Home screen
        """
        await self.setup_content_div(self.show_ui)
        if self.args.input:
            await self.read_and_optionally_render(self.args.input)
