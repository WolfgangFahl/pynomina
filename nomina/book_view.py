"""
Created on 2024-10-12

@author: wf
"""

import os

from ngwidgets.combobox import ComboBox
from ngwidgets.input_webserver import InputWebSolution
from ngwidgets.local_filepicker import LocalFilePicker
from nicegui import background_tasks, run, ui

from nomina.account_view import AccountView
from nomina.file_formats import AccountingFileFormats
from nomina.ledger import Book as LedgerBook


class BookView:
    """
    view a Ledger Book (of any accounting file format)
    """

    def __init__(self, solution: InputWebSolution):
        self.solution = solution
        self.is_local = self.solution.is_local
        self.file_formats = AccountingFileFormats()
        self.file_path = None
        self.summary_card = None

    async def load_book(self):
        """
        load book
        """
        try:
            self.summary_row.clear()
            with self.summary_row:
                ui.notify(f"loading {self.file_path}...")
                self.file_format = self.file_formats.detect_format(self.file_path)

                if not self.file_format:
                    ui.notify("could not detect file format")
                    return

                if not self.file_format.acronym == "LB-YAML":
                    ui.notify(
                        f"can not handle file format {self.file_format.acronym} (yet)"
                    )
                    return
                else:
                    self.book = LedgerBook.load_from_yaml_file(self.file_path)
                    self.stats = self.book.get_stats()
                    with ui.card() as self.summary_card:
                        ui.label(f"{self.file_path} ({self.file_format.acronym})")
                        ui.label(f"{self.stats.start_date}-{self.stats.end_date}")
                        ui.label(
                            f"{self.stats.accounts} accounts, {self.stats.transactions} transactions"
                        )

                    account_names = []
                    for _account_id, account in self.book.accounts.items():
                        account_names.append(account.name)
                    ComboBox(
                        label="account",
                        options=account_names,
                        width_chars=30,
                        clearable=True,
                        on_change=self.select_account,
                    )
        except Exception as ex:
            self.solution.handle_exception(ex)

    async def select_account(self, args):
        """
        select an account
        """
        account_name = args.value
        for _account_id, account in self.book.accounts.items():
            if account_name == account.name:
                self.account_view.update(book=self.book, account=account)
        pass

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
            self.file_path = input_str
            # https://github.com/zauberzeug/nicegui/discussions/2729
            self.summary_row.clear()
            with self.summary_row:
                ui.spinner()
                self.load_task = background_tasks.create(self.load_book())

    def setup_ui(self):
        """
        setup my user interface
        """
        with ui.row() as self.button_row:
            self.solution.tool_button(
                tooltip="reload",
                icon="refresh",
                handler=self.solution.reload_file,
            )
            if self.is_local:
                self.solution.tool_button(
                    tooltip="open",
                    icon="file_open",
                    handler=self.solution.open_file,
                )
        with ui.row() as self.summary_row:
            self.book_html = ui.html("Welcome to Nomina!")
        self.account_view = AccountView(self)
