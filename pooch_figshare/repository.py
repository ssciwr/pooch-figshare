from pooch_doi import DataRepository

class FigshareRepository(DataRepository):  # pylint: disable=missing-class-docstring
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
        return "placeholder"  # pragma: no cover
    
    def __init__(self, doi, archive_url):
        self.archive_url = archive_url
        self.doi = doi
        self._api_response = None

    @classmethod
    def initialize(cls, doi, archive_url):
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
        # Check whether this is a Figshare URL
        from urllib.parse import urlsplit
        if urlsplit(archive_url).netloc != "figshare.com":
            return None
        return cls(doi, archive_url)

    def _parse_version_from_doi(self):
        """
        Parse version from the doi
        Return None if version is not available in the doi.
        """
        # Get suffix of the doi
        _, suffix = self.doi.split("/")
        # Split the suffix by dots and keep the last part
        last_part = suffix.split(".")[-1]
        # Parse the version from the last part
        if last_part[0] != "v":
            return None
        version = int(last_part[1:])
        return version

    @property
    def api_response(self):
        """Cached API response from Figshare"""
        if self._api_response is None:
            # Lazy import requests to speed up import time
            import requests  # pylint: disable=C0415
            # Use the figshare API to find the article ID from the DOI
            article = requests.get(
                f"https://api.figshare.com/v2/articles?doi={self.doi}",
                timeout=DEFAULT_TIMEOUT,
            ).json()[0]
            article_id = article["id"]
            # Parse desired version from the doi
            version = self._parse_version_from_doi()
            # With the ID and version, we can get a list of files and their
            # download links
            if version is None:
                # Figshare returns the latest version available when no version
                # is specified through the DOI.
                warnings.warn(
                    f"The Figshare DOI '{self.doi}' doesn't specify which version of "
                    "the repository should be used. "
                    "Figshare will point to the latest version available.",
                    UserWarning,
                )
                # Define API url using only the article id
                # (figshare will resolve the latest version)
                api_url = f"https://api.figshare.com/v2/articles/{article_id}"
            else:
                # Define API url using article id and the desired version
                # Get list of files using article id and the version
                api_url = (
                    "https://api.figshare.com/v2/articles/"
                    f"{article_id}/versions/{version}"
                )
            # Make the request and return the files in the figshare repository
            response = requests.get(api_url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            self._api_response = response.json()["files"]
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
        files = {item["name"]: item for item in self.api_response}
        if file_name not in files:
            raise ValueError(
                f"File '{file_name}' not found in data archive {self.archive_url} (doi:{self.doi})."
            )
        download_url = files[file_name]["download_url"]
        return download_url

    def create_registry(self):
        """
        Populate the registry using the data repository's API
        Parameters
        ----------
        pooch : Pooch
            The pooch instance that the registry will be added to.
        """
        #for filedata in self.api_response:
        #    pooch.registry[filedata["name"]] = f"md5:{filedata['computed_md5']}"
    def licenses(self):
        return list()
