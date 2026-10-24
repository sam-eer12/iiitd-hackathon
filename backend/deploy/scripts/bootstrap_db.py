"""Initial role setup using managed RDS master credentials in an ephemeral container."""

import asyncio
import os
import ssl

import asyncpg


async def main():
    connection = await asyncpg.connect(
        host=os.environ["DATABASE_HOST"],
        database="tenderlens",
        user=os.environ["BOOTSTRAP_USERNAME"],
        password=os.environ["BOOTSTRAP_PASSWORD"],
        ssl=ssl.create_default_context(cafile="/app/certs/rds-ca.pem"),
    )
    try:
        async with connection.transaction():
            # Fixed identifiers, no untrusted SQL interpolation.
            for name in ["tl_app", "tl_migrator"]:
                if not await connection.fetchval("SELECT 1 FROM pg_roles WHERE rolname=$1", name):
                    await connection.execute(f"CREATE ROLE {name} LOGIN")
                await connection.execute(f"GRANT rds_iam TO {name}")
            await connection.execute("GRANT CONNECT ON DATABASE tenderlens TO tl_app, tl_migrator")
            await connection.execute("GRANT CREATE ON DATABASE tenderlens TO tl_migrator")
            await connection.execute(
                "CREATE SCHEMA IF NOT EXISTS tenderlens_api AUTHORIZATION tl_migrator"
            )
            await connection.execute("GRANT USAGE ON SCHEMA tenderlens_api TO tl_app")
            await connection.execute(
                "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA tenderlens_api TO tl_app"
            )
            await connection.execute(
                "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA tenderlens_api TO tl_app"
            )
            await connection.execute(
                "ALTER DEFAULT PRIVILEGES FOR ROLE tl_migrator IN SCHEMA tenderlens_api GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO tl_app"
            )
            await connection.execute(
                "ALTER DEFAULT PRIVILEGES FOR ROLE tl_migrator IN SCHEMA tenderlens_api GRANT USAGE, SELECT ON SEQUENCES TO tl_app"
            )
    finally:
        await connection.close()


asyncio.run(main())
