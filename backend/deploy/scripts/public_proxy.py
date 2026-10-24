"""HTTPS demo entry point to the private application load balancer."""

import base64
import http.client
import os

HOP_HEADERS = {"connection", "transfer-encoding", "keep-alive", "content-length", "upgrade"}


def handler(event, context):
    request = event.get("requestContext", {})
    method = request.get("http", {}).get("method", "GET")
    path = event.get("rawPath", "/")
    if not path.startswith("/"):
        return {"statusCode": 400, "body": "Invalid request path"}
    query = event.get("rawQueryString", "")
    if query:
        path += "?" + query
    headers = {
        key: value
        for key, value in event.get("headers", {}).items()
        if key.lower() not in HOP_HEADERS
        and key.lower() not in {"host", "x-forwarded-host", "x-forwarded-proto"}
    }
    host = request["domainName"]
    headers.update({"Host": host, "X-Forwarded-Host": host, "X-Forwarded-Proto": "https"})
    if event.get("cookies"):
        headers["Cookie"] = "; ".join(event["cookies"])
    body = event.get("body")
    if body is not None:
        body = base64.b64decode(body) if event.get("isBase64Encoded") else body.encode()
    connection = http.client.HTTPConnection(os.environ["ORIGIN_DNS"], 80, timeout=110)
    try:
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        data = response.read()
        pairs = response.getheaders()
        return {
            "statusCode": response.status,
            "headers": {
                key: value
                for key, value in pairs
                if key.lower() not in HOP_HEADERS | {"set-cookie"}
            },
            "cookies": [value for key, value in pairs if key.lower() == "set-cookie"],
            "body": base64.b64encode(data).decode(),
            "isBase64Encoded": True,
        }
    except (OSError, http.client.HTTPException):
        return {
            "statusCode": 503,
            "headers": {"content-type": "application/json", "cache-control": "no-store"},
            "body": '{"error":{"message":"The demo is starting. Please retry shortly."}}',
        }
    finally:
        connection.close()
