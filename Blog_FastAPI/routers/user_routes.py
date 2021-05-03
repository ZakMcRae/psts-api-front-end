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

    return templates.TemplateResponse(
        "home.html", {"request": request, "posts": posts, "title": "Home"}
    )


@router.get("/user/{user_id}")
async def users_posts(request: Request, user_id: int):
    async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
        resp = await ac.get(
            f"/user/{user_id}/posts?skip=0&limit=10&sort-newest-first=true"
        )

    posts = resp.json()

    for i, post in enumerate(posts):
        async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
            resp = await ac.get(
                f"/post/{post.get('id')}/replies?skip=0&limit=3&sort-newest-first=false"
            )
        post["replies"] = resp.json()

    return templates.TemplateResponse(
        "user_posts.html",
        {
            "request": request,
            "posts": posts,
            "title": f"{posts[0].get('username')}'s Posts",
        },
    )


@router.get("/register")
async def get_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def post_register(request: Request):
    form_data = await request.form()

    body = {
        "username": form_data.get("username"),
        "email": form_data.get("email"),
        "password": form_data.get("password"),
    }

    # send user data to backend API - create user endpoint
    async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
        resp = await ac.post("/user", json=body)

    # todo round trip form data
    # round trip form data to user if an 409 conflict
    if resp.status_code == 409:
        return templates.TemplateResponse("register.html", {"request": request})

    return resp.json(), resp.status_code
