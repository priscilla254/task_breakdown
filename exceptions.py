"""Domain / application errors raised by services (mapped to HTTP in main.py)."""


class AppError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    pass


class BadRequestError(AppError):
    pass
