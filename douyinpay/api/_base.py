class BaseService:
    """Base class for API service modules.

    Holds a reference to the DouyinPayClient and provides a convenience
    method for making requests.
    """

    def __init__(self, client):
        self._client = client

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        return self._client.request(method, path, body)
