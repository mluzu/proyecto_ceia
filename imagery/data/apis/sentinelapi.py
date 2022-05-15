from requests import Session


class SentinelApi:
    def __init__(self, user, password, platformname, producttype, processinglevel, url="https://apihub.copernicus.eu/apihub") -> None:
        self.session = Session()
        self.api_url = url
        self.credentials = (user, password)

    def do_query(self, url, stream=False):
        with self.session.get(url, auth=self.credentials, stream=stream) as response:
            return response.content

    def build_search_query(self, filters):
        if filters is None:
            raise ValueError
        filters = ' AND '.join(
            [
                f'{key}:{value}'
                for key, value in sorted(filters.items())
            ]
        )
        return f'{self.api_url}/search?q={filters}'

    def build_odata_url(self, path):
        return '{}{}{}'.format(self.api_url, "/odata/v1", path)
