"""
Created on 2024-10-08

@author: wf
"""

import os
import traceback

from nomina.file_formats import AccountingFileFormats
from nomina.nomina_cmd import NominaCmd
from tests.basetest import Basetest


class TestNominaConverter(Basetest):
    """
    test the nomina command line converter
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.input_files = [
            "empty.yaml",
            "empty_xml.gnucash",
            "example.beancount",
            "expenses.qif",
            "expenses.yaml",
            "expenses2024_bzv.yaml",
            "expenses2024.yaml",
            "expenses2024_xml.gnucash",
            "expenses_xml.gnucash",
            "simple_sample.yaml",
            "simple_sample_xml.gnucash",
            # "sample_microsoft_money.zip"
        ]
        self.target_formats = [
            ("LB-YAML", ".yaml"),
            ("GC-XML", ".gnucash"),
            ("BEAN", ".beancount"),
        ]
        self.formats = AccountingFileFormats()
        self.target_dir = "/tmp/nomina"
        os.makedirs(self.target_dir, exist_ok=True)

        self.cmd = NominaCmd()

    def test_conversions(self):
        """
        test the conversions
        """
        for input_file in self.input_files:
            for target_format, ext in self.target_formats:
                with self.subTest(
                    input_file=input_file, target_format=target_format, ext=ext
                ):
                    input_path = self.examples_path + f"/{input_file}"
                    from_format = self.formats.detect_format(input_path)
                    if from_format.acronym != target_format:
                        self.run_conversion(
                            input_path, target_format=target_format, ext=ext
                        )

    def run_conversion(self, input_path, target_format: str, ext: str):
        """
        run the given conversion via command line
        """
        base_name = os.path.basename(input_path)
        name, _ = os.path.splitext(base_name)
        converted_name = f"{name}_converted{ext}"
        output_file = os.path.join(self.target_dir, converted_name)

        argv = [
            "--debug",
            "--convert",
            input_path,
            "--format",
            target_format,
            "--output",
            output_file,
        ]

        try:
            exit_code = self.cmd.cmd_main(argv)
            self.assertEqual(exit_code, 0, f"Command failed with exit code {exit_code}")
            self.assertTrue(
                os.path.exists(output_file), f"Output file not created: {output_file}"
            )
            file_size = os.path.getsize(output_file)
            self.assertGreater(
                file_size, 0, f"Output file has size {file_size}: {output_file}"
            )
        except Exception as e:
            if self.debug:
                print(traceback.format_exc())
            self.fail(
                f"Conversion failed for {input_path} to {target_format}:\n{str(e)}"
            )
