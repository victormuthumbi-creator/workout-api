import os
import sys
import tempfile

import pytest

# Point the app at a throwaway database BEFORE it is imported
_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URI"] = f"sqlite:///{_db_file.name}"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app as flask_app  # noqa: E402
from models import db  # noqa: E402


@pytest.fixture
def client():
    with flask_app.app_context():
        db.drop_all()
        db.create_all()
        yield flask_app.test_client()
        db.session.remove()
