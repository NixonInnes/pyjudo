"""
This type stub file was generated by pyright.
"""

class ServiceException(Exception):
    ...


class ServiceCircularDependencyError(ServiceException):
    ...


class ServiceResolutionError(ServiceException):
    ...


class ServiceRegistrationError(ServiceException):
    ...


class ServiceTypeError(ServiceException):
    ...


class ServiceDisposedError(ServiceException):
    ...


class ServiceScopeError(ServiceException):
    ...


