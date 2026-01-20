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

