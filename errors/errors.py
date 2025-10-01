class ErrEntityNotFound(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class ErrEntityConflict(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class ErrBadRequest(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class ErrNotAuthorized(Exception):
    def __init__(self, message: str):
        super().__init__(message)
