"""Command line interface"""

import argparse
from logging import Logger
from pathlib import Path

from diverso_conversion.conversion import conversion


class Cli:
    """Command line interface to run the conversion from a terminal."""

    def __init__(self, logger: Logger):
        self.logger = logger

        # Initialize the command line interface
        parser = argparse.ArgumentParser(description="EquiRef Blood Conversion CLI")
        parser.add_argument(
            "--patient-file", type=Path, help="Path to the patient file"
        )
        parser.add_argument("--output-file", type=Path, help="Path to the output file")
        parser.add_argument(
            "--column-whitelist",
            "-c",
            type=str,
            action="append",
            default=[],
            help="Path to the column whitelist file",
        )

        # Bundled app might geht some unknown args, so we parse them but ignore them
        self.args, _ = parser.parse_known_args()

    def is_complete(self) -> bool:
        """
        Returns whether all required arguments are provided.

        Returns
        -------
        bool
            True if all required arguments are provided, False otherwise.
        """
        return all(
            [
                self.args.patient_file is not None,
                self.args.output_file is not None,
            ]
        )

    def run_conversion(self):
        """
        Runs the conversion process using the provided arguments.
        """
        if not self.is_complete():
            raise ValueError("Not all required arguments are provided.")

        try:
            conversion(
                self.args.patient_file,
                self.args.output_file,
                set(self.args.column_whitelist),
                self.logger,
            )
        except (FileNotFoundError, NotADirectoryError) as e:
            self.logger.error("%s", e)
