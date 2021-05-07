from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from httpx import AsyncClient
from starlette import status

from Blog_FastAPI.util import verify_logged_in

router = APIRouter()

templates = Jinja2Templates(directory="templates")


@router.get("/post/new")
async def get_new_post(request: Request, token: str = Depends(verify_logged_in)):
    """Create New Post - empty form unless round tripped"""
    return templates.TemplateResponse("new_post.html", {"request": request})


@router.post("/post/new")
async def post_new_post(request: Request, token: str = Depends(verify_logged_in)):
    form_data = await request.form()
    form_data = dict(form_data)

    header = {"Authorization": f"Bearer {token}"}
    body = {
        "title": form_data.get("title"),
        "body": form_data.get("body"),
    }

    # send user data to backend API - create user endpoint
    async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
        resp = await ac.post("/post", json=body, headers=header)

    # check for incorrect username or password
    if resp.status_code != 201:
        print(resp.status_code)
        print(resp.json())

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server Error - Try again later",
        )

    response = RedirectResponse(url=f"/post/{resp.json().get('id')}", status_code=303)
    return response


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
