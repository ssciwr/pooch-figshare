import pytest

from tests.data.figshare_record import FigshareTestRecord

from pooch_doi.license import *
from pooch_figshare.repository import FigshareRepository


def test_sanity_checks(sanity_check_data_repo):
    sanity_check_data_repo(FigshareRepository)

def test_initialize(data_repo_tester):
    # TESTCASE 1: With invalid archive_path but valid base url -> repo gets initialized
    data_repo_tester(base_url="https://figshare.com").assert_repo_does_initialize(archive_path="/somevalue/abc")

    # TESTCASE 2: With invalid archive_path and invalid base url -> repo doesnt get initialized
    data_repo_tester(base_url="https://figggshare.com").assert_repo_does_not_initialize(archive_path="/somevalue/abc")

download_url_testcases = [
    # TESTCASE 1: empty API response
    (
        True,
        FigshareTestRecord.endpoints.article_search.response,
        {"files": []},
        "file1",
        ValueError(f"File 'file1' not found in data archive {FigshareTestRecord.archive_url} (doi:{FigshareTestRecord.doi})."),
    ),
    # TESTCASE 2: malformed API response
    (
        True,
        FigshareTestRecord.endpoints.article_search.response,
        { # fake article_details response
            "files": [
                {
                    "id": 28369770,
                    "name": "tiny-data.txt",
                    "size": 59,
                    "is_link_only": False,
                    "supplied_md5": "70e2afd3fd7e336ae478b1e740a5f08e",
                    "computed_md5": "70e2afd3fd7e336ae478b1e740a5f08e",
                    "mimetype": "text/plain"
                }
            ]
        },
        "tiny-data.txt",
        KeyError("download_url"),
    ),
    # TESTCASE 2.5: malformed article_search response
    # what happens with artile_search respones has no "id" key
    # TESTCASE 3: valid API response with valid filename
    (
        False,
        FigshareTestRecord.endpoints.article_search.response,
        FigshareTestRecord.endpoints.article_details.response,
        "tiny-data.txt",
        FigshareTestRecord.endpoints.article_details.response["files"][0]["download_url"],
    ),
    # TESTCASE 4: valid API response with invalid filename
    (
        False,
        FigshareTestRecord.endpoints.article_search.response,
        FigshareTestRecord.endpoints.article_details.response,
        "non_existent_filename",
        ValueError("File 'non_existent_filename' not found in data archive"),
    ),
]


@pytest.mark.parametrize(
    "always_mock,search_json_resp,details_json_resp,filename,result", download_url_testcases
)
def test_download_url(
    data_repo_tester, always_mock, search_json_resp, details_json_resp, filename, result
):
    repo_tester = data_repo_tester()
    with repo_tester.endpoint_mocker(always_mock=always_mock) as m:
        # mock article_search endpoint to return json_resp
        m.get(FigshareTestRecord.endpoints.article_search.path, json=search_json_resp)
        m.get(FigshareTestRecord.endpoints.article_details.path, json=details_json_resp)
        repo_tester.initialize_repo(doi="doi", archive_path=FigshareTestRecord.archive_path)
        if isinstance(result, Exception):
            with pytest.raises(type(result), match=str(result)):
                repo_tester.repo.download_url(filename)
        else:
            assert repo_tester.repo.download_url(filename) == result

