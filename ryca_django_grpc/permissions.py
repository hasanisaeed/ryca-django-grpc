import jwt
from rest_framework.settings import api_settings

SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')
ACCESS_TOKEN_ERROR_MSG = 'Invalid access_token'
SESSION_TOKEN_ERROR_MSG = 'Invalid session_token'
SESSION_TOKEN_EXPIRED_MSG = 'Expired session_token'
PERMISSION_EXPIRED_MSG = 'Endpoint is restricted access'


class OperationHolderMixin:
    def __and__(self, other):
        return OperandHolder(AND, self, other)

    def __or__(self, other):
        return OperandHolder(OR, self, other)

    def __rand__(self, other):
        return OperandHolder(AND, other, self)

    def __ror__(self, other):
        return OperandHolder(OR, other, self)

    def __invert__(self):
        return SingleOperandHolder(NOT, self)


class SingleOperandHolder(OperationHolderMixin):
    def __init__(self, operator_class, op1_class):
        self.operator_class = operator_class
        self.op1_class = op1_class

    def __call__(self, *args, **kwargs):
        op1 = self.op1_class(*args, **kwargs)
        return self.operator_class(op1)


class OperandHolder(OperationHolderMixin):
    def __init__(self, operator_class, op1_class, op2_class):
        self.operator_class = operator_class
        self.op1_class = op1_class
        self.op2_class = op2_class

    def __call__(self, *args, **kwargs):
        op1 = self.op1_class(*args, **kwargs)
        op2 = self.op2_class(*args, **kwargs)
        return self.operator_class(op1, op2)


class AND:
    def __init__(self, op1, op2):
        self.op1 = op1
        self.op2 = op2

    def has_permission(self, request, context):
        return (
                self.op1.has_permission(request, context) and
                self.op2.has_permission(request, context)
        )

    def has_object_permission(self, request, context, obj):
        return (
                self.op1.has_object_permission(request, context, obj) and
                self.op2.has_object_permission(request, context, obj)
        )


class OR:
    def __init__(self, op1, op2):
        self.op1 = op1
        self.op2 = op2

    def has_permission(self, request, context):
        return (self.op1.has_permission(request, context) or
                self.op2.has_permission(request, context))

    def has_object_permission(self, request, context, obj):
        return (self.op1.has_object_permission(request, context, obj) or
                self.op2.has_object_permission(request, context, obj))


class NOT:
    def __init__(self, op1):
        self.op1 = op1

    def has_permission(self, request, context):
        return not self.op1.has_permission(request, context)

    def has_object_permission(self, request, context, obj):
        return not self.op1.has_object_permission(request, context, obj)


class BasePermissionMetaclass(OperationHolderMixin, type):
    pass


class BasePermission(metaclass=BasePermissionMetaclass):
    """
    A base class from which all permission classes should inherit.
    """

    def has_permission(self, request, context):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True

    def has_object_permission(self, request, context, obj):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True


class IsAuthenticated(BasePermission):

    def has_permission(self, request, context):
        metadata = dict(context.invocation_metadata())
        access_token = metadata['access_token']
        if self.has_access_token_error(access_token):
            return False
        has_error, detail = self.has_jwt_error(access_token)
        if has_error:
            return False
        return True

    def has_access_token_error(self, access_token):
        return not access_token

    def has_jwt_error(self, access_token):
        token = api_settings.JWT_TOKEN
        if token:
            try:
                jwt.decode(access_token,
                           key=token,
                           algorithms=["HS256"]).get('user_info')
            except jwt.DecodeError:
                return True, SESSION_TOKEN_ERROR_MSG
            except jwt.ExpiredSignatureError:
                return True, SESSION_TOKEN_EXPIRED_MSG
        return False, None
