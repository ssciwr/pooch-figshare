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
    
    @classproperty
    def archive_url(cls) -> str:
        return f"https://figshare.com{cls.archive_path}"

    class endpoints:
        article_search = _FigshareEndpoint(
            path=f"/v2/articles?doi=10.6084/m9.figshare.14763051.v1s",
            response=[{"id": 14763051, "title": "Test data for the Pooch library", "doi": "10.6084/m9.figshare.14763051.v1", "handle": "",
            "url": "https://api.figshare.com/v2/articles/14763051", "published_date": "2021-06-10T14:45:37Z", "thumb": "", "defined_type": 3,
            "defined_type_name": "dataset", "group_id": 0, "url_private_api": "https://api.figshare.com/v2/account/articles/14763051",
            "url_public_api": "https://api.figshare.com/v2/articles/14763051",
            "url_private_html": "https://figshare.com/account/articles/14763051",
            "url_public_html": "https://figshare.com/articles/dataset/Test_data_for_the_Pooch_library/14763051",
            "timeline": {"posted": "2021-06-10T14:45:37", "firstOnline": "2021-06-10T14:45:37"},
            "resource_title": "", "resource_doi": "", "created_date": "2021-06-10T14:45:37Z", "modified_date": "2023-05-30T11:14:17Z"}])
        
        article_details = _FigshareEndpoint(
            path=f"/v2/articles/14763051",
            response={"files": [{"id": 28369770, "name": "tiny-data.txt", "size": 59, "is_link_only": False, "download_url": "https://ndownloader.figshare.com/files/28369770",
                                "supplied_md5": "70e2afd3fd7e336ae478b1e740a5f08e", "computed_md5": "70e2afd3fd7e336ae478b1e740a5f08e", "mimetype": "text/plain"},
                                {"id": 28369773, "name": "store.zip", "size": 780, "is_link_only": False, "download_url": "https://ndownloader.figshare.com/files/28369773",
                                "supplied_md5": "7008231125631739b64720d1526619ae", "computed_md5": "7008231125631739b64720d1526619ae", "mimetype": "application/zip"}],
                                "folder_structure": {}, "authors": [{"id": 97471, "full_name": "Leonardo Uieda", "first_name": "Leonardo", "last_name": "Uieda",
                                "is_active": True, "url_name": "Leonardo_Uieda", "orcid_id": "0000-0001-6123-9515"}], "custom_fields": [],
                                "figshare_url": "https://figshare.com/articles/dataset/Test_data_for_the_Pooch_library/14763051",
                                "download_disabled": False, "description": "Pooch is an open-source Python library for data download. This archive contains testing data for Pooch's figshare download functionality. <br>",
                                "funding": None, "funding_list": [], "version": 1, "status": "public", "size": 839, "created_date": "2021-06-10T14:45:37Z",
                                "modified_date": "2023-05-30T11:14:17Z", "is_public": True, "is_confidential": False, "is_metadata_record": False, "confidential_reason": "",
                                "metadata_reason": "", "license": {"value": 1, "name": "CC BY 4.0", "url": "https://creativecommons.org/licenses/by/4.0/"},
                                "tags": ["Python", "open-source tool", "Technology not elsewhere classified"], "keywords": ["Python", "open-source tool",
                                "Technology not elsewhere classified"], "categories": [{"id": 26860, "title": "Other engineering not elsewhere classified",
                                "parent_id": 26848, "path": "/26212/26848/26860", "source_id": "409999", "taxonomy_id": 100}], "references": ["https://github.com/fatiando/pooch"],
                                "has_linked_file": False, "citation": "Uieda, Leonardo (2021). Test data for the Pooch library. figshare. Dataset. https://doi.org/10.6084/m9.figshare.14763051.v1",
                                "related_materials": [{"id": 468281, "identifier": "https://github.com/fatiando/pooch", "title": "", "relation": "References",
                                "identifier_type": "URL", "is_linkout": False, "link": "https://github.com/fatiando/pooch"}], "is_embargoed": False, "embargo_date": None,
                                "embargo_type": "file", "embargo_title": "", "embargo_reason": "", "embargo_options": [], "id": 14763051, "title": "Test data for the Pooch library",
                                "doi": "10.6084/m9.figshare.14763051.v1", "handle": "", "url": "https://api.figshare.com/v2/articles/14763051", "published_date": "2021-06-10T14:45:37Z",
                                "thumb": "", "defined_type": 3, "defined_type_name": "dataset", "group_id": None, "url_private_api": "https://api.figshare.com/v2/account/articles/14763051",
                                "url_public_api": "https://api.figshare.com/v2/articles/14763051", "url_private_html": "https://figshare.com/account/articles/14763051",
                                "url_public_html": "https://figshare.com/articles/dataset/Test_data_for_the_Pooch_library/14763051", "timeline": {"posted": "2021-06-10T14:45:37",
                                "firstOnline": "2021-06-10T14:45:37"}, "resource_title": None, "resource_doi": None})