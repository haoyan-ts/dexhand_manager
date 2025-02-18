from injector import Module, provider, singleton
from repositories.repository import LocalRepository


class RepositoryModule(Module):
    @singleton
    @provider
    def provide_local_repository() -> LocalRepository:
        return LocalRepository()


# class
