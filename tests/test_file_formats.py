"""
Created on 2024-10-06

@author: wf
"""

import os

from nomina.file_formats import AccountingFileFormatDetector
from tests.basetest import Basetest


class Test_FileformatDetector(Basetest):
    """
    test fileformat detection
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.examples_path = os.path.join(
            os.path.dirname(__file__), "../nomina_examples"
        )
        self.detector = AccountingFileFormatDetector()

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
            # "empty.yaml": None,
            # "expenses_sqlite.gnucash": None,
            "simple_sample_xml.gnucash": "GC-XML",
            "expenses.qif": "QIF",
            # "simple_sample.yaml": None,
            "expenses_xml.gnucash": "GC-XML",
            "expenses2024_xml.gnucash": "GC-XML",
            # "empty_sqlite.gnucash": None,
            "expenses.yaml": "LB-YAML",
            # "ledger.puml": None,
            "empty_xml.gnucash": "GC-XML",
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

        # Assert that we detected at least one file
        self.assertGreater(len(detected_formats), 0, "No files were detected")
