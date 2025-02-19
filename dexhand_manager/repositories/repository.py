import logging
import threading
from typing import Optional

import grpc
from entities import DexHand, Session
from ts.dexhand.v1.common_pb2 import ArmType, HandType, Side
from ts.dexhand.v1.dexhand_service_pb2 import DexHandConfig
from .error import RepositoryError, RepositoryAlreadyExistsError

LOG = logging.getLogger(__name__)


class LocalRepository:
    _lock = threading.RLock()

    _session: Optional[Session] = None

    def create_session(self):
        with self._lock:
            if self._session is None:
                self._session = Session.create()

                return self._session
            else:
                raise RepositoryAlreadyExistsError("Session already exists.")

    def get_session(self) -> Session:
        with self._lock:
            if self._session is None:
                raise RepositoryError("Session does not exist.")
            else:
                return self._session

    def update_session(self, **kwargs):
        with self._lock:
            if self._session is None:
                raise RepositoryError("Session does not exist.")
            else:
                self._session.merge_from_dict(**kwargs)
                return self._session

    def delete_session(self):
        with self._lock:
            if self._session is None:
                raise RepositoryError("Session does not exist.")
            else:
                del self._session
