import pytest
import fastapi.testclient

import controller


@pytest.fixture
def client():
    with fastapi.testclient.TestClient(controller.app) as client:
        yield client
