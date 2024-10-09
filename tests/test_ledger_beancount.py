"""
Created on 2024-10-07

@author: wf
"""

import os
from pathlib import Path

from nomina.beancount_ledger import (
    BeancountToLedgerConverter,
    LedgerToBeancountConverter,
)
from nomina.nomina_beancount import Beancount
from nomina.stats import Stats
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
        converter = BeancountToLedgerConverter(debug=self.debug)
        beancount = converter.load(bc_example)
        self.assertIsInstance(beancount, Beancount)
        ledger_book = converter.convert_to_target()
        stats = ledger_book.get_stats()
        if self.debug:
            stats.show()
        example = NominaExample(
            name="example",
            owner="John Doe",
            url=None,
            example_path=Path(self.examples_path),
            do_log=True,
            expected_stats=Stats(
                accounts=63,
                transactions=966,
                start_date="2022-01-01",
                end_date="2024-10-04",
                currencies={
                    "EUR": 18,
                    "USD": 31,
                    "IRAUSD": 5,
                    "ITOT": 1,
                    "VEA": 1,
                    "VHT": 1,
                    "GLD": 1,
                    "VBMPX": 1,
                    "RGAGX": 1,
                    "VACHR": 3,
                },
            ),
        )
        wrong = example.check_stats(stats)
        self.assertEqual(0, wrong)

    def test_ledger2beancount(self):
        """
        test converting ledger format to Beancount
        """
        for name, example in self.examples.items():
            with self.subTest(f"Testing {name}"):
                l2b = LedgerToBeancountConverter()
                ledger_book = l2b.load(example.ledger_file)
                output_path = os.path.join("/tmp", f"{name}_l2b.beancount")
                beancount = l2b.convert_from_ledger(ledger_book)
                with open(output_path, "w") as bean_file:
                    output_text = l2b.to_text()
                    bean_file.write(output_text)
                if self.debug:
                    l2b.show_stats()
                # Verify the conversion
                self.assertIsNotNone(output_text)
                self.assertGreater(len(output_text), 0)

                # Parse the Beancount output to ensure it's valid
                beancount = Beancount()
                beancount.load_string(output_text)
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
                ledger_stats = l2b.source.get_stats()
                beancount_stats = beancount.get_stats()

                # Use the check_stats method from NominaExample
                example.check_stats(beancount_stats, ledger_stats)
