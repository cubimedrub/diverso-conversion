"""Conversion module for equi_ref blood conversion."""

from typing import Set
from logging import Logger, FileHandler
from pathlib import Path

import pandas as pd

RECRUITING_PREFIX: str = "rekrutierung_"
QUESTIONNAIRE_PREFIX: str = "befragung_"


def read_dataframe_from_file(
    file_path: Path,
    separator: str,
) -> pd.DataFrame:
    """
    Reads a DataFrame from a file based on its extension.
    Parameters
    ----------
    file_path : Path
        Path to the input file.
    separator : str
        Separator to use when reading CSV files.
    Returns
    -------
    pd.DataFrame
        DataFrame read from the file.
    """
    match file_path.suffix:
        case ".xlsx":
            return pd.read_excel(file_path, engine="openpyxl")
        case ".tsv":
            return pd.read_csv(file_path, sep="\t")
        case ".csv":
            return pd.read_csv(file_path, sep=separator)
        case _:
            raise ValueError(
                (
                    f"Unsupported patient file format: {file_path.suffix}. "
                    "Supported formats are .xlsx, .tsv, .csv"
                )
            )


def write_dataframe_to_file(
    df: pd.DataFrame,
    file_path: Path,
):
    """
    Writes a DataFrame to a file based on its extension.
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to write to the file.
    file_path : Path
        Path to the output file.
    """
    match file_path.suffix:
        case ".xlsx":
            df.to_excel(file_path, index=False)
        case ".tsv":
            df.to_csv(file_path, sep="\t", index=False)
        case ".csv":
            df.to_csv(file_path, index=False)
        case _:
            raise ValueError(
                (
                    f"Unsupported output file format: {file_path.suffix}. "
                    "Supported formats are .xlsx, .tsv, .csv"
                )
            )


def conversion(
    patient_file: Path,
    output_file: Path,
    column_whitelist: Set[str],
    patient_file_separator: str,
    logger: Logger,
):
    """
    Runs the conversion process by opening the patient file,
    indexing the genomic results files and merging the results into a new Excel file.

    Parameters
    ----------
    patient_file : Path
        Patient file containing recruiting and questionnaire data.
    output_file : Path
        Path to the output file where the merged results will be saved.
    column_whitelist : Set[str]
        List of columns to include in the output file.
    logger : Logger
        Logger instance for logging messages.
    """

    # checks
    if not patient_file.is_file():
        raise FileNotFoundError(f"Patient file {patient_file} does not exist.")

    if not output_file.parent.is_dir():
        raise NotADirectoryError(
            f"Output directory {output_file.parent} does not exist."
        )

    # attatch file handler to logger temporarily
    log_file = output_file.with_suffix(".log")
    logger.info("Logging to %s", log_file)
    logging_file_handler = FileHandler(log_file, encoding="utf-8", mode="w")
    logger.addHandler(logging_file_handler)

    try:
        df = read_dataframe_from_file(patient_file, patient_file_separator)
    except ValueError as e:
        logger.error("%s", e)
        return

    patient_ids = df["pat_id"].unique().tolist()

    updated_questionnaire_dfs = []

    for patient_id in patient_ids:
        logger.info("Processing patient ID: %s", patient_id)

        patient_df = df[df["pat_id"] == patient_id]
        recruiting_row = patient_df[
            patient_df["redcap_event_name"].str.startswith(RECRUITING_PREFIX)
        ]
        if recruiting_row.empty:
            logger.warning(
                "No recruiting data found for patient ID: %s. Skipping.", patient_id
            )
            continue

        if len(recruiting_row) > 1:
            logger.warning(
                "Multiple recruiting entries found for patient ID: %s. Using the first one.",
                patient_id,
            )

        questionnaire_df = patient_df[
            patient_df["redcap_event_name"].str.startswith(QUESTIONNAIRE_PREFIX)
        ].copy(deep=True)

        for col in questionnaire_df.columns:
            if (
                questionnaire_df[col].isnull().all()
                and not recruiting_row[col].isnull().all()
            ):
                questionnaire_df.fillna(
                    {col: recruiting_row.iloc[0][col]}, inplace=True
                )

        if len(column_whitelist) > 0:
            existing_columns = set(questionnaire_df.columns)
            columns_to_drop = existing_columns - column_whitelist
            questionnaire_df.drop(columns=columns_to_drop, inplace=True)

        updated_questionnaire_dfs.append(questionnaire_df)

    df = pd.concat(updated_questionnaire_dfs, ignore_index=True)

    # Convert height from cm to m. Considering no human is taller than 3 meters and not NaN
    if "pat_height" in df.columns:
        df["pat_height"] = df["pat_height"].apply(
            lambda x: x / 100.0 if x is not pd.NA and x > 3.0 else x
        )

    if output_file.is_file():
        existing_df = read_dataframe_from_file(output_file, ",")
        columns_of_existing_df = list(existing_df.columns)
        columns_of_existing_df.sort()
        columns_of_new_df = list(df.columns)
        columns_of_new_df.sort()
        if columns_of_existing_df != columns_of_new_df:
            logger.error(
                "The output file %s already exists and has different columns. Cannot append. Abort.",
                str(output_file),
            )
        else:
            logger.info(
                "The output file %s already exists with the same columns. Appending and remove duplicates keeping the first one.",
                str(output_file),
            )
            backup_file_suffix = output_file.suffix
            backup_file = output_file.with_suffix(f".backup.{backup_file_suffix}")
            logger.info("Backing up existing file to %s", str(backup_file))
            existing_df.to_excel(backup_file, index=False)

            df = pd.concat([existing_df, df], ignore_index=True)
            df.drop_duplicates(inplace=True)

            try:
                write_dataframe_to_file(df, output_file)
                logger.info(
                    "Appended data written to %s successfully.", str(output_file)
                )
            except ValueError as e:
                logger.error("%s", e)

    else:
        logger.info("Writing merged data to %s", str(output_file))
        try:
            write_dataframe_to_file(df, output_file)
            logger.info("Data written to %s successfully.", str(output_file))
        except ValueError as e:
            logger.error("%s", e)

    logger.info("Conversion completed successfully.")

    # Remove the file handler after logging
    logger.removeHandler(logging_file_handler)
    logging_file_handler.close()
