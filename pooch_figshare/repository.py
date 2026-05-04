from functools import lru_cache
from importlib.resources import files
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlsplit, urlunsplit
import warnings

from pooch_doi.license import *
from pooch_doi.repository import DEFAULT_TIMEOUT, DataRepository


PUBLIC_FIGSHARE_API_BASE_URL = "https://api.figshare.com/v2"


class _ParsedFigshareURL:
    def __init__(
        self, base_url: str, article_id: Optional[str], version: Optional[int]
    ):
        self.base_url = base_url
        self.article_id = article_id
        self.version = version


class FigshareRepository(DataRepository):  # pylint: disable=missing-class-docstring

    allowed_exceptions: Tuple[type[Exception], ...] = ()

    # A URL for an issue tracker for this implementation
    issue_tracker: Optional[str] = "https://github.com/ssciwr/pooch-figshare/issues"

    # Whether the repository allows self-hosting
    allows_self_hosting: bool = True

    # Whether this repository is fully supported (meaning that all public data
    # from this repository is accessible via pooch).
    full_support: bool = True

    # Whether this implementation performs requests to external services
    # during initialization. We use this to minimize the execution time.
    init_requires_requests: bool = True

    @property
    def name(self) -> str:
        """
        The display name of the repository.
        """
        return "Figshare"  # pragma: no cover

    @property
    def homepage(self) -> str:
        """
        The homepage URL of the repository.
        This could be the URL of the actual service or the URL of the project,
        if it is a data repository that allows self-hosting.
        """
        return "https://figshare.com/"  # pragma: no cover

    def __init__(
        self,
        doi: str,
        archive_url: str,
        api_base_url: str = PUBLIC_FIGSHARE_API_BASE_URL,
        article_id: Optional[str] = None,
        version: Optional[int] = None,
        api_response: Optional[dict] = None,
    ):
        parsed_url = self._parse_archive_url(archive_url)
        self.archive_url = archive_url.rstrip("/")
        self.doi = doi
        self.base_url = (
            parsed_url.base_url
            if parsed_url is not None
            else self._origin_from_url(archive_url)
        )
        self.api_base_url = api_base_url.rstrip("/")
        self.article_id = article_id or (
            parsed_url.article_id if parsed_url is not None else None
        )
        self.url_version = (
            (version if version is not None else parsed_url.version)
            if parsed_url is not None
            else version
        )
        self._api_response = api_response
        self._warned_unversioned_doi = False

    @classmethod
    def initialize(cls, doi: str, archive_url: str):
        """
        Initialize the data repository if the given URL points to a
        corresponding repository.

        Initializes a data repository object. This is done as part of
        a chain of responsibility. If the class cannot handle the given
        repository URL, it returns `None`. Otherwise a `DataRepository`
        instance is returned.

        Parameters
        ----------
        doi : str
            The DOI that identifies the repository
        archive_url : str
            The resolved URL for the DOI
        """
        parsed_url = cls._parse_archive_url(archive_url)

        # A generic Figshare probe should be reasonably cheap and specific.
        # Without an article id in the resolved URL, the only way to detect
        # Figshare would be a broad DOI search request for every DOI.
        if parsed_url is None or parsed_url.article_id is None:
            return None

        version = cls._parse_version_from_doi(doi)
        if version is None:
            version = parsed_url.version

        for api_base_url in cls._api_base_url_candidates(parsed_url.base_url):
            article_details = cls._probe_article_details(
                api_base_url=api_base_url,
                article_id=parsed_url.article_id,
                doi=doi,
                expected_base_url=parsed_url.base_url,
                version=version,
            )
            if article_details is None:
                continue

            return cls(
                doi=doi,
                archive_url=archive_url,
                api_base_url=api_base_url,
                article_id=parsed_url.article_id,
                version=parsed_url.version,
                api_response=article_details,
            )

        return None

    @staticmethod
    def _origin_from_url(url: str) -> str:
        split_url = urlsplit(url)
        return urlunsplit((split_url.scheme, split_url.netloc, "", "", "")).rstrip("/")

    @staticmethod
    def _parse_archive_url(archive_url: str) -> Optional[_ParsedFigshareURL]:
        split_url = urlsplit(archive_url.strip())
        if split_url.scheme not in ("http", "https") or not split_url.netloc:
            return None

        base_url = urlunsplit((split_url.scheme, split_url.netloc, "", "", "")).rstrip(
            "/"
        )
        path_parts = [part for part in split_url.path.split("/") if part]
        if not path_parts:
            return _ParsedFigshareURL(base_url, None, None)

        article_id: Optional[str] = None
        version: Optional[int] = None

        if len(path_parts) >= 2 and path_parts[0] == "article":
            article_id = path_parts[1] if path_parts[1].isdigit() else None
            if len(path_parts) >= 3 and path_parts[2].isdigit():
                version = int(path_parts[2])

        elif "articles" in path_parts:
            article_index = path_parts.index("articles")
            article_path = path_parts[article_index + 1 :]
            numeric_segments = [
                (index, segment)
                for index, segment in enumerate(article_path)
                if segment.isdigit()
            ]

            if len(article_path) >= 2 and article_path[-1].isdigit():
                if article_path[-2].isdigit():
                    article_id = article_path[-2]
                    version = int(article_path[-1])
                elif numeric_segments:
                    article_id = numeric_segments[-1][1]
            elif numeric_segments:
                article_id = numeric_segments[-1][1]

        return _ParsedFigshareURL(base_url, article_id, version)

    @staticmethod
    def _uses_public_figshare_api(base_url: str) -> bool:
        host = urlsplit(base_url).netloc.lower()
        return host == "figshare.com" or host.endswith(".figshare.com")

    @classmethod
    def _api_base_url_candidates(cls, base_url: str) -> list[str]:
        split_url = urlsplit(base_url)
        candidates = [PUBLIC_FIGSHARE_API_BASE_URL]

        if not cls._uses_public_figshare_api(base_url):
            candidates.extend(
                [
                    urlunsplit(
                        (
                            split_url.scheme,
                            f"api.{split_url.netloc}",
                            "/v2",
                            "",
                            "",
                        )
                    ),
                    urlunsplit((split_url.scheme, split_url.netloc, "/api/v2", "", "")),
                    urlunsplit((split_url.scheme, split_url.netloc, "/v2", "", "")),
                ]
            )

        return list(dict.fromkeys(candidate.rstrip("/") for candidate in candidates))

    @staticmethod
    def _make_request(
        url: str, headers: Optional[Dict[str, str]] = None, check_rate_limit=True
    ):
        headers = headers if headers is not None else dict()
        headers.update(
            {
                "User-Agent": (
                    "pooch/1.8.2 "
                    "(https://github.com/fatiando/pooch; "
                    "https://github.com/ssciwr/pooch-figshare)"
                )
            }
        )

        import requests  # pylint: disable=C0415

        response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)

        if check_rate_limit and response.status_code == 429:
            raise RuntimeError(
                f"The request to '{url}' returned with status code "
                f"{response.status_code!s}. "
                "This means you are probably rate-limited. "
                "Please try again in a few minutes."
            )

        return response

    @staticmethod
    def _json_from_response(response, url: str):
        try:
            return response.json()
        except ValueError as exc:
            raise RuntimeError(
                f"An issue occurred decoding the JSON response from '{url}'. "
                "This should not happen. "
                "Please open an issue at https://github.com/ssciwr/pooch-figshare/issues"
            ) from exc

    @classmethod
    def _make_request_to_json(
        cls,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        check_rate_limit=True,
    ):
        response = cls._make_request(
            url, headers=headers, check_rate_limit=check_rate_limit
        )
        response.raise_for_status()
        return cls._json_from_response(response, url)

    @staticmethod
    def _article_details_url(
        api_base_url: str, article_id: str, version: Optional[int] = None
    ) -> str:
        url = f"{api_base_url.rstrip('/')}/articles/{article_id}"
        if version is not None:
            url += f"/versions/{version}"
        return url

    @staticmethod
    def _article_search_url(api_base_url: str, doi: str) -> str:
        return f"{api_base_url.rstrip('/')}/articles?doi={doi}"

    @classmethod
    def _probe_article_details(
        cls,
        api_base_url: str,
        article_id: str,
        doi: str,
        expected_base_url: Optional[str] = None,
        version: Optional[int] = None,
    ) -> Optional[dict]:
        url = cls._article_details_url(api_base_url, article_id, version)

        try:
            response = cls._make_request(
                url, headers={"Accept": "application/json"}, check_rate_limit=False
            )
            if 400 <= response.status_code < 600:
                return None
            article_details = cls._json_from_response(response, url)
        except Exception:  # pylint: disable=broad-exception-caught
            return None

        if not cls._article_details_match(
            article_details, article_id, doi, expected_base_url
        ):
            return None

        return article_details

    @staticmethod
    def _doi_without_figshare_version(doi: str) -> str:
        return re.sub(r"\.v\d+$", "", doi.strip().lower())

    @classmethod
    def _doi_matches(cls, expected: str, actual: str) -> bool:
        if not expected or not actual:
            return True
        expected = expected.strip().lower()
        actual = actual.strip().lower()
        return expected == actual or (
            cls._doi_without_figshare_version(expected)
            == cls._doi_without_figshare_version(actual)
        )

    @classmethod
    def _article_details_match(
        cls,
        article_details: dict,
        article_id: Optional[str],
        doi: str,
        expected_base_url: Optional[str] = None,
    ) -> bool:
        if article_id is not None and str(article_details.get("id")) != str(article_id):
            return False

        details_doi = article_details.get("doi")
        if details_doi is not None and not cls._doi_matches(doi, details_doi):
            return False

        public_html_url = article_details.get("url_public_html")
        if public_html_url is not None and expected_base_url is not None:
            if cls._origin_from_url(public_html_url) != expected_base_url.rstrip("/"):
                return False

        return "files" in article_details

    @staticmethod
    def _parse_version_from_doi(doi: str) -> Optional[int]:
        """
        Parse version from the DOI.

        Return None if version is not available in the DOI.
        """
        match = re.search(r"\.v(?P<version>\d+)$", doi.strip(), re.IGNORECASE)
        if match is None:
            return None
        return int(match.group("version"))

    def _desired_version(self) -> Optional[int]:
        doi_version = self._parse_version_from_doi(self.doi)
        return doi_version if doi_version is not None else self.url_version

    def _warn_about_unversioned_doi(self) -> None:
        if self._desired_version() is not None or self._warned_unversioned_doi:
            return

        warnings.warn(
            f"The Figshare DOI '{self.doi}' doesn't specify which version of "
            "the repository should be used. "
            "Figshare will point to the latest version available.",
            UserWarning,
        )
        self._warned_unversioned_doi = True

    @property
    def api_response(self):
        """Cached API response from Figshare"""
        if self._api_response is None:
            article_id = self.article_id
            if article_id is None:
                article = self._make_request_to_json(
                    self._article_search_url(self.api_base_url, self.doi),
                    headers={"Accept": "application/json"},
                )[0]
                article_id = str(article["id"])
                self.article_id = article_id

            self._api_response = self._make_request_to_json(
                self._article_details_url(
                    self.api_base_url, article_id, self._desired_version()
                ),
                headers={"Accept": "application/json"},
            )

        self._warn_about_unversioned_doi()
        return self._api_response

    def download_url(self, file_name):
        """
        Use the repository API to get the download URL for a file given
        the archive URL.

        Parameters
        ----------
        file_name : str
            The name of the file in the archive that will be downloaded.

        Returns
        -------
        download_url : str
            The HTTP URL that can be used to download the file.
        """
        files = {item["name"]: item for item in self.api_response["files"]}
        if file_name not in files:
            raise ValueError(
                f"File '{file_name}' not found in data archive "
                f"{self.archive_url} (doi:{self.doi})."
            )
        download_url = files[file_name]["download_url"]
        return download_url

    def create_registry(self) -> dict[str, str]:
        """
        Create a registry dictionary using the data repository's API

        Returns
        ----------
        registry : Dict[str,str]
            The registry dictionary.
        """
        registry: dict[str, str] = dict()
        for filedata in self.api_response["files"]:
            registry[filedata["name"]] = f"md5:{filedata['computed_md5']}"
        return registry

    def licenses(self) -> List[License]:
        license_data = self.api_response["license"]
        if not license_data:
            return list()

        return [
            License(
                name=license_data["name"],
                identifiers=[
                    LicenseIdentifier(
                        scheme=LicenseIdentifierScheme.URL, value=license_data["url"]
                    )
                ],
            )
        ]


