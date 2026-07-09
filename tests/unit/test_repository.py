import copy

import pytest

from tests.data.figshare_record import FigshareTestRecord, ManchesterFigshareTestRecord

from doiggie.license import *
from doiggie_figshare.repository import (
    PUBLIC_FIGSHARE_API_BASE_URL,
    FigshareRepository,
)


def _article_details(data=None, archive_url=None):
    details = copy.deepcopy(
        FigshareTestRecord.endpoints.article_details.response if data is None else data
    )
    details.setdefault("id", int(FigshareTestRecord.article_id))
    details.setdefault("doi", FigshareTestRecord.doi)
    details.setdefault("files", [])
    if archive_url is not None:
        details["url_public_html"] = archive_url
    return details


def _details_path(version=1):
    if version is None:
        return f"/v2/articles/{FigshareTestRecord.article_id}"
    return f"/v2/articles/{FigshareTestRecord.article_id}/versions/{version}"


def _new_repo(doi=FigshareTestRecord.doi, archive_url=FigshareTestRecord.archive_url):
    return FigshareRepository(doi=doi, archive_url=archive_url)


def _institutional_details():
    return copy.deepcopy(
        ManchesterFigshareTestRecord.endpoints.article_details.response
    )


def test_sanity_checks(sanity_check_data_repo):
    sanity_check_data_repo(FigshareRepository)


def test_initialize(data_repo_tester):
    # Invalid Figshare-looking path: no article id, no request, no repository.
    data_repo_tester(
        archive_base_url="https://figshare.com"
    ).assert_repo_does_not_initialize(archive_path="/somevalue/abc")

    # Valid figshare.com URL: API confirmation initializes the repository.
    repo_tester = data_repo_tester(archive_base_url="https://figshare.com")
    with repo_tester.endpoint_mocker() as m:
        m.get(_details_path(), json=_article_details())
        repo_tester.initialize_repo(
            doi=FigshareTestRecord.doi, archive_path=FigshareTestRecord.archive_path
        )

    assert repo_tester.repo.api_base_url == PUBLIC_FIGSHARE_API_BASE_URL
    assert repo_tester.repo.article_id == FigshareTestRecord.article_id

    # Modern article URLs can carry both the article id and the record version.
    repo_tester = data_repo_tester(archive_base_url="https://figshare.com")
    with repo_tester.endpoint_mocker() as m:
        m.get(_details_path(), json=_article_details())
        repo_tester.initialize_repo(
            doi="10.6084/m9.figshare.14763051",
            archive_path="/articles/dataset/Test_data_for_the_Pooch_library/14763051/1",
        )

    assert repo_tester.repo.article_id == FigshareTestRecord.article_id
    assert repo_tester.repo.url_version == 1

    # Hosted institutional/custom domains can still use the public Figshare API.
    repo_tester = data_repo_tester(archive_base_url="https://figshare.manchester.ac.uk")
    with repo_tester.endpoint_mocker() as m:
        m.get(
            ManchesterFigshareTestRecord.endpoints.article_details.path,
            json=_institutional_details(),
        )
        repo_tester.initialize_repo(
            doi=ManchesterFigshareTestRecord.doi,
            archive_path=ManchesterFigshareTestRecord.archive_path,
        )

    assert repo_tester.repo.archive_url == ManchesterFigshareTestRecord.archive_url
    assert repo_tester.repo.article_id == ManchesterFigshareTestRecord.article_id

    # Other deployments can expose an API on a derived api.<host>/v2 URL.
    repo_tester = data_repo_tester(
        archive_base_url="https://data.example.edu",
        api_base_url="https://api.data.example.edu",
    )
    with repo_tester.endpoint_mocker(always_mock=True) as m:
        m.get(
            _details_path(),
            json=_article_details(
                archive_url="https://data.example.edu/articles/dataset/Example/14763051"
            ),
        )
        repo_tester.initialize_repo(
            doi=FigshareTestRecord.doi,
            archive_path="/articles/dataset/Example/14763051",
        )

    assert repo_tester.repo.api_base_url == "https://api.data.example.edu/v2"

    # A Figshare-shaped URL is not enough if the API does not confirm it.
    repo_tester = data_repo_tester(archive_base_url="https://not-figshare.example")
    with repo_tester.endpoint_mocker(always_mock=True) as m:
        m.get(_details_path(), status_code=404)
        repo_tester.assert_repo_does_not_initialize(
            doi=FigshareTestRecord.doi,
            archive_path="/articles/dataset/Example/14763051",
        )


def test_initialize_rejects_article_on_wrong_host(data_repo_tester):
    repo_tester = data_repo_tester(archive_base_url="https://not-figshare.example")
    with repo_tester.endpoint_mocker(always_mock=True) as m:
        m.get(_details_path(), json=_article_details())
        repo_tester.assert_repo_does_not_initialize(
            doi=FigshareTestRecord.doi,
            archive_path="/articles/dataset/Example/14763051",
        )


