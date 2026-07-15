import httpx
import respx
from assertllm.caller.http import call_endpoint
from assertllm.models.schema import TestConfig


def _test_config(**overrides):
    kwargs = {
        "name": "sample",
        "endpoint": "https://example.com/chat",
        "body": {"message": "hi"},
        "assert": ["is polite"],
    }
    kwargs.update(overrides)
    return TestConfig(**kwargs)


@respx.mock
def test_call_endpoint_returns_status_and_body_on_200():
    respx.post("https://example.com/chat").mock(
        return_value=httpx.Response(200, text="hello there")
    )
    test = _test_config()
    status, body = call_endpoint(test)
    assert status == 200
    assert body == "hello there"


@respx.mock
def test_call_endpoint_does_not_raise_on_401():
    respx.post("https://example.com/chat").mock(
        return_value=httpx.Response(401, text='{"error": "unauthorized"}')
    )
    test = _test_config()
    status, body = call_endpoint(test)
    assert status == 401
    assert "unauthorized" in body


@respx.mock
def test_call_endpoint_does_not_raise_on_500():
    respx.post("https://example.com/chat").mock(
        return_value=httpx.Response(500, text="internal error")
    )
    test = _test_config()
    status, body = call_endpoint(test)
    assert status == 500
    assert body == "internal error"


@respx.mock
def test_call_endpoint_sends_headers_and_body():
    route = respx.post("https://example.com/chat").mock(
        return_value=httpx.Response(200, text="ok")
    )
    test = _test_config(headers={"Authorization": "Bearer tok"}, body={"message": "hi there"})
    call_endpoint(test)
    sent_request = route.calls.last.request
    assert sent_request.headers["Authorization"] == "Bearer tok"
    assert b"hi there" in sent_request.content


@respx.mock
def test_call_endpoint_uses_configured_method():
    route = respx.get("https://example.com/chat").mock(
        return_value=httpx.Response(200, text="ok")
    )
    test = _test_config(method="GET")
    call_endpoint(test)
    assert route.calls.last.request.method == "GET"