@lru_cache(maxsize=1)
def _known_figshare_instances() -> dict[str, str]:
    instances_file = files("pooch_figshare").joinpath("instances.txt")
    instances = dict()
    for line in instances_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        instance_base_url, *api_base_url = line.split()
        instances[instance_base_url.rstrip("/")] = (
            api_base_url[0].rstrip("/")
            if api_base_url
            else PUBLIC_FIGSHARE_API_BASE_URL
        )

    return instances


class KnownInstancesFigshareRepository(FigshareRepository):
    init_requires_requests = False
    omit_from_repository_list = True

    @classmethod
    def _known_instance_api_base_url(cls, base_url: str) -> Optional[str]:
        if cls._uses_public_figshare_api(base_url):
            return PUBLIC_FIGSHARE_API_BASE_URL

        normalized_base_url = base_url.rstrip("/")
        for instance_base_url, api_base_url in _known_figshare_instances().items():
            if (
                normalized_base_url == instance_base_url
                or normalized_base_url.startswith(f"{instance_base_url}/")
            ):
                return api_base_url

        return None

    @classmethod
    def initialize(cls, doi: str, archive_url: str):
        parsed_url = cls._parse_archive_url(archive_url)
        if parsed_url is None or parsed_url.article_id is None:
            return None

        api_base_url = cls._known_instance_api_base_url(parsed_url.base_url)
        if api_base_url is None:
            return None

        return cls(
            doi=doi,
            archive_url=archive_url,
            api_base_url=api_base_url,
            article_id=parsed_url.article_id,
            version=parsed_url.version,
        )
