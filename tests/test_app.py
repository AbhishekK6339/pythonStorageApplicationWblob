import sys
import os

# Add the parent directory of the current file to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now you can import modules from the parent directory
from app import create_app

import pytest

@pytest.fixture
def client():
    app = create_app()
    with app.test_client() as client:
        yield client

def test_homepage(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data
    assert b'<html lang="en">' in response.data