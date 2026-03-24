import argparse
import asyncio
import sys

from dotenv import load_dotenv

from src.agents.receptionist import create_receptionist_agent
from src.core.telemetry import flush_telemetry, setup_telemetry
from src.devui import serve_devui


async def _show_agent_status() -> None:
    async with create_receptionist_agent() as agent:
        print(f"Loaded {agent.name} agent using deployment {agent.client.model_id}.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the maf-contact-centre entry points.")
    subparsers = parser.add_subparsers(dest="command")
    parser.set_defaults(command="status")

    subparsers.add_parser("status", help="Load the receptionist agent and print the active deployment.")

    devui_parser = subparsers.add_parser("devui", help="Run Agent Framework DevUI with in-memory registration.")
    devui_parser.add_argument("--host", default="127.0.0.1", help="Host interface for the DevUI server.")
    devui_parser.add_argument("--port", type=int, default=8080, help="Port for the DevUI server.")
    devui_parser.add_argument(
        "--no-auto-open",
        action="store_true",
        help="Do not open the browser after DevUI starts.",
    )
    devui_parser.add_argument(
        "--instrumentation-enabled",
        action="store_true",
        help="Enable DevUI OpenTelemetry instrumentation.",
    )
    devui_parser.add_argument(
        "--mode",
        choices=["developer", "user"],
        default="developer",
        help="Run DevUI in developer or user mode.",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    load_dotenv()
    args = parse_args(argv or [])

    if args.command == "devui":
        serve_devui(
            host=args.host,
            port=args.port,
            auto_open=not args.no_auto_open,
            instrumentation_enabled=args.instrumentation_enabled,
            mode=args.mode,
        )
        return

    setup_telemetry()
    try:
        asyncio.run(_show_agent_status())
    finally:
        flush_telemetry()


if __name__ == "__main__":
    main(sys.argv[1:])
