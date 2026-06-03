class DouyinPayError(Exception):
    pass


class ServiceError(DouyinPayError):
    def __init__(self, code: str, message: str, detail: dict | None = None):
        self.code = code
        self.message = message
        self.detail = detail
        super().__init__(f"[{code}] {message}")


class SignatureError(DouyinPayError):
    pass


class DecryptionError(DouyinPayError):
    pass


class NetworkError(DouyinPayError):
    def __init__(self, message: str, original: Exception | None = None):
        super().__init__(message)
        if original is not None:
            self.__cause__ = original
