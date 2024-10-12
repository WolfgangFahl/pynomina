'''
Created on 2024-10-12

@author: wf
'''
from ngwidgets.input_webserver import InputWebSolution
from ngwidgets.local_filepicker import LocalFilePicker
from nomina.file_formats import AccountingFileFormats
from nicegui import ui, run
from nomina.ledger import Book as LedgerBook
import os

class BookView():
    """
    view a Ledger Book (of any accounting file format)
    """

    def __init__(self,solution:InputWebSolution):
        self.solution=solution
        self.is_local=self.solution.is_local
        self.file_formats=AccountingFileFormats()
        self.file_path=None
        self.summary_card=None

    def load_book(self):
        """
        load book
        """
        with self.solution.content_div:
            try:
                ui.notify(f"loading {self.file_path}...")
                self.file_format=self.file_formats.detect_format(self.file_path)
                if self.file_format.acronym=="LB-YAML":
                    self.book=LedgerBook.load_from_yaml_file(self.file_path)
                    self.stats=self.book.get_stats()
                    with ui.card() as self.summary_card:
                        ui.label(f"{self.file_path} ({self.file_format.acronym})")
                        ui.label(f"{self.stats.start_date}-{self.stats.end_date}")
                        ui.label(f"{self.stats.accounts} accounts, {self.stats.transactions} transactions")
                    pass
            except Exception as ex:
                self.solution.handle_exception(ex)

    async def read_and_optionally_render(self, input_str, with_render: bool = False):
        """
        Reads the given input and optionally renders the given input

        Args:
            input_str (str): The input string representing a URL or local file.
            with_render(bool): if True also render
        """
        if with_render:
            # just to use the flag
            pass
        if self.is_local and os.path.isfile(input_str):
            self.file_path=input_str
            await run.io_bound(self.load_book)


    async def open_file(self) -> None:
        """Opens a Local filer picker dialog and reads the selected input file."""
        if self.is_local:
            pick_list = await LocalFilePicker("~", multiple=False)
            if len(pick_list) > 0:
                input_file = pick_list[0]
                await self.read_and_optionally_render(input_file)

    def setup_ui(self):
        """
        setup my user interface
        """
        self.book_html=ui.html("Welcome to Nomina!")