def test_initialize_rejects_mismatched_api_metadata(data_repo_tester):
    repo_tester = data_repo_tester(archive_base_url="https://figshare.com")
    with repo_tester.endpoint_mocker(always_mock=True) as m:
        mismatched_id = _article_details({"id": 1, "files": []})
        m.get(_details_path(), json=mismatched_id)
        repo_tester.assert_repo_does_not_initialize(
            doi=FigshareTestRecord.doi,
            archive_path=FigshareTestRecord.archive_path,
        )

    repo_tester = data_repo_tester(archive_base_url="https://figshare.com")
    with repo_tester.endpoint_mocker(always_mock=True) as m:
        mismatched_doi = _article_details(
            {"doi": "10.6084/not-this-record", "files": []}
        )
        m.get(_details_path(), json=mismatched_doi)
        repo_tester.assert_repo_does_not_initialize(
            doi=FigshareTestRecord.doi,
            archive_path=FigshareTestRecord.archive_path,
        )


def test_initialize_rejects_non_json_api_response(data_repo_tester):
    repo_tester = data_repo_tester(archive_base_url="https://figshare.com")
    with repo_tester.endpoint_mocker(always_mock=True) as m:
        m.get(_details_path(), text="this is not json")
        repo_tester.assert_repo_does_not_initialize(
            doi=FigshareTestRecord.doi, archive_path=FigshareTestRecord.archive_path
        )


def test_parse_archive_url_edge_cases():
    assert FigshareRepository._parse_archive_url("not-a-url") is None

    parsed_url = FigshareRepository._parse_archive_url(
        "https://figshare.com/article/14763051/1"
    )
    assert parsed_url.article_id == FigshareTestRecord.article_id
    assert parsed_url.version == 1

    parsed_url = FigshareRepository._parse_archive_url(
        "https://figshare.com/articles/dataset/14763051/details"
    )
    assert parsed_url.article_id == FigshareTestRecord.article_id
    assert parsed_url.version is None


def test_doi_matches_allows_missing_values():
    assert FigshareRepository._doi_matches("", FigshareTestRecord.doi)


download_url_testcases = [
    # TESTCASE 1: empty API response
    (
        _article_details({"files": []}),
        "file1",
        ValueError("File 'file1' not found in data archive."),
    ),
    # TESTCASE 2: malformed API response
    (
        _article_details(
            {
                "files": [
                    {
                        "id": 28369770,
                        "name": "tiny-data.txt",
                        "size": 59,
                        "is_link_only": False,
                        "supplied_md5": "70e2afd3fd7e336ae478b1e740a5f08e",
                        "computed_md5": "70e2afd3fd7e336ae478b1e740a5f08e",
                        "mimetype": "text/plain",
                    }
                ]
            }
        ),
        "tiny-data.txt",
        KeyError("download_url"),
    ),
    # TESTCASE 3: valid API response with valid filename
    (
        _article_details(),
        "tiny-data.txt",
        FigshareTestRecord.endpoints.article_details.response["files"][0][
            "download_url"
        ],
    ),
    # TESTCASE 4: valid API response with invalid filename
    (
        _article_details(),
        "non_existent_filename",
        ValueError("File 'non_existent_filename' not found in data archive"),
    ),
]


@pytest.mark.parametrize("details_json_resp,filename,result", download_url_testcases)
def test_download_url(data_repo_tester, details_json_resp, filename, result):
    with data_repo_tester().endpoint_mocker(always_mock=True) as m:
        m.get(_details_path(), json=details_json_resp)
        repo = _new_repo()

        if isinstance(result, Exception):
            with pytest.raises(type(result), match=str(result)):
                repo.download_url(filename)
        else:
            assert repo.download_url(filename) == result


def test_download_url_uses_latest_for_unversioned_doi(data_repo_tester):
    with data_repo_tester().endpoint_mocker(always_mock=True) as m:
        m.get(_details_path(version=None), json=_article_details())
        repo = _new_repo(doi="10.6084/m9.figshare.14763051")

        with pytest.warns(UserWarning, match="doesn't specify which version"):
            assert (
                repo.download_url("tiny-data.txt")
                == FigshareTestRecord.endpoints.article_details.response["files"][0][
                    "download_url"
                ]
            )


def test_download_url_uses_version_from_archive_url(data_repo_tester):
    archive_url = (
        "https://figshare.com/articles/dataset/Test_data_for_the_Pooch_library/"
        "14763051/1"
    )
    with data_repo_tester().endpoint_mocker(always_mock=True) as m:
        m.get(_details_path(version=1), json=_article_details())
        repo = _new_repo(doi="10.6084/m9.figshare.14763051", archive_url=archive_url)

        assert (
            repo.download_url("tiny-data.txt")
            == FigshareTestRecord.endpoints.article_details.response["files"][0][
                "download_url"
            ]
        )


