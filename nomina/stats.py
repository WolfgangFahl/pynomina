"""
Created on 2024-10-06

@author: wf
"""

from dataclasses import field
from typing import Any, Dict, Optional

from lodstorage.yamlable import lod_storable


@lod_storable
class Stats:
    """
    Ledger statistics
    """

    accounts: int
    transactions: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    classes: Optional[int] = None
    categories: Optional[int] = None
    errors: Optional[int] = None
    other: Optional[Dict[str, Any]] = field(default_factory=dict)
