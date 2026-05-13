import logging
import sys

from .acronyms import AcronymStore
from .bot import AcronymBot
from .config import Config


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    config = Config.from_env()
    store = AcronymStore(config.acronyms_file)
    logger = logging.getLogger(__name__)
    logger.info("Loaded %d acronyms from %s", len(store), config.acronyms_file)

    bot = AcronymBot(config, store)
    bot.run()


if __name__ == "__main__":
    main()
