from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/test")
async def get_test(request: Request):
    """dev function - delete later"""
    return templates.TemplateResponse("test.html", {"request": request})


@router.get("/alert")
async def get_alert():
    """dev function - delete later"""
    response = RedirectResponse(url="/")
    response.set_cookie("alert", "test alert", expires=3)
    return response
