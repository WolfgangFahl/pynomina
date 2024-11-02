"""
Created on 2024-11-02

@author: wf
"""

import os

import yaml
from lodstorage.query import QueryManager
from tabulate import tabulate

from nomina import beanquery_cmd
from nomina.bean_query import BeanQueryHandler
from tests.basetest import Basetest


class Test_NamedParameterizedBeanQueries(Basetest):
    """
    test named parameterized Query
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.examples_path = self.get_examples_path()
        self.example_beancount_path = os.path.join(
            self.examples_path, "example.beancount"
        )
        self.queries_yaml_path = os.path.join(self.examples_path, "queries.yaml")
        self.endpoint_yaml_path = self.create_endpoints_yaml(
            "/tmp", self.example_beancount_path
        )
        self.qm = QueryManager(
            lang="sql",
            debug=self.debug,
            queriesPath=self.queries_yaml_path,
            with_default=False,
        )

    def create_endpoints_yaml(self, yaml_path: str, examples_beancount_path):
        """
        Create endpoints.yaml on the fly for testing.
        """
        endpoints_yaml_path = str(os.path.join(yaml_path, "endpoints.yaml"))
        endpoint_data = {
            "example_beancount": {
                "database": "beancount",
                "lang": "sql",
                "endpoint": examples_beancount_path,
            }
        }
        with open(endpoints_yaml_path, "w") as f:
            yaml.dump(endpoint_data, f)
        return endpoints_yaml_path

    @classmethod
    def get_examples_path(cls) -> str:
        """
        Get the path to the nomina_examples directory.
        """
        path = os.path.join(os.path.dirname(__file__), "../nomina_examples")
        path = os.path.abspath(path)
        return path

    def test_query_via_cmd_line(self):
        """
        Test running beanquery via command line script.
        """
        args = [
            "--endpointPath",
            str(self.endpoint_yaml_path),
            "-en",
            "example_beancount",
            "--queriesPath",
            str(self.queries_yaml_path),
            "--queryName",
            "AccountSummary",
            "--params",
            "account=Expenses:Food:Groceries",
        ]
        beanquery_cmd.main(args)

    def test_query_direct(self):
        """
        Test running beanquery via direct method call.
        """
        handler = BeanQueryHandler(self.example_beancount_path)

        # Test cases with expected results for each account
        test_cases = [
            (
                "Expenses:Food:Groceries",
                {
                    "TotalSum": 1,
                    "PayeeSummary": 4,
                    "AccountSummary": 1
                }
            ),
            (
                "Expenses:Home:Rent",
                {
                    "TotalSum": 1,
                    "PayeeSummary": 1,
                    "AccountSummary": 1
                }
            ),
            (
                "Expenses:Transport:Tram",
                {
                    "TotalSum": 1,
                    "PayeeSummary": 1,
                    "AccountSummary": 1
                }
            )
        ]

        for account, expected_results in test_cases:
            with self.subTest(account=account):
                if self.debug:
                    print(f"\n=== Testing Account: {account} ===")

                for i, (qname, query) in enumerate(self.qm.queriesByName.items(), start=1):
                    with self.subTest(qname=qname):
                        params = {"account": account}
                        query = query.params.apply_parameters_with_check(params)

                        if self.debug:
                            print(f"\nQuery {i} - {qname}:")
                            print(f"{query}")

                        lod = handler.execute_query(query)

                        if self.debug and lod:
                            print("\nResults:")
                            print(tabulate(
                                lod,
                                headers="keys",
                                tablefmt="plain",
                                numalign="right",
                                floatfmt=".2f"
                            ))

                        self.assertTrue(qname in expected_results)
                        expected_len = expected_results[qname]

                        # Check that the result is not empty and contains expected data
                        self.assertIsNotNone(lod)
                        self.assertEqual(
                            len(lod),
                            expected_len,
                            f"For account {account}, query {qname}: "
                            f"expected {expected_len} results, got {len(lod)}"
                        )
