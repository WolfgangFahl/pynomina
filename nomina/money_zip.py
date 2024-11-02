"""
Created on 2024-10-14

@author: wf
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from datetime import datetime

import yaml


class MnyToZipConverter:
    """
    Convert Microsoft Money Files to ZIP file with JSON dumps of all tables
    and a header YAML file
    """

    # Color definitions
    BLUE = "\033[0;34m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    END_COLOR = "\033[0m"

    # Default values
    VERSION = "0.0.2"

    def __init__(self):
        self.debug = False
        self.verbose = False
        self.keep_temp = False
        self.output_dir = None

    def color_msg(self, color, msg):
        """Display colored messages with UTF-8 symbols."""
        print(f"{color}{msg}{self.END_COLOR}")

    def error(self, msg):
        """Display errors and exit."""
        self.color_msg(self.RED, f"✖ {msg}")
        sys.exit(1)

    def positive(self, msg):
        """Display positive messages."""
        self.color_msg(self.GREEN, f"✔ {msg}")

    def negative(self, msg):
        """Display negative messages."""
        self.color_msg(self.RED, f"✖ {msg}")

    def check_tools(self):
        """Check if required tools are available."""
        tools = ["mdb-ver", "mdb-tables", "mdb-json"]
        ok = True
        for tool in tools:
            if shutil.which(tool):
                self.positive(f"{tool} is available")
            else:
                self.negative(f"{tool} is not installed or not found in PATH")
                ok = False
        if not ok:
            self.negative(
                "You might want to install https://github.com/mdbtools/mdbtools on your system"
            )

    def create_yaml_declaration(self, mny_file, yaml_file):
        """Create YAML declaration file."""
        try:
            mdb_ver = subprocess.check_output(
                ["mdb-ver", mny_file], universal_newlines=True
            ).strip()
            file_date = datetime.fromtimestamp(os.path.getmtime(mny_file)).isoformat()
            file_size = os.path.getsize(mny_file)

            with open(mny_file, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()

            yaml_data = {
                "file_type": "NOMINA-MICROSOFT-MONEY-YAML",
                "version": "0.1",
                "name": mny_file,
                "date": file_date,
                "size": file_size,
                "sha256": file_hash,
                "jetversion": mdb_ver,
            }

            self.color_msg(self.BLUE, f"{yaml_file} ...")
            with open(yaml_file, "w") as f:
                yaml.dump(yaml_data, f)

        except subprocess.CalledProcessError:
            self.error("YAML creation failed")

    def export_tables_to_json(self, mny_file, output_dir):
        """Export tables of the given Microsoft Money file to JSON files."""
        tables = subprocess.check_output(
            ["mdb-tables", "-1", mny_file], universal_newlines=True
        ).split()

        for table in tables:
            json_file = os.path.join(output_dir, f"{table}.json")
            self.color_msg(self.BLUE, f"{table} ...")
            msg = f"{table} → {json_file}"

            try:
                with open(json_file, "w") as f:
                    subprocess.run(["mdb-json", mny_file, table], stdout=f, check=True)

                if os.path.getsize(json_file) > 0:
                    self.positive(msg)
                else:
                    raise subprocess.CalledProcessError(1, "mdb-json")

            except subprocess.CalledProcessError:
                self.negative(msg)
                if os.path.exists(json_file):
                    os.remove(json_file)

    def export_mny_to_zip(self, mny_file) -> str:
        """Export the given money file to a zip file that pynomina might be able to read."""
        basename = os.path.splitext(os.path.basename(mny_file))[0]
        if self.output_dir is None:
            self.output_dir = f"/tmp/{basename}_mdb_dump"
        zip_file = f"{basename}.zip"
        yaml_file = os.path.join(self.output_dir, "nomina.yaml")

        try:
            os.makedirs(self.output_dir, exist_ok=True)
            self.create_yaml_declaration(mny_file, yaml_file)
            self.export_tables_to_json(mny_file, self.output_dir)

            self.color_msg(self.BLUE, "→ Creating zip archive...")
            shutil.make_archive(basename, "zip", self.output_dir)

            if not self.keep_temp:
                shutil.rmtree(self.output_dir)
            else:
                self.positive(f"Temporary files kept in {self.output_dir}")

            self.positive(f"Conversion complete. Output file: {zip_file}")

        except Exception as e:
            self.error(f"Failed to create zip archive: {str(e)}")
        return zip_file

    def run(self):
        parser = argparse.ArgumentParser(
            description="Convert Microsoft Money files to ZIP"
        )
        parser.add_argument(
            "-ct",
            "--checktools",
            action="store_true",
            help="Check if required tools are installed",
        )
        parser.add_argument(
            "-d", "--debug", action="store_true", help="Enable debug output"
        )
        parser.add_argument(
            "--keep",
            action="store_true",
            help="Keep the temporary files after conversion",
        )
        parser.add_argument(
            "--version", action="version", version=f"Version: {self.VERSION}"
        )
        parser.add_argument(
            "-o",
            "--output",
            help="Specify the output directory - default: /tmp/[basename]_money_dump",
        )
        parser.add_argument(
            "mny_file", nargs="?", help="Microsoft Money file to convert"
        )

        args = parser.parse_args()

        self.debug = args.debug
        self.keep_temp = args.keep
        self.output_dir = args.output

        if args.checktools:
            self.check_tools()
        elif args.mny_file:
            if not args.mny_file.endswith(".mny"):
                self.error("Input file must have .mny extension")
            self.export_mny_to_zip(args.mny_file)
        else:
            parser.print_help()


def main():
    converter = MnyToZipConverter()
    converter.run()


if __name__ == "__main__":
    main()
