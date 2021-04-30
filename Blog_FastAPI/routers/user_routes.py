from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from httpx import AsyncClient

router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/")
async def home(request: Request):
    async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
        resp = await ac.get("/posts/recent?skip=0&limit=10")

    posts = resp.json()

    for i, post in enumerate(posts):
        async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
            resp = await ac.get(
                f"/post/{post.get('id')}/replies?skip=0&limit=3&sort-newest-first=false"
            )
        post["replies"] = resp.json()

    return templates.TemplateResponse("home.html", {"request": request, "posts": posts})
