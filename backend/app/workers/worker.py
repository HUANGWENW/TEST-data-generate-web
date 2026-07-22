import redis
from rq import Queue, Worker

from app.core.config import get_settings


def main():
    settings = get_settings()
    connection = redis.from_url(settings.redis_url)
    queue = Queue("default", connection=connection)
    worker = Worker([queue], connection=connection)
    worker.work()


if __name__ == "__main__":
    main()
