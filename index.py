"""
Index of available apps as required by gunicorn
"""

from src.app import app

app = app.server

if __name__ == "__main__":
    app.run()
