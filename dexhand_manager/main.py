import json
import sys
from os import path
from logging import config, getLogger

from services import serve

LOG = getLogger(__name__)

if __name__ == "__main__":
    with open(path.join(path.dirname(__file__), "log_config.json"), "r") as f:
        config.dictConfig(json.load(f))

    LOG.info(f"Starting DexHand Manager")
    serve()
