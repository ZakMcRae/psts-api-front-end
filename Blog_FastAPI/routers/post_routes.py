from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from httpx import AsyncClient
from starlette import status

from Blog_FastAPI.util import verify_logged_in

router = APIRouter()

templates = Jinja2Templates(directory="templates")


# noinspection PyUnusedLocal
# token not used by dependency confirms login
@router.get("/post/new")
async def get_new_post(request: Request, token: str = Depends(verify_logged_in)):
    """Create New Post - empty form unless round tripped"""
    return templates.TemplateResponse("new_post.html", {"request": request})


# noinspection DuplicatedCode
# prefer keeping routes as is for clarity
@router.post("/post/new")
async def post_new_post(request: Request, token: str = Depends(verify_logged_in)):
    """Create New Post - pass form data to backend api and handle any errors"""
    form_data = await request.form()
    form_data = dict(form_data)

    # check for blank title or body and round trip info and errors
    if form_data.get("title") == "":
        print("title error")
        form_data["title_error"] = "Title is blank"

    if form_data.get("body") == "":
        print("body error")
        form_data["body_error"] = "Body is blank"

    if form_data.get("title_error") or form_data.get("body_error"):
        return templates.TemplateResponse(
            "new_post.html", {"request": request, "form_data": form_data}
        )

    # send user data to backend API - create user endpoint
    header = {"Authorization": f"Bearer {token}"}
    body = {
        "title": form_data.get("title"),
        "body": form_data.get("body"),
    }

    async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
        resp = await ac.post("/post", json=body, headers=header)

    # check for incorrect username or password
    if resp.status_code != 201:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server Error - Try again later",
        )

    # success - redirect to created post
    response = RedirectResponse(url=f"/post/{resp.json().get('id')}", status_code=303)
    return response


# noinspection PyUnusedLocal
# token not used by dependency confirms login
@router.get("/post/{post_id}/edit")
async def get_update_post(
    request: Request, post_id: int, token: str = Depends(verify_logged_in)
):
    """Update Post - filled form with existing post info"""
    async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
        resp = await ac.get(f"/post/{post_id}")

    form_data = resp.json()

    return templates.TemplateResponse(
        "update_post.html", {"request": request, "form_data": form_data}
    )


# noinspection DuplicatedCode
# prefer keeping routes as is for clarity
@router.post("/post/{post_id}/edit")
async def post_update_post(
    request: Request, post_id: int, token: str = Depends(verify_logged_in)
):
    """Update Post - pass form data to backend api and handle any errors"""
    form_data = await request.form()
    form_data = dict(form_data)

    # check for blank title or body and round trip info and errors
    if form_data.get("title") == "":
        print("title error")
        form_data["title_error"] = "Title is blank"

    if form_data.get("body") == "":
        print("body error")
        form_data["body_error"] = "Body is blank"

    if form_data.get("title_error") or form_data.get("body_error"):
        return templates.TemplateResponse(
            "update_post.html", {"request": request, "form_data": form_data}
        )

    # send user data to backend API - create user endpoint
    header = {"Authorization": f"Bearer {token}"}
    body = {
        "title": form_data.get("title"),
        "body": form_data.get("body"),
    }

    async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
        resp = await ac.put(f"/post/{post_id}", json=body, headers=header)

    # catch error for post belonging to another user
    if resp.status_code == 401:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This post belongs to another user",
        )

    # todo - issue with backend API - Async SQLAlchemy not properly updating item in db
    # success - redirect to created post
    response = RedirectResponse(url=f"/post/{post_id}", status_code=303)
    return response


@router.get("/post/{post_id}")
async def get_post(request: Request, post_id: int):
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
