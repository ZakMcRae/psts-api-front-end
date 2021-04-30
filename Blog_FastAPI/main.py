import fastapi
import uvicorn

from Blog_FastAPI.routers import user_routes

app = fastapi.FastAPI(docs_url=None, redoc_url=None)


def configure_routing():
    app.include_router(user_routes.router, tags=["User"])


if __name__ == "__main__":
    configure_routing()
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
else:
    configure_routing()
