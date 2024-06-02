"""
Index of available apps as required by gunicorn
"""

from src.app import app
from src.app_with_redis import app as app_redis

app_redis = app_redis.server
app = app.server

if __name__ == "__main__":
    app.run()
