"""Conversion tool for equi ref blood project."""

import logging

from diverso_conversion.cli import Cli
from diverso_conversion.gui import Gui

LOGGER_NAME = "equi_ref_blood_conversion"


def main():
    """Main function to run the EquiRef Blood Conversion application."""

    # Set up logging
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logging_terminal_handler = logging.StreamHandler()
    logger.addHandler(logging_terminal_handler)

    cli = Cli(logger)
    if cli.is_complete():
        cli.run_conversion()
    else:
        _ = Gui(logger)

    # exit()


if __name__ in "__main__":
    main()
