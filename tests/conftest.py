import pytest
from pooch_figshare.repository import (
    FigshareRepository,
)
from tests.data.figshare_record import FigshareTestRecord

pytest_plugins = ["pooch_doi.testkit"]


@pytest.fixture
def data_repo_tester(create_data_repo_tester_type):
    return create_data_repo_tester_type(
        FigshareRepository,
        archive_base_url_fallback="https://figshare.com/",
        api_base_url_fallback="https://api.figshare.com",
    )


""" @pytest.fixture
def create_initialized_data_repo_tester(data_repo_tester):
    def _func(article_id):
        instance = data_repo_tester()
        with instance.endpoint_mocker() as m:
            m.get(
                f"/api/article/{article_id!s}/files",
                json=FigshareTestRecord.endpoints.article_details.response,
            )
            instance.initialize_repo("doi", f"/article/{article_id}")
        return instance

    return _func """
