import pathlib
import logging

from . import util_context

logger = logging.getLogger(__file__)


def main():
    logging.basicConfig(
        level=logging.INFO,
        # format="%(asctime)s %(levelname)s %(message)s",
        format="%(levelname)s %(filename)s:%(lineno)d %(message)s",
        datefmt="%H:%M:%S",
    )

    context = util_context.Context(directory=pathlib.Path.cwd())
    context.collect()
    context.print_libraries()
    context.print()


if __name__ == "__main__":
    main()
