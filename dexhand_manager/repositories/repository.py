import logging

import grpc

from entities.dexhand_entity import DexHandEntity
from ts.dexhand.v1.dexhand_service_pb2 import DexHandConfig
from ts.dexhand.v1.common_pb2 import Side


LOG = logging.getLogger(__name__)


class LocalRepository:
    session = None
    dex_hands: dict[Side, DexHandEntity] = {}

    def validate_create_dex_hand_request(
        # self, request: dexhand_srv_pb2.CreateDexHandRequest
    ):
        # tester = self.dex_hands.get(request.config.side, None)

        # return True if tester is None else False
        pass

    def create_dex_hand_from_config(self, config: DexHandConfig):
        dex_hand = DexHandEntity()
        dex_hand.create(config)

        self.dex_hands[dex_hand.side] = dex_hand

        return dex_hand

    def get_dex_hand_by_id(self, id: str):
        for dex_hand in self.dex_hands.values():
            if dex_hand.id == id:
                return dex_hand
        return None

    def get_dex_hand_by_name(self, name: str):
        for dex_hand in self.dex_hands.values():
            if dex_hand.name == name:
                return dex_hand
        return None

    def get_dex_hand_by_side(self, side: Side):
        return self.dex_hands.get(side, None)

    # def update_dex_hand(self, request: dexhand_srv_pb2.UpdateDexHandRequest):
    #     dex_hand = self.get_dex_hand_by_id(request.dex_hand.id)
    #     LOG.debug(f"Received a update mask. {request.update_mask}")

    #     if dex_hand is None:
    #         raise grpc.RpcError(
    #             grpc.StatusCode.NOT_FOUND, f"Invalid DexHand ID: {request.dex_hand.id}"
    #         )
    #     else:
    #         dex_hand.update(request.dex_hand)
    #         return dex_hand
