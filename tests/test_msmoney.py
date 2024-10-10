"""
Created on 2024-10-09

@author: wf
"""

from nomina.msmoney import MsMoney
from tests.basetest import Basetest


class Test_Microsoft_Money(Basetest):
    """
    test Microsoft money handling
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_load_microsoft_money(self):
        """
        test loading Microsoft Money zip file
        """
        for money_example in [
            self.examples_path + "/sample_microsoft_money.zip",
        ]:

            ms_money = MsMoney()
            ms_money.load(money_example)
            stats = ms_money.get_stats()
            if self.debug:
                stats.show()

            # Assert that the header was loaded correctly
            self.assertIsNotNone(ms_money.header)
            self.assertEqual(ms_money.header.file_type, "NOMINA-MICROSOFT-MONEY-YAML")
            self.assertEqual(ms_money.header.version, "0.1")

            graph = ms_money.graph.graph

            # Assert that the graph was populated with nodes
            self.assertGreater(len(graph.nodes), 0)

            if self.debug:
                print(f"Loaded {len(graph.nodes)} nodes into the graph")
                print(f"File name: {ms_money.header.name}")
                print(f"File date: {ms_money.header.date}")

                print()
                ms_money.graph.dump(["ACCT", "TRN", "TRN_SPLIT"])
