class ApplicationError(Exception):
    def __init__(self, message, error_code="INTERNAL_ERROR", http_status=500):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.http_status = http_status

class ValidationError(ApplicationError):
    def __init__(self, message, error_code="VALIDATION_ERROR"):
        super().__init__(message, error_code, 400)

class ResourceDuplicateError(ApplicationError):
    def __init__(self, message, error_code="RESOURCE_DUPLICATE"):
        super().__init__(message, error_code, 400)

class ResourceNotFoundError(ApplicationError):
    def __init__(self, message, error_code="RESOURCE_NOT_FOUND"):
        super().__init__(message, error_code, 404)

class UnauthorizedError(ApplicationError):
    def __init__(self, message, error_code="UNAUTHORIZED"):
        super().__init__(message, error_code, 401)

class ForbiddenError(ApplicationError):
    def __init__(self, message, error_code="FORBIDDEN"):
        super().__init__(message, error_code, 403)
