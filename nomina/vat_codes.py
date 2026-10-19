"""
Created on 2026-10-19

@author: wf

VAT codes as found in Finanzmanager Deluxe QIF exports, see issue #16
"""

import os
import re
from dataclasses import field
from typing import ClassVar, Dict, List, Optional, Tuple

from basemkit.yamlable import lod_storable


@lod_storable
class VatRate:
    """
    a VAT rate with its validity period
    """

    rate: Optional[float] = None  # percent, None if the split carries the tax only
    valid_from: Optional[str] = None  # ISO date
    valid_until: Optional[str] = None  # ISO date


@lod_storable
class VatCode:
    """
    a VAT code e.g. N1 with its rates
    """

    code: str
    description: Optional[str] = ""
    rates: List[VatRate] = field(default_factory=list)

    def rate_for(self, isodate: Optional[str]) -> Optional[VatRate]:
        """
        get the rate valid at the given ISO date

        Args:
            isodate: the ISO date to check, None for the first rate

        Returns:
            Optional[VatRate]: the matching rate or None
        """
        vat_rate = None
        for candidate in self.rates:
            after_start = (
                isodate is None
                or candidate.valid_from is None
                or candidate.valid_from <= isodate
            )
            before_end = (
                isodate is None
                or candidate.valid_until is None
                or isodate <= candidate.valid_until
            )
            if vat_rate is None and after_start and before_end:
                vat_rate = candidate
        return vat_rate


@lod_storable
class VatCodes:
    """
    configurable map of VAT codes
    """

    name: Optional[str] = None
    codes: Dict[str, VatCode] = field(default_factory=dict)

    # QIF class markup e.g. _VATCode_N1_I - I: input tax, O: output VAT
    PATTERN: ClassVar[re.Pattern] = re.compile(
        r"^_VATCode_(?P<code>\w+?)_(?P<dir>[IO])$"
    )

    @classmethod
    def default_path(cls) -> str:
        """
        get the path of the default VAT code map

        Returns:
            str: the path of vat_codes.yaml in nomina_examples
        """
        path = os.path.join(
            os.path.dirname(__file__), "../nomina_examples/vat_codes.yaml"
        )
        path = os.path.abspath(path)
        return path

    @classmethod
    def of_yaml(cls, yaml_path: Optional[str] = None) -> "VatCodes":
        """
        load the VAT codes

        Args:
            yaml_path: the path of the yaml file, None for the default map

        Returns:
            VatCodes: the loaded VAT code map
        """
        if yaml_path is None:
            yaml_path = cls.default_path()
        vat_codes = cls.load_from_yaml_file(yaml_path)
        return vat_codes

    @classmethod
    def parse(cls, markup: Optional[str]) -> Optional[Tuple[str, str]]:
        """
        parse the given QIF class markup

        Args:
            markup: the class markup e.g. _VATCode_N1_I

        Returns:
            Optional[Tuple[str, str]]: code and direction or None if the markup is no VAT code
        """
        parsed = None
        if markup:
            match = cls.PATTERN.match(markup)
            if match:
                parsed = (match.group("code"), match.group("dir"))
        return parsed

    def lookup(self, code: str) -> Optional[VatCode]:
        """
        lookup the given VAT code

        Args:
            code: the code e.g. N1

        Returns:
            Optional[VatCode]: the VAT code or None if unknown
        """
        vat_code = self.codes.get(code)
        return vat_code
