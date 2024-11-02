"""
Created on 2024-10-10

@author: wf
"""

from nomina.nomina_beancount import Beancount
from tests.basetest import Basetest


class Test_Beancount(Basetest):
    """
    test Beancount handling
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_sanitize_account_names(self):
        """
        test sanitizing account names
        """
        beancount = Beancount()
        for fq_name, expected_sanitized in [
            ("Assets:[Cash]", "Assets:Cash"),
            ("Expense:4240-Gas,-Strom,-Wasser", "Expense:4240-Gas--Strom--Wasser"),
            (
                "4660-Reisekosten-Arbeitnehmer:Auto-0.52",
                "4660-Reisekosten-Arbeitnehmer:Auto-0-52",
            ),
            ("3300-Wareneinkauf-7%", "3300-Wareneinkauf-7-"),
            ("4610-Werbung:newsletter", "4610-Werbung:Newsletter"),
        ]:
            sanitized = beancount.sanitize_account_name(fq_name)
            self.assertEqual(expected_sanitized, sanitized)
