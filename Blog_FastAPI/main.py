import fastapi
import uvicorn
from fastapi.staticfiles import StaticFiles

from Blog_FastAPI.routers import user_routes, post_routes, dev_routes

app = fastapi.FastAPI(docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")


def configure_routing():
    app.include_router(user_routes.router)
    app.include_router(post_routes.router)
    app.include_router(dev_routes.router)


if __name__ == "__main__":
    configure_routing()
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
else:
    configure_routing()
