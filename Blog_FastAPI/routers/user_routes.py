from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
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
async def get_register_account(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def post_register_account(request: Request):
    form_data = await request.form()
    form_data = dict(form_data)

    body = {
        "username": form_data.get("username"),
        "email": form_data.get("email"),
        "password": form_data.get("password"),
    }

    # send user data to backend API - create user endpoint
    async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
        resp = await ac.post("/user", json=body)
    response_detail = resp.json().get("detail")

    # check for validation errors
    if resp.status_code == 409:
        if response_detail == "Username is taken, please try another":
            form_data["username_error"] = response_detail

        if response_detail == "Email is taken, please try another":
            form_data["email_error"] = response_detail

        # send back validation errors and form data
        return templates.TemplateResponse(
            "register.html", {"request": request, "form_data": form_data}
        )

    # redirect to login page and alert account created
    response = RedirectResponse(url="/")
    response.set_cookie("alert", "Account Created - Please log in")
    return response
