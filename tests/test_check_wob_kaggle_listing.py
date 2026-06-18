from scripts.check_wob_kaggle_listing import (
    NORMAL_SLUG,
    TEST_SLUG,
    compute_listing_report,
    parse_kaggle_files_csv,
)


def test_parse_kaggle_files_csv_ignores_page_token():
    rows = parse_kaggle_files_csv(
        "Next Page Token = abc\nname,size,creationDate\nNORMAL-TRAIN/ep-0000/ep-0000.tar,10,2022-01-01\n"
    )
    assert rows == [
        {
            "name": "NORMAL-TRAIN/ep-0000/ep-0000.tar",
            "size": "10",
            "creationDate": "2022-01-01",
        }
    ]


def test_compute_listing_report_counts_nonlocked_rows():
    rows = [
        {"source": "NORMAL-TRAIN/ep-0000/ep-0000.tar", "split": "train"},
        {"source": "TEST/BlackScreen/ep-0000/ep-0000.tar", "split": "validation"},
    ]
    report = compute_listing_report(
        rows,
        normal_listing=[{"name": "NORMAL-TRAIN/ep-0000/ep-0000.tar", "size": "100"}],
        test_listing=[{"name": "TEST/BlackScreen/ep-0000/ep-0000.tar", "size": "200"}],
        locked_rows_in_split_csv=59,
    )
    assert report["official_sources"]["normal_dataset"] == NORMAL_SLUG
    assert report["official_sources"]["test_dataset"] == TEST_SLUG
    assert report["resolved_nonlocked_rows"] == 2
    assert report["missing_nonlocked_rows"] == 0
    assert report["total_nonlocked_bytes"] == 300
    assert report["kaggle_native_status"] == "READY_FOR_KAGGLE_WOB_P0"


def test_compute_listing_report_flags_missing_rows():
    rows = [{"source": "TEST/BlackScreen/ep-0001/ep-0001.tar", "split": "validation"}]
    report = compute_listing_report(
        rows,
        normal_listing=[],
        test_listing=[],
        locked_rows_in_split_csv=59,
    )
    assert report["resolved_nonlocked_rows"] == 0
    assert report["missing_nonlocked_rows"] == 1
    assert report["kaggle_native_status"] == "BLOCKED_KAGGLE_INPUT_SETUP"
