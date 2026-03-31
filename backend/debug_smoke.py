import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from soft_skills_backend.app import create_app
from soft_skills_backend.config import get_settings
from soft_skills_backend.smoke.support.backend import SmokeBackendClient
from soft_skills_backend.smoke.support.actors import SmokeActorBootstrap
from soft_skills_backend.smoke.support.environment import SmokeApplicationSessionFactory
import httpx

settings = get_settings()


async def run():
    with TemporaryDirectory(prefix="proactivity-smoke-") as temp_dir:
        smoke_settings = settings.model_copy(
            update={
                "environment": "test",
                "database_url": f"sqlite+pysqlite:///{temp_dir}/smoke.db",
                "provider_max_retries": 0,
            }
        )
        app = create_app(smoke_settings)
        app.state.container.background_tasks.attach(asyncio.get_running_loop())
        SmokeApplicationSessionFactory()._migrate(smoke_settings)

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            backend = SmokeBackendClient(
                client, session_factory=app.state.container.session_factory
            )
            actors = await SmokeActorBootstrap(backend).prepare()

            session_payload = await backend.create_assistant_session(
                user_id=actors.learner_id,
                title="Proactivity Smoke",
            )
            turn_payload = await backend.create_assistant_turn(
                user_id=actors.learner_id,
                session_id=str(session_payload["id"]),
                message="check my collections",
            )

            for i in range(20):
                await asyncio.sleep(1)
                session = await backend.get_assistant_session(
                    user_id=actors.learner_id,
                    session_id=str(session_payload["id"]),
                )
                turn = session["turns"][0]
                print(f"Second {i + 1}: status={turn['status']}")
                if turn["status"] != "running":
                    print(f"Final turn: {turn}")
                    break
            else:
                print("Still running after 20s")


asyncio.run(run())
