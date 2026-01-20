import dataclasses

class classproperty(property):
    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


@dataclasses.dataclass
class _FigshareEndpoint:
    path: str
    response: dict


class FigshareTestRecord:
    @classproperty
    def doi(cls) -> str:
        return "10.6084/m9.figshare.14763051.v1"

    @classproperty
    def article_id(cls) -> str:
        return "14763051"

    @classproperty
    def archive_path(cls) -> str:
        return f"/article/{cls.article_id}"

    class endpoints:
        articles = _FigshareEndpoint(
            path=f"/v2/articles?doi=10.6084/m9.figshare.14763051.v1s",
            response=[{"id": 14763051, "title": "Test data for the Pooch library", "doi": "10.6084/m9.figshare.14763051.v1", "handle": "",
            "url": "https://api.figshare.com/v2/articles/14763051", "published_date": "2021-06-10T14:45:37Z", "thumb": "", "defined_type": 3,
            "defined_type_name": "dataset", "group_id": 0, "url_private_api": "https://api.figshare.com/v2/account/articles/14763051",
            "url_public_api": "https://api.figshare.com/v2/articles/14763051",
            "url_private_html": "https://figshare.com/account/articles/14763051",
            "url_public_html": "https://figshare.com/articles/dataset/Test_data_for_the_Pooch_library/14763051",
            "timeline": {"posted": "2021-06-10T14:45:37", "firstOnline": "2021-06-10T14:45:37"},
            "resource_title": "", "resource_doi": "", "created_date": "2021-06-10T14:45:37Z", "modified_date": "2023-05-30T11:14:17Z"}])