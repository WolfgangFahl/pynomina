"""
Created on 2024-10-12

@author: wf
"""

from ngwidgets.input_webserver import InputWebSolution
from ngwidgets.lod_grid import GridConfig, ListOfDictsGrid

from nomina.ledger import Account as LedgerAccount
from nomina.ledger import Book as LedgerBook


class AccountView:
    """
    account display
    """

    def __init__(self, solution: InputWebSolution, grid_row):
        """
        constructor
        """
        self.solution = solution
        self.lod_grid = None
        self.grid_row = grid_row
        self.setup_ui()

    def setup_ui(self):
        with self.grid_row:
            pass

    def style_grid(self, col_name: str, col_option: str, option_value: object):
        """
        style a part of the grid
        """
        for col_def in self.lod_grid.ag_grid.props["options"]["columnDefs"]:
            if col_def["field"] == col_name:
                col_def[col_option] = option_value
                pass

    def update(self, book: LedgerBook, account: LedgerAccount):
        """
        update my user interface with the given account
        """
        try:
            lod = []
            balance = 0.0
            row_num = 0
            for _tx_id, tx in book.transactions.items():
                for split in tx.splits:
                    if split.account_id == account.account_id:
                        if split.amount is not None:
                            row_num += 1
                            balance += split.amount
                            record = {
                                "#": row_num,
                                "Date": tx.isodate,
                                "Memo": split.memo,
                                "Amount": f"{split.amount:10.2f}",
                                "Ok": "⚫" if split.reconciled else "⚪",
                                "Balance": f"{balance:10.2f}",
                            }
                            lod.append(record)
            if self.lod_grid is None:
                key_col = "#"
                grid_config = GridConfig(
                    key_col=key_col,
                    editable=False,
                    multiselect=True,
                    with_buttons=False,
                    debug=False,
                )
                with self.grid_row:
                    self.lod_grid = ListOfDictsGrid(lod=lod, config=grid_config)
                    self.lod_grid.set_checkbox_selection(key_col)
                    # type: 'rightAligned'
                    self.style_grid("Amount", "type", "rightAligned")
                    self.style_grid("Balance", "type", "rightAligned")
                    self.style_grid(
                        "Amount",
                        "cellClassRules",
                        {"amount_negative": "x<0", "amount_positive": "x>=0"},
                    )
                    pass
                    # self.select_all_button.on("click", self.lod_grid.select_all_rows)
            else:
                with self.grid_row:
                    self.lod_grid.load_lod(lod)
                    self.lod_grid.update()
        except Exception as ex:
            self.solution.handle_exception(ex)
        pass
