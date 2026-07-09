import pytest
from doiggie_figshare.repository import (
    FigshareRepository,
    KnownInstancesFigshareRepository,
)

pytest_plugins = ["doiggie.testkit"]


@pytest.fixture
def data_repo_tester(create_data_repo_tester_type):
    return create_data_repo_tester_type(
        FigshareRepository,
        archive_base_url_fallback="https://figshare.com/",
        api_base_url_fallback="https://api.figshare.com",
    )


@pytest.fixture(scope="session")
def known_instances_data_repo_tester(create_data_repo_tester_type):
    return create_data_repo_tester_type(KnownInstancesFigshareRepository)
