import datetime

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from httpx import AsyncClient

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def home(request: Request):
    """home page - display 10 most recent posts with 3 replies each"""
    # get posts
    async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
        resp = await ac.get("/posts/recent?skip=0&limit=10")

    posts = resp.json()

    # add 3 replies per post
    for post in posts:
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
    """display specific user's recent posts with 3 replies each"""
    # get posts
    async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
        resp = await ac.get(
            f"/user/{user_id}/posts?skip=0&limit=10&sort-newest-first=true"
        )

    posts = resp.json()

    # add 3 replies per post
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
    """New account registration form - empty form unless round tripped"""
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def post_register_account(request: Request):
    """New account registration form - verify submitted info or send back"""
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

    # check for API validation errors - others checked client side in template
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
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie("alert", "Account Created - Please log in", expires=10)
    return response


@router.get("/login")
async def get_login(request: Request):
    """User login - empty form unless round tripped"""
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def post_login(request: Request):
    """User login - verify submitted info or send back"""
    form_data = await request.form()
    form_data = dict(form_data)

    body = {
        "username": form_data.get("username"),
        "password": form_data.get("password"),
    }

    # send user data to backend API - create user endpoint
    async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
        resp = await ac.post("/token", data=body)

    # check for incorrect username or password
    if resp.status_code == 401:
        form_data["username_error"] = "Invalid Username or Password"

        # send back validation errors and form data
        return templates.TemplateResponse(
            "login.html", {"request": request, "form_data": form_data}
        )

    token_info = resp.json()

    # redirect home, alert logged in, give token as cookie
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie("alert", "Logged in", expires=10)
    response.set_cookie(
        "jlt",
        token_info.get("access_token"),
        expires=int(
            token_info.get("expires_at") - datetime.datetime.utcnow().timestamp()
        ),
    )
    return response

    # todo - check expiry time is correct - didn't seem to like floats
