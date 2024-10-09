# pynomina
personal accounting tool with file conversion

[![Join the discussion at https://github.com/WolfgangFahl/pynomina/discussions](https://img.shields.io/github/discussions/WolfgangFahl/pynomina)](https://github.com/WolfgangFahl/pynomina/discussions)
[![pypi](https://img.shields.io/pypi/pyversions/pynomina)](https://pypi.org/project/pynomina/)
[![Github Actions Build](https://github.com/WolfgangFahl/pynomina/actions/workflows/build.yml/badge.svg)](https://github.com/WolfgangFahl/pynomina/actions/workflows/build.yml)
[![PyPI Status](https://img.shields.io/pypi/v/pynomina.svg)](https://pypi.python.org/pypi/pynomina/)
[![GitHub issues](https://img.shields.io/github/issues/WolfgangFahl/pynomina.svg)](https://github.com/WolfgangFahl/pynomina/issues)
[![GitHub closed issues](https://img.shields.io/github/issues-closed/WolfgangFahl/pynomina.svg)](https://github.com/WolfgangFahl/pynomina/issues/?q=is%3Aissue+is%3Aclosed)
[![API Docs](https://img.shields.io/badge/API-Documentation-blue)](https://WolfgangFahl.github.io/pynomina/)
[![License](https://img.shields.io/github/license/WolfgangFahl/pynomina.svg)](https://www.apache.org/licenses/LICENSE-2.0)
## Introduction
pynomina is intended as a personal accounting swiss army knife

## Demo
[Demo](http://nomina.bitplan.com/)

## Motivation
In the past decades the author used different personal accounting tools:
* [Quicken](https://en.wikipedia.org/wiki/Quicken)
* [Microsoft Money](https://en.wikipedia.org/wiki/Microsoft_Money)
* [Lexware Finanzmanager](https://www.wikidata.org/wiki/Q1822341)
* [BankingZV](https://www.wikidata.org/wiki/Q130438296)

the [pain](https://wiki.bitplan.com/index.php/IT_Pain_Scale) the conversion between those tools created was finally big enough to do something about it.

## Goals
* use a computer and human readable ledger format that is ready to survive decades
* convert from and to the formats of the tool of choice
* allow for simple sanity checks and reports
* allow for systematic tidy up
* allow for integration into a larger organizational knowledge graph

## Docs and Tutorials
[Wiki](https://wiki.bitplan.com/index.php/pynomina)

## Hub & Spoke Conversion

The pyNomina tool follows a **Hub and Spoke** model for
conversion between different personal accounting file formats. The **Ledger Book (YAML/JSON)** format acts as the hub, with each supported format serving as a spoke.
This setup simplifies conversions by allowing data to be transformed from
any spoke to the hub and then to any other spoke format.

![Hub and Spoke Diagram](https://diagrams.bitplan.com/render/png/0xa0be5aae.png)

### Supported Formats

| Format                         | Type         | Description                                                | Wikidata Entry                                                      |
|--------------------------------|--------------|------------------------------------------------------------|---------------------------------------------------------------------|
| **Ledger Book YAML/JSON**      | **Hub**      | Main format of pyNomina for converting between formats.    | [Ledger Book](https://www.wikidata.org/wiki/Q281876)                |
| **Beancount**                  | Spoke        | A plaintext accounting format.                             | [Beancount](https://www.wikidata.org/wiki/Q130456404)               |
| **GnuCash XML**                | Spoke        | An XML-based format used by GnuCash.                       | [GnuCash](https://www.wikidata.org/wiki/Q130445392)                 |
| **Microsoft Money**            | Spoke        | Zip File exported with mny_export script using mdb-tools   | [Microsoft Money](https://www.wikidata.org/wiki/Q117428)            |
| **Finanzmanager Deluxe (QIF)** | Spoke        | A variant of QIF used by Finanzmanager Deluxe.             | [Finanzmanager Deluxe](https://www.wikidata.org/wiki/Q1822341)      |
| **Quicken Interchange Format** | Spoke        | Quicken Interchange Format (QIF)                           | [Quicken](https://www.wikidata.org/wiki/Q750657)                    |
| **pyNomina Banking ZV YAML**   | Spoke        | A format for exporting banking data in YAML or JSON.       | [Banking ZV](https://www.wikidata.org/wiki/Q130438296)              |


### Structure

#### Ledger-Book Hub Structure
![ledger module Class Diagram](https://diagrams.bitplan.com/render/png/0xfec2cab6.png)


### Authors
* [Wolfgang Fahl](http://www.bitplan.com/Wolfgang_Fahl)

