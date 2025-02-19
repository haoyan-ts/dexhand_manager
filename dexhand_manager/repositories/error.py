class RepositoryError(Exception):
    pass


class RepositoryAlreadyExistsError(RepositoryError):
    pass
