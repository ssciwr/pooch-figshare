import pytest
from pooch_figshare.repository import (
    FigshareRepository,
)
from tests.data.figshare_record import FigshareTestRecord

pytest_plugins = ["pooch_doi.test_utils"]

@pytest.fixture
def data_repo_tester(create_data_repo_tester_type):
    return create_data_repo_tester_type(
        FigshareRepository, base_url_fallback="https://figshare.com"
    )
