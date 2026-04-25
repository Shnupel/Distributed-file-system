class AppException(Exception):
    """Base application exception"""
    status_code: int = 500
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.detail
        super().__init__(self.detail)


# Register Exceptions
class UserAlreadyExists(AppException):
    status_code = 409
    detail = "User already exists"


# Authenticate Exceptions
class InvalidCredentials(AppException):
    status_code = 401
    detail = "Invalid username or password"

class TokenExpiredError(AppException):
    status_code = 401
    detail = "Token has expired"

class TokenInvalidError(AppException):
    status_code = 401
    detail = "Token is invalid"


# User Exceptions
class UserNotFound(AppException):
    status_code = 404
    detail = "User not found"


# DFS Exceptions
class FsEntryNotFound(AppException):
    status_code = 404
    detail = "File system entry not found"


class FsEntryAlreadyExists(AppException):
    status_code = 409
    detail = "Entry with this name already exists"


class FsParentInvalid(AppException):
    status_code = 400
    detail = "Parent entry is invalid"


class FileNotReady(AppException):
    status_code = 409
    detail = "File is not ready for download"


class FileUploadFailed(AppException):
    status_code = 500
    detail = "File upload failed"


class ChunkUrlInvalid(AppException):
    status_code = 403
    detail = "Chunk URL signature is invalid or expired"


class ChunkNotFound(AppException):
    status_code = 404
    detail = "Chunk not found"


class StorageNodeUnavailable(AppException):
    status_code = 503
    detail = "No available storage nodes"


class ReplicationQuorumNotReached(AppException):
    status_code = 503
    detail = "Replication quorum was not reached"


class FsEntryIsDirectory(AppException):
    status_code = 400
    detail = "Operation is only supported for files"