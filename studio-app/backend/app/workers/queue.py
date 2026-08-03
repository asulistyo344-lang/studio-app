from arq.connections import ArqRedis, RedisSettings, create_pool

from app.core.config import settings

# BytePlus Hyper3D alone can poll for up to 1200s, and animate_3d_tencent
# chains a conversion + a second poll on top of that — give the worker a
# generous ceiling well above any single provider call's own timeout.
JOB_TIMEOUT_SECONDS = 1500


def get_redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(settings.redis_url)


async def get_arq_pool() -> ArqRedis:
    return await create_pool(get_redis_settings())
