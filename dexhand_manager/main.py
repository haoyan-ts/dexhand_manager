import asyncio
import json
import sys
from os import path
from logging import config, getLogger

from services import serve

LOG = getLogger(__name__)

if __name__ == "__main__":
    with open(path.join(path.dirname(__file__), "log_config.json"), "r") as f:
        config.dictConfig(json.load(f))

    loop = asyncio.get_event_loop()
    try:
        LOG.info("Starting DexHand Manager")
        loop.run_until_complete(serve())
    except KeyboardInterrupt:
        LOG.info("Shutting down DexHand Manager")
        loop.run_until_complete(loop.shutdown_asyncgens())
        sys.exit(0)
