class AppError(Exception):
    status_code = 500
    default_detail = "Application Error"
    
    def __init__(self, detail: str | None = None):
        self.detail = detail or self.default_detail
        super().__init__(self.detail)
        


class ConflictError(AppError):
    status_code = 409
    default_detail = "Conflict"
    

class NotFoundError(AppError):
    status_code = 404
    default_detail = "Resource not found"
    
class AuthenticationError(AppError):
    status_code = 401
    default_detail = "Authentication failed"
    
class EmailAlreadyInUseError(ConflictError):
    default_detail = "Email already in use"
    
class UserNotFoundError(NotFoundError):
    default_detail = "User not found"
    
class InvalidCredentialsError(AuthenticationError):
    default_detail = "Invalid credentials"
    
class InvalidTokenError(AppError):
    status_code = 400
    default_detail = "Invalid or expired token"
    
class OwnedResourceNotFoundError(NotFoundError):
    default_detail = "Resource not found"
    
    
class ValidationError(AppError):
    status_code = 400
    default_detail = "Invalid request"
    
class AccountNotFoundError(NotFoundError):
    default_detail = "Account not found"
    
class CategoryNotFoundError(NotFoundError):
    default_detail = "Category not found"
    
class TransactionNotFoundError(NotFoundError):
    default_detail = "Transaction not found"
    
class InvalidTransactionError(ValidationError):
    default_detail = "Invalid transaction"

class DuplicateTransactionError(ConflictError):
    default_detail = "Duplicate transaction"