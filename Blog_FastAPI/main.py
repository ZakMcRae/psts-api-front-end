import fastapi
import uvicorn
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from Blog_FastAPI.routers import user_routes, post_routes, dev_routes, reply_routes

# html template for handling errors
templates = Jinja2Templates(directory="templates")


async def http_exception_handler(request: Request, exception: StarletteHTTPException):
    """Catch http errors and returns an html template that gives specific error info"""
    return templates.TemplateResponse(
        "http_status_errors.html", {"request": request, "exception": exception}
    )


exception_handlers = {StarletteHTTPException: http_exception_handler}

# todo modals on delete of post or reply for confirmation
# todo play with alert colour

# todo turn off docs urls after dev work finished - uncomment below
app = fastapi.FastAPI(
    exception_handlers=exception_handlers
)  # , docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")


def configure_routing():
    """Includes endpoints into app from specific routers stored elsewhere for organization purposes"""
    app.include_router(user_routes.router)
    app.include_router(post_routes.router)
    app.include_router(reply_routes.router)
    app.include_router(dev_routes.router)


if __name__ == "__main__":
    configure_routing()
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
else:
    configure_routing()
