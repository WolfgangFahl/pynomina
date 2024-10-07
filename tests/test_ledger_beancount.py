"""
Created on 2024-10-07

@author: wf
"""

import os

from nomina.beancount import Beancount
from nomina.beancount_ledger import (
    BeancountToLedgerConverter,
    LedgerToBeancountConverter,
)
from tests.basetest import Basetest
from tests.example_testcases import NominaExample


class Test_LedgerBeancount(Basetest):
    """
    test Beancount handling
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.examples = NominaExample.get_examples()

    def test_beancount2ledger(self):
        """
        test converting beancount format to ledger
        """
        bc_example = self.examples_path + "/example.beancount"
        converter = BeancountToLedgerConverter(bc_example)
        ledger_book = converter.convert_to_ledger_book()
        stats = ledger_book.get_stats()
        print(stats)

    def test_ledger2beancount(self):
        """
        test converting ledger format to Beancount
        """
        for name, example in self.examples.items():
            with self.subTest(f"Testing {name}"):
                if self.debug:
                    print(f"loading ledger book {name} from yaml")
                ledger_book = example.get_ledger_book()

                if self.debug:
                    print(f"converting ledger book {name} to Beancount")
                l2b = LedgerToBeancountConverter(ledger_book)
                beancount_output = l2b.convert()

                if self.debug:
                    print(f"writing Beancount file for {name} to /tmp")
                output_path = os.path.join("/tmp", f"{name}_l2b.beancount")
                with open(output_path, "w") as f:
                    f.write(beancount_output)

                # Verify the conversion
                self.assertIsNotNone(beancount_output)
                self.assertGreater(len(beancount_output), 0)

                # Parse the Beancount output to ensure it's valid
                beancount = Beancount()
                beancount.load_string(beancount_output)
                error_count = len(beancount.errors)
                if error_count > 0 and self.debug:
                    for i, error in enumerate(beancount.errors):
                        print(f"{i:3}:{error}")
                self.assertEqual(
                    error_count,
                    0,
                    f"Errors in Beancount conversion for {name}: {beancount.errors}",
                )

                # Compare statistics
                ledger_stats = ledger_book.get_stats()
                beancount_stats = beancount.get_stats()

                # Use the check_stats method from NominaExample
                example.check_stats(beancount_stats, ledger_stats)
