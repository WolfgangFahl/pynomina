"""
Created on 2024-10-06
@author: wf
"""

from dataclasses import dataclass


@dataclass
class Version(object):
    """
    Version handling for MoneyBrowser
    """

    name = "pynomina"
    version = "0.0.4"
    date = "2024-10-06"
    updated = "2024-10-09"
    description = "Personal finance tool"
    authors = "Wolfgang Fahl"

    doc_url = "https://wiki.bitplan.com/index.php/Pynomina"
    chat_url = "https://github.com/WolfgangFahl/pynomina/discussions/"
    cm_url = "https://github.com/WolfgangFahl/pynomina"

    license = f"""Copyright 2024 contributors. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied."""
    longDescription = f"""{name} version {version}
{description}

  Created by {authors} on {date} last updated {updated}"""
