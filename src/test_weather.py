"""
Testing basic properties of the database

"""

import pandas as pd
import pytest


@pytest.fixture
def test_data():
    """

    :return:
    """
    with open(
        "data/rawdata/weatherdata.csv", encoding="utf8", errors="ignore", newline=""
    ) as file:
        df_weather = pd.read_csv(file, sep=",")
    return df_weather


def test_unique_records_per_city_per_day(test_data):  # pylint: disable=W0621
    """
    Test to ensure that for each city, there is only one record per day.
    """
    grouped = test_data.groupby(["City", "time"]).size().reset_index(name="counts")

    duplicates = grouped[grouped["counts"] > 1]

    # Assert that there are no duplicates
    assert duplicates.empty, f"Found duplicate records: {duplicates}"


def test_tavg_value_constraints(test_data):  # pylint: disable=W0621
    """
    Test to ensure that the 'tavg' column does not contain values greater
    than 42 or less than -42 (lowest and highest temperatures recorded in Poland).
    """
    tavg_above_42 = test_data[test_data["tavg"] > 42]
    assert tavg_above_42.empty, f"Found 'tavg' values greater than 42: {tavg_above_42}"

    tavg_below_neg_42 = test_data[test_data["tavg"] < -42]
    assert (
        tavg_below_neg_42.empty
    ), f"Found 'tavg' values less than -42: {tavg_below_neg_42}"


def test_no_missing_values(test_data):  # pylint: disable=W0621
    """
    Test to ensure there are no missing values in used columns.
    """
    critical_columns = ["City", "time", "tavg", "wspd", "pres", "prcp"]
    missing_values = test_data[critical_columns].isnull().sum()

    for col, count in missing_values.items():
        assert count == 0, f"Column {col} has {count} missing values"


def test_data_types(test_data):  # pylint: disable=W0621
    """
    Test to ensure that each column has the correct data type.
    """
    expected_dtypes = {
        "City": "object",
        "tavg": "float64",
        "wspd": "float64",
        "pres": "float64",
        "prcp": "float64",
    }

    for column, expected_dtype in expected_dtypes.items():
        assert (
            test_data[column].dtype == expected_dtype
        ), f"Column {column} is not of type {expected_dtype}"


if __name__ == "__main__":
    pytest.main()
