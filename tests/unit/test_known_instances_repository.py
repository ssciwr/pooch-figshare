import pooch_figshare.repository as repository
from pooch_figshare import KnownInstancesFigshareRepository
from tests.data.figshare_record import FigshareTestRecord, ManchesterFigshareTestRecord


def test_sanity_checks(sanity_check_data_repo):
    sanity_check_data_repo(KnownInstancesFigshareRepository)


def test_known_figshare_instances_parser(monkeypatch):
    class _InstancesFile:
        def read_text(self, encoding):
            assert encoding == "utf-8"
            return (
                "# Comment lines are ignored\n"
                "\n"
                "https://data.example.edu https://api.data.example.edu/v2\n"
                "https://public.example.edu\n"
            )

    class _PackageFiles:
        def joinpath(self, filename):
            assert filename == "instances.txt"
            return _InstancesFile()

    repository._known_figshare_instances.cache_clear()
    monkeypatch.setattr(repository, "files", lambda package: _PackageFiles())

    try:
        assert repository._known_figshare_instances() == {
            "https://data.example.edu": "https://api.data.example.edu/v2",
            "https://public.example.edu": "https://api.figshare.com/v2",
        }
    finally:
        repository._known_figshare_instances.cache_clear()


def test_initialize(known_instances_data_repo_tester, monkeypatch):
    # TESTCASE 1: With invalid domain and invalid archive_path -> invalid archive_url
    known_instances_data_repo_tester(
        archive_base_url="https://absfaweijo.com"
    ).assert_repo_does_not_initialize(archive_path="/somevalue/abc")

    # TESTCASE 2: With invalid domain and valid archive_path -> invalid archive_url
    known_instances_data_repo_tester(
        archive_base_url="https://absfaweijo.com"
    ).assert_repo_does_not_initialize(archive_path=FigshareTestRecord.archive_path)

    # TESTCASE 3: With valid domain and invalid archive_path -> invalid archive_url
    known_instances_data_repo_tester(
        archive_base_url="https://figshare.com"
    ).assert_repo_does_not_initialize(archive_path="/somevalue/abc")

    # TESTCASE 4: With valid domain and valid archive_path -> valid archive_url
    known_instances_data_repo_tester(
        archive_base_url="https://figshare.com"
    ).assert_repo_does_initialize(archive_path=FigshareTestRecord.archive_path)

    # TESTCASE 5: Figshare subdomains are known hosted instances.
    known_instances_data_repo_tester(
        archive_base_url="https://faber.figshare.com"
    ).assert_repo_does_initialize(
        archive_path="/articles/dataset/My_example_embargoed_record/8356369"
    )

    # TESTCASE 6: Exact custom instances can be configured in instances.txt.
    monkeypatch.setattr(
        repository,
        "_known_figshare_instances",
        lambda: {
            "https://data.example.edu": "https://api.data.example.edu/v2",
            "https://figshare.manchester.ac.uk": "https://api.figshare.com/v2",
        },
    )
    repo_tester = known_instances_data_repo_tester(
        archive_base_url="https://data.example.edu"
    )
    repo_tester.initialize_repo(
        doi=FigshareTestRecord.doi,
        archive_path="/articles/dataset/Example/14763051",
    )

    assert repo_tester.repo.api_base_url == "https://api.data.example.edu/v2"

    # TESTCASE 7: Institutional Figshare instances from re3data initialize
    # through the known-instance code path without probing the API.
    repo_tester = known_instances_data_repo_tester(
        archive_base_url="https://figshare.manchester.ac.uk"
    )
    repo_tester.initialize_repo(
        doi=ManchesterFigshareTestRecord.doi,
        archive_path=ManchesterFigshareTestRecord.archive_path,
    )

    assert repo_tester.repo.api_base_url == "https://api.figshare.com/v2"
