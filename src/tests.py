"""
Testing basic properties of the database

"""

import pandas as pd
import pytest
import helpers as hp


@pytest.fixture
def test_data():
    """
    Getting data for test.
    """
    return hp.get_data(30)


def test_unique_records_per_city_per_day(test_data):
    """
    Test to ensure that for each city, there is only one record per day.
    """
    grouped = test_data.groupby(["City", "time"]).size().reset_index(name="counts")

    duplicates = grouped[grouped["counts"] > 1]

    # Assert that there are no duplicates
    assert duplicates.empty, f"Found duplicate records: {duplicates}"


def test_tavg_value_constraints(test_data):
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


def test_no_missing_values(test_data):
    """
    Test to ensure there are no missing values in used columns.
    """
    critical_columns = ["City", "time", "tavg", "wspd", "pres", "prcp"]
    missing_values = test_data[critical_columns].isnull().sum()

    for col, count in missing_values.items():
        assert count == 0, f"Column {col} has {count} missing values"


def test_data_types(test_data):
    """
    Test to ensure that each column has the correct data type.
    """
    expected_dtypes = {
        "City": "object",
        "time": "datetime64[ns]",
        "tavg": "float64",
        "wspd": "float64",
        "pres": "float64",
        "prcp": "float64",
    }

    for column, expected_dtype in expected_dtypes.items():
        assert (
            test_data[column].dtype == expected_dtype
        ), f"Column {column} is not of type {expected_dtype}"


def test_dates_within_range(test_data):
    """
    Test to ensure that all dates are within the specified DATE_RANGE days from today.
    """
    max_date = pd.to_datetime("today")
    min_date = max_date - pd.Timedelta(days=hp.DATE_RANGE)
    dates_out_of_range = test_data[~test_data["time"].between(min_date, max_date)]

    assert (
        dates_out_of_range.empty
    ), f"Found dates out of the specified range: {dates_out_of_range['time'].unique()}"


if __name__ == "__main__":
    pytest.main()
