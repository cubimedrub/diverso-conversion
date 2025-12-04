# DiVerso file conversion

1. Merges the survey rows with the recruitment rows for each patient. Removing the recruitment rows and keeping the survey rows.
2. Converts the `pat_height` column from centimeters to meter. Assuming no human is taller than 3.0 meters and not NaN.
3. If the output file alredy exists, it is merged with the newly generated data, if the the whitelisted colums match. 