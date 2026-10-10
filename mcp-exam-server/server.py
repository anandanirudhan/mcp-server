import contextvars
import hashlib
import os

from mcp.server.fastmcp import FastMCP, Context
from starlette.datastructures import Headers

EMAIL = "22f3000311@ds.study.iitm.ac.in"

# Holds the challenge for the current asynchronous request.
current_challenge = contextvars.ContextVar("current_challenge", default=None)

mcp = FastMCP(
    "Exam Challenge Server",
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
async def solve_challenge(ctx: Context) -> str:
    """Return the required hash for the current HTTP challenge."""
    challenge = current_challenge.get()

    if not challenge:
        raise ValueError("Missing X-Exam-Challenge HTTP header")

    result = hashlib.sha256(
        f"{challenge}:{EMAIL}".encode("utf-8")
    ).hexdigest()[:16]

    return result


class ChallengeHeaderMiddleware:
    """Capture X-Exam-Challenge separately for every HTTP request."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        challenge = headers.get("x-exam-challenge")
        token = current_challenge.set(challenge)

        try:
            await self.app(scope, receive, send)
        finally:
            current_challenge.reset(token)


app = ChallengeHeaderMiddleware(mcp.streamable_http_app())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
    )
