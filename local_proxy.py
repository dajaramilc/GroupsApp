import re
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask
import os

app = FastAPI()

# Mount static files first
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return Response(content=f.read(), media_type="text/html")

@app.get("/style.css")
def read_css():
    with open("static/style.css", "r", encoding="utf-8") as f:
        return Response(content=f.read(), media_type="text/css")

@app.get("/app.js")
def read_js():
    with open("static/app.js", "r", encoding="utf-8") as f:
        return Response(content=f.read(), media_type="application/javascript")

client = httpx.AsyncClient()

# Regex patterns that mirror the nginx.conf routing
# These must be checked BEFORE simple prefix matching
REGEX_ROUTES = [
    # /messages/{id}/attachments → svc-files
    (re.compile(r"^messages/[^/]+/attachments"), 8006),
    # /channels/{id}/messages* → svc-messages
    (re.compile(r"^channels/[^/]+/messages"), 8005),
    # /users/{id}/messages* → svc-messages
    (re.compile(r"^users/[^/]+/messages"), 8005),
    # /users/{id}/presence → svc-presence
    (re.compile(r"^users/[^/]+/presence"), 8007),
    # /groups/{id}/channels* → svc-channels
    (re.compile(r"^groups/[^/]+/channels"), 8004),
    # /groups/{id}/members* → svc-groups
    (re.compile(r"^groups/[^/]+/members"), 8003),
]

# Simple prefix routing (fallback)
PREFIX_ROUTES = {
    "auth": 8001,
    "users": 8002,
    "groups": 8003,
    "channels": 8004,
    "messages": 8005,
    "conversations": 8005,
    "attachments": 8006,
    "presence": 8007,
}


def resolve_port(path: str) -> int | None:
    """Determine which microservice port to route to, matching nginx.conf logic."""
    # 1. Check regex routes first (more specific)
    for pattern, port in REGEX_ROUTES:
        if pattern.match(path):
            return port

    # 2. Fallback to prefix routing
    first_part = path.split("/")[0] if path else ""
    return PREFIX_ROUTES.get(first_part)


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy(request: Request, path: str):
    if path == "health":
        return {"status": "ok", "service": "api-gateway"}

    port = resolve_port(path)
    if port is None:
        print(f"DEBUG: No route found for path: {path}")
        return Response("Not Found", status_code=404)

    url = f"http://localhost:{port}/{path}"
    if request.url.query:
        url += f"?{request.url.query}"

    print(f"DEBUG: Routing {request.method} /{path} to port {port}")

    req = client.build_request(
        request.method,
        url,
        headers=request.headers.raw,
        content=await request.body()
    )
    
    resp = await client.send(req, stream=True)
    return StreamingResponse(
        resp.aiter_raw(),
        status_code=resp.status_code,
        headers=resp.headers,
        background=BackgroundTask(resp.aclose)
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
