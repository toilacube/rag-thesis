from functools import wraps

class Guard:

    def is_super_user(self, user) -> bool:
        return user.is_superuser

    def check_superuser(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            user = kwargs.get('user') or args[1]  # Get user from args
            if self.is_super_user(user):
                return True  # Full permission for superuser
            return func(self, *args, **kwargs)
        return wrapper

    @check_superuser
    def canAddDocument(self, add_document_permission: str, user, project_id: str) -> bool:

        # Check if the user has add_document_permission under the project_id
        return 1
    
    @check_superuser
    def canEditDocument(self, edit_document_permission: str, user, project_id: str) -> bool:
        return 1