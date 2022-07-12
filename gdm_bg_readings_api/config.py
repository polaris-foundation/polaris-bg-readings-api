from environs import Env
from flask import Flask


class Configuration:
    env = Env()
    SERVER_TIMEZONE: str = env.str("SERVER_TIMEZONE")
    RABBITMQ_TEST: bool = env.bool("RABBITMQ_TEST", False)
    CUSTOMER_CODE: str = env.str("CUSTOMER_CODE")
    DHOS_TRUSTOMER_API_HOST: str = env.str("DHOS_TRUSTOMER_API_HOST")
    POLARIS_API_KEY: str = env.str("POLARIS_API_KEY")
    TRUSTOMER_CONFIG_CACHE_TTL_SEC: int = env.int(
        "TRUSTOMER_CONFIG_CACHE_TTL_SEC", 60 * 60  # Cache for 1 hour by default.
    )


def init_config(app: Flask) -> None:
    app.config.from_object(Configuration)