def test_download_url_can_find_article_id_from_doi(data_repo_tester):
    with data_repo_tester().endpoint_mocker(always_mock=True) as m:
        m.get(
            FigshareTestRecord.endpoints.article_search.path,
            json=FigshareTestRecord.endpoints.article_search.response,
        )
        m.get(_details_path(), json=_article_details())
        repo = _new_repo(archive_url="https://figshare.com/")

        assert (
            repo.download_url("tiny-data.txt")
            == FigshareTestRecord.endpoints.article_details.response["files"][0][
                "download_url"
            ]
        )


def test_institutional_download_url_and_registry(data_repo_tester):
    repo_tester = data_repo_tester(archive_base_url="https://figshare.manchester.ac.uk")
    with repo_tester.endpoint_mocker() as m:
        m.get(
            ManchesterFigshareTestRecord.endpoints.article_details.path,
            json=_institutional_details(),
        )
        repo_tester.initialize_repo(
            doi=ManchesterFigshareTestRecord.doi,
            archive_path=ManchesterFigshareTestRecord.archive_path,
        )

    with pytest.warns(UserWarning, match="doesn't specify which version"):
        assert (
            repo_tester.repo.download_url("QubitWdiss_term2.json")
            == "https://ndownloader.figshare.com/files/63874299"
        )
    assert (
        repo_tester.repo.create_registry()["QubitWdiss_term2.json"]
        == "md5:5d8588536bdc75fa7fcbbd0d951ed963"
    )


def test_download_url_handles_api_errors(data_repo_tester):
    with data_repo_tester().endpoint_mocker(always_mock=True) as m:
        m.get(_details_path(), status_code=429, json={})
        repo = _new_repo()

        with pytest.raises(RuntimeError, match="rate-limited"):
            repo.download_url("tiny-data.txt")

    with data_repo_tester().endpoint_mocker(always_mock=True) as m:
        m.get(_details_path(), text="not json")
        repo = _new_repo()

        with pytest.raises(RuntimeError, match="decoding the JSON response"):
            repo.download_url("tiny-data.txt")


create_registry_testcases = [
    # TESTCASE 1: empty API response
    (_article_details({"files": []}), {}),
    # TESTCASE 2: malformed API response with no checksum
    (
        _article_details(
            {
                "files": [
                    {
                        "id": 28369770,
                        "name": "tiny-data.txt",
                        "size": 59,
                        "is_link_only": False,
                        "download_url": "https://ndownloader.figshare.com/files/28369770",
                        "supplied_md5": "70e2afd3fd7e336ae478b1e740a5f08e",
                        "mimetype": "text/plain",
                    }
                ]
            }
        ),
        KeyError("computed_md5"),
    ),
    # Testcase 3: with valid response and valid registry
    (
        _article_details(),
        {
            "store.zip": "md5:7008231125631739b64720d1526619ae",
            "tiny-data.txt": "md5:70e2afd3fd7e336ae478b1e740a5f08e",
        },
    ),
]


@pytest.mark.parametrize("details_json_resp,result", create_registry_testcases)
def test_create_registry(data_repo_tester, details_json_resp, result):
    with data_repo_tester().endpoint_mocker(always_mock=True) as m:
        m.get(_details_path(), json=details_json_resp)
        repo = _new_repo()

        if isinstance(result, Exception):
            with pytest.raises(type(result), match=str(result)):
                repo.create_registry()
        else:
            assert repo.create_registry() == result


licenses_testcases = [
    # TESTCASE 1: empty API response
    (_article_details({}), KeyError("license")),
    # TESTCASE 2: API response with empty License
    (_article_details({"license": {}}), list()),
    # TESTCASE 3: API response with license
    (
        _article_details(
            {
                "license": {
                    "value": 1,
                    "name": "CC BY 4.0",
                    "url": "https://creativecommons.org/licenses/by/4.0/",
                }
            }
        ),
        [
            License(
                name="CC BY 4.0",
                identifiers=[
                    LicenseIdentifier(
                        scheme=LicenseIdentifierScheme.URL,
                        value="https://creativecommons.org/licenses/by/4.0/",
                    )
                ],
            )
        ],
    ),
]


@pytest.mark.parametrize("details_json_resp,result", licenses_testcases)
def test_licenses(data_repo_tester, details_json_resp, result):
    with data_repo_tester().endpoint_mocker(always_mock=True) as m:
        m.get(_details_path(), json=details_json_resp)
        repo = _new_repo()

        if isinstance(result, Exception):
            with pytest.raises(type(result), match=str(result)):
                repo.licenses()
        else:
            assert repo.licenses() == result
