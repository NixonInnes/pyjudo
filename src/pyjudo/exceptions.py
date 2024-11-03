class ServicesException(Exception):
    pass


class ServicesCircularDependencyError(ServicesException):
    pass


class ServicesResolutionError(ServicesException):
    pass


class ServicesRegistrationError(ServicesException):
    pass