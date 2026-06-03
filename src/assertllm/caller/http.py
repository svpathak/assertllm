import httpx
from assertllm.models.schema import TestConfig


def call_endpoint(test: TestConfig) -> str:
    with httpx.Client() as client:
        response = client.request(
            method=test.method,
            url=str(test.endpoint),
            headers=test.headers,
            json=test.body,
            timeout=30.0
        )
        response.raise_for_status()
        return response.text