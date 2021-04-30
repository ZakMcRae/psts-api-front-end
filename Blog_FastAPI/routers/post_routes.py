from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from httpx import AsyncClient

router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/post/{post_id}")
async def home(request: Request, post_id: int):
    async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
        resp = await ac.get(f"/post/{post_id}")

    posts = resp.json()

    async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
        resp = await ac.get(
            f"/post/{post_id}/replies?skip=0&limit=25&sort-newest-first=false"
        )
    posts["replies"] = resp.json()

    return templates.TemplateResponse(
        "single_post.html",
        {
            "request": request,
            "posts": posts,
            "title": f"{posts.get('title')}",
        },
    )
