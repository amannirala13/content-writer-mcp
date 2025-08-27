import argparse
from typing import Any

from pydantic import Field

from core.foundation.models.strict_mode import StrictModel


class Argument(StrictModel):
    name: str = Field()
    type: Any = Field()
    help: str = Field()
    default: Any = Field(default=None)

def build_cmd_args_parser(description: str, args: list[Argument]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the application with specified host and port.")
    for arg in args:
        if arg.type == bool:
            parser.add_argument(f"--{arg.name}", action="store_true", help=arg.help, default=arg.default)
        else:
            parser.add_argument(f"--{arg.name}", type=arg.type, help=arg.help, default=arg.default)
    return parser