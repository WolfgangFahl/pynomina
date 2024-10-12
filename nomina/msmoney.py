"""
Created on 2024-10-09

@author: wf
"""

import os
from json import JSONDecodeError
from typing import Any, Dict
from zipfile import ZipFile

from lodstorage.yamlable import lod_storable

from nomina.date_utils import DateUtils
from nomina.graph import Graph
from nomina.stats import Stats


@lod_storable
class ZipHeader:
    file_type: str
    version: str
    name: str
    date: str
    size: int
    sha256: str
    jetversion: str


class MsMoney:
    """
    Wrapper for Microsoft Money content
    """

    def __init__(self):
        self.header = None
        self.graph = Graph()

    def load(self, path: str):
        """
        Load Microsoft Money data from a ZIP file or a directory
        """
        if os.path.isdir(path):
            file_generator = self._generate_files_from_directory(path)
        else:
            file_generator = self._generate_files_from_zip(path)

        self._handle_files(file_generator)

    def _generate_files_from_zip(self, zip_path: str):
        """
        Generator that yields file name and file object from a ZIP file
        """
        with ZipFile(zip_path, "r") as zip_file:
            for file_name in zip_file.namelist():
                with zip_file.open(file_name) as file_content:
                    yield file_name, file_content

    def _generate_files_from_directory(self, dir_path: str):
        """
        Generator that yields file name and file object from a directory
        """
        for file_name in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file_name)
            with open(file_path, "r") as file_content:
                yield file_name, file_content

    def _handle_files(self, file_generator):
        """
        Handle the files yielded by the generator (from ZIP or directory)
        """
        for file_name, file_content in file_generator:
            if file_name == "nomina.yaml":
                # Load the YAML file
                self.header = ZipHeader.load_from_yaml_stream(file_content)
            elif file_name.endswith(".json"):
                try:
                    # Load JSON files as networkx nodes
                    self.graph.add_nodes_from_json(file_name, file_content)
                except JSONDecodeError as e:
                    print(f"Error decoding JSON in file {file_name}: {e}")
                    continue

    def to_transaction_dict(self, data) -> Dict[str, Any]:
        """
        convert a data node to a transcaction dict with transaction_id and isodate
        """
        tx_dict = None
        if data.get("type") == "TRN":
            transaction_id = str(data.get("htrn"))
            t_date = data.get("dt")
            isodate = DateUtils.parse_date(t_date)
            tx_dict = {
                "transaction_id": transaction_id,
                "isodate": isodate,
                "amount": data.get("amt", 0.0),
                "account_id": data.get("hacct"),
            }
        return tx_dict

    def get_stats(self) -> Stats:
        """
        Get statistics about the Microsoft Money data.

        Returns:
            Stats: An object containing various statistics about the data.
        """
        graph = self.graph.graph  # Assign for clarity

        # Calculate date range
        dates = []
        transactions = 0
        for _node, data in graph.nodes(data=True):
            tx_dict = self.to_transaction_dict(data)
            if tx_dict is not None:
                transactions += 1
                dates.append(tx_dict["isodate"])

        if dates:
            min_date = min(dates)
            max_date = max(dates)
        else:
            min_date = max_date = None

        # Count accounts and calculate currency counts
        accounts = 0
        currency_counts = {}
        for _node, data in graph.nodes(data=True):
            if data.get("type") == "ACCT":
                accounts += 1
                currency = data.get("currency", "UNKNOWN")
                currency_counts[currency] = currency_counts.get(currency, 0) + 1

        return Stats(
            accounts=accounts,
            transactions=transactions,
            start_date=min_date,
            end_date=max_date,
            currencies=currency_counts,
        )
