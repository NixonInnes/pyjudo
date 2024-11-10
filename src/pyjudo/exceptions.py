class ServiceException(Exception):
    pass


class ServiceCircularDependencyError(ServiceException):
    pass


class ServiceResolutionError(ServiceException):
    pass


class ServiceRegistrationError(ServiceException):
    pass


class ServiceTypeError(ServiceException):
    pass


class ServiceDisposedError(ServiceException):
    pass

class ServiceScopeError(ServiceException):
    pass