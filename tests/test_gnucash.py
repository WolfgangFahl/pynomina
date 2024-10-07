"""
Created on 2024-10-02

@author: wf
"""

from tests.basetest import Basetest
from tests.example_testcases import NominaExample


class Test_GnuCash(Basetest):
    """
    test GnuCash handling
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.examples = NominaExample.get_examples(do_log=debug)

    def test_gnucash_xml_read(self):
        """
        Test parsing a GnuCash XML file.
        """
        for name, example in self.examples.items():
            with self.subTest(f"Testing {name}"):
                gncv2 = example.get_parsed_gnucash()
                stats = gncv2.get_stats()
                if self.debug:
                    stats.show()
                example.check_stats(stats)

    def test_gnucash_xml_write(self):
        """
        test writing an xml file and roundtrip
        """
        for name, example in self.examples.items():
            with self.subTest(f"Testing {name}"):
                gncv2 = example.get_parsed_gnucash()
                output_file = example.write_gnucash(gncv2, "/tmp", "roundtrip")
                example.check_file(output_file)
                gncv2_out = example.gcxml.parse_gnucash_xml(output_file)
                stats = gncv2_out.get_stats()
                example.check_stats(stats)
