import asyncio

from dotenv import load_dotenv

load_dotenv()

from src.core.telemetry import setup_telemetry  # noqa: E402

setup_telemetry()

from src.agents.receptionist import create_receptionist_agent  # noqa: E402


async def _main_async() -> None:
    async with create_receptionist_agent() as agent:
        print(f"Loaded {agent.name} agent using deployment {agent.client.model_id}.")


def main() -> None:
    asyncio.run(_main_async())


if __name__ == "__main__":
    main()
