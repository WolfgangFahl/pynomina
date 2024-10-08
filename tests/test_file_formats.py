"""
Created on 2024-10-06

@author: wf
"""

import os

from nomina.file_formats import AccountingFileFormats
from tests.basetest import Basetest


class Test_FileformatDetector(Basetest):
    """
    test fileformat detection
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.detector = AccountingFileFormats()

    def yield_filenames(self):
        """
        Generator that yields all filenames in the examples directory
        """
        for root, _, files in os.walk(self.examples_path):
            for file in files:
                yield os.path.join(root, file)

    def test_detect_formats(self):
        """
        Test the detection of file formats for all files in the examples directory
        """
        expected_results = {
            "expenses2024.yaml": "LB-YAML",
            "empty.yaml": "LB-YAML",
            "expenses_sqlite.gnucash": "GC-SQLITE",
            "simple_sample_xml.gnucash": "GC-XML",
            "expenses.qif": "QIF",
            "simple_sample.yaml": "LB-YAML",
            "expenses_xml.gnucash": "GC-XML",
            "expenses2024_xml.gnucash": "GC-XML",
            "empty_sqlite.gnucash": "GC-SQLITE",
            "expenses.yaml": "LB-YAML",
            "example.beancount": "BEAN",
            "FMQifTest2023-10-18.qif": "FMD",
            # "ledger.puml": None,
            "empty_xml.gnucash": "GC-XML",
            "expenses2024_bzv.yaml": "BZV-YAML",
        }
        detected_formats = {}

        for file_path in self.yield_filenames():
            detected_format = self.detector.detect_format(file_path)
            file_name = os.path.basename(file_path)

            if detected_format:
                detected_formats[file_name] = detected_format.name
                if self.debug:
                    print(f"File: {file_name}, Detected Format: {detected_format.name}")
            else:
                if self.debug:
                    print(f"File: {file_name}, Format: Unknown")

            if file_name in expected_results:
                expected_format = expected_results[file_name]
                self.assertEqual(
                    detected_format.acronym, expected_format, f"{file_name}"
                )

        # Assert that we detected at least 14 files
        self.assertGreaterEqual(len(detected_formats), 14)
