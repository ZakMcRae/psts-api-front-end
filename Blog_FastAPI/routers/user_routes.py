from typing import Optional

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from httpx import AsyncClient
from starlette import status

from Blog_FastAPI.util import get_user_info, verify_logged_in
from Blog_FastAPI.config import config_settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def home(request: Request):
    """If logged in return recent activity, otherwise show landing page"""
    if request.cookies.get("jlt"):
        response = RedirectResponse(url="/recent", status_code=303)
        return response

    return templates.TemplateResponse(
        "landing.html", {"request": request, "title": "Home"}
    )


@router.get("/recent")
async def get_recent_activity(request: Request, page: Optional[int] = 1):
    """Display 10 most recent posts with 3 replies each. Pagination to allow viewing of older posts"""
    # get posts
    if page == 1:
        skip = 0
    else:
        skip = page * 10 - 10

    async with AsyncClient(base_url=config_settings.api_base_url) as ac:
        resp = await ac.get(f"/posts/recent?skip={skip}&limit=10")

    posts = resp.json()

    # todo new api endpoint /post/replies
    # add 3 replies per post
    for post in posts:
        async with AsyncClient(base_url=config_settings.api_base_url) as ac:
            resp = await ac.get(
                f"/post/{post.get('id')}/replies?skip=0&limit=3&sort-newest-first=false"
            )
        post["replies"] = resp.json()

    # get user info to display options for editing or deleting own posts/replies
    user_info = await get_user_info(request)

    return templates.TemplateResponse(
        "post/show_posts.html",
        {
            "request": request,
            "posts": posts,
            "title": "Recent Activity",
            "subtitle": "See what everybody has been up to",
            "user_info": user_info,
            "blog_base_url": config_settings.blog_base_url,
            "page": page,
        },
    )


# noinspection PyUnusedLocal
# token not used by dependency - confirms login
@router.get("/user/me/posts")
async def get_my_posts(request: Request, token: str = Depends(verify_logged_in)):
    user_info = await get_user_info(request)

    response = RedirectResponse(
        url=f"/user/{user_info.get('id')}/posts", status_code=303
    )
    return response


@router.get("/user/{user_id}/posts")
async def get_users_posts(request: Request, user_id: int):
    """display specific user's recent posts with 3 replies each"""
    # get posts
    async with AsyncClient(base_url=config_settings.api_base_url) as ac:
        resp = await ac.get(
            f"/user/{user_id}/posts?skip=0&limit=10&sort-newest-first=true"
        )

    posts = resp.json()

    # add 3 replies per post
    for post in posts:
        async with AsyncClient(base_url=config_settings.api_base_url) as ac:
            resp = await ac.get(
                f"/post/{post.get('id')}/replies?skip=0&limit=3&sort-newest-first=false"
            )
        post["replies"] = resp.json()

    # get user info to display options for editing or deleting own posts/replies
    user_info = await get_user_info(request)

    return templates.TemplateResponse(
        "post/show_posts.html",
        {
            "request": request,
            "posts": posts,
            "title": f"{posts[0].get('username')}'s Posts",
            "subtitle": "Here's what I've been up to",
            "user_info": user_info,
            "blog_base_url": config_settings.blog_base_url,
        },
    )


@router.get("/user/{user_id}")
async def get_user_page(request: Request, user_id: int):
    # get user info
    async with AsyncClient(base_url=config_settings.api_base_url) as ac:
        resp = await ac.get(f"/user/{user_id}")

    user_info = resp.json()

    # get list of users the page owner is following
    async with AsyncClient(base_url=config_settings.api_base_url) as ac:
        resp = await ac.get(f"/user/{user_id}/followers")

    following = resp.json()

    # get list of users following page owner
    async with AsyncClient(base_url=config_settings.api_base_url) as ac:
        resp = await ac.get(f"/user/{user_id}/following")

    followers = resp.json()

    return templates.TemplateResponse(
        "user/profile.html",
        {
            "request": request,
            "user_info": user_info,
            "followers": followers,
            "following": following,
        },
    )


@router.get("/register")
async def get_register_account(request: Request):
    """New account registration form - empty form unless round tripped"""
    return templates.TemplateResponse("user/register.html", {"request": request})


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
    async with AsyncClient(base_url=config_settings.api_base_url) as ac:
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
            "user/register.html", {"request": request, "form_data": form_data}
        )

    # redirect to login page and alert account created
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie("alert", "Account Created - Please log in", max_age=1)
    return response


@router.get("/login")
async def get_login(request: Request):
    """User login - empty form unless round tripped"""
    # if logged in alert and redirect home
    if request.cookies.get("jlt"):
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie("alert", "Already Logged In", max_age=1)

        return response

    return templates.TemplateResponse("user/login.html", {"request": request})


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
    async with AsyncClient(base_url=config_settings.api_base_url) as ac:
        resp = await ac.post("/token", data=body)

    # check for incorrect username or password
    if resp.status_code == 401 or resp.status_code == 422:
        form_data["username_error"] = "Invalid Username or Password"

        # send back validation errors and form data
        return templates.TemplateResponse(
            "user/login.html", {"request": request, "form_data": form_data}
        )

    token_info = resp.json()

    # redirect home, alert logged in, give token as cookie (apx 30 day expiry = 2583360s)
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie("alert", "Logged in", max_age=1)
    response.set_cookie("jlt", token_info.get("access_token"), expires=2583360)
    return response


@router.get("/logout")
async def get_logout(request: Request):
    """Logout user by deleting token cookie or redirect if not logged in"""

    if request.cookies.get("jlt"):
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie("alert", "Logged out", max_age=1)
        response.set_cookie("jlt", "expired", max_age=0)

        return response

    else:
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie("alert", "You are not currently logged in", max_age=1)

        return response


# noinspection PyUnusedLocal
# token not used by dependency - confirms login
@router.get("/account")
async def get_user_account(request: Request, token: str = Depends(verify_logged_in)):
    """User account page - Display user info and relevant links. Also displays list of followers and following users"""
    user_info = await get_user_info(request)

    return templates.TemplateResponse(
        "user/account.html",
        {"request": request, "user_info": user_info},
    )


@router.get("/user/{user_id}/follow")
async def get_follow_user(user_id: int, token: str = Depends(verify_logged_in)):
    # send info to backend API - follow user endpoint
    header = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(base_url=config_settings.api_base_url) as ac:
        resp = await ac.post(f"/user/follow/{user_id}", headers=header)

    # catch if user already followed
    if resp.status_code == 409:
        response = RedirectResponse(url=f"/user/{user_id}")
        response.set_cookie("alert", "User already followed", max_age=1)
        return response

    response = RedirectResponse(url=f"/user/{user_id}")
    response.set_cookie("alert", "Now Following", max_age=1)
    return response


@router.get("/user/{user_id}/unfollow")
async def get_unfollow_user(user_id: int, token: str = Depends(verify_logged_in)):
    # send info to backend API - unfollow user endpoint
    header = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(base_url=config_settings.api_base_url) as ac:
        resp = await ac.delete(f"/user/follow/{user_id}", headers=header)

    # catch if user already not followed
    if resp.status_code == 404:
        response = RedirectResponse(url=f"/user/{user_id}")
        response.set_cookie("alert", "User was not being followed", max_age=1)
        return response

    response = RedirectResponse(url=f"/user/{user_id}")
    response.set_cookie("alert", "Now Following", max_age=1)
    return response


# noinspection PyUnusedLocal
# token not used by dependency - confirms login
@router.get("/profile")
async def get_profile(request: Request, token: str = Depends(verify_logged_in)):
    user_info = await get_user_info(request)

    response = RedirectResponse(url=f"/user/{user_info.get('id')}", status_code=303)
    return response


# noinspection PyUnusedLocal
# token not used by dependency - confirms login
@router.get("/following/posts")
async def get_followed_users_posts(
    request: Request, token: str = Depends(verify_logged_in)
):
    user_info = await get_user_info(request)

    # send data to backend API - get posts of followed users
    header = {"Authorization": f"Bearer {token}"}
    async with AsyncClient(base_url=config_settings.api_base_url) as ac:
        resp = await ac.get("/posts/following", headers=header)

    # catch if user has no followers
    if resp.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resp.json().get("detail"),
        )

    posts = resp.json()

    post_ids = [post.get("id") for post in posts]

    # get replies of all posts in post_ids
    async with AsyncClient(base_url=config_settings.api_base_url) as ac:
        resp = await ac.get("/posts/replies", params={"ids": post_ids})

    replies = resp.json()

    # add 3 replies per post
    for post in posts:
        post["replies"] = []
        for reply in replies:
            if post.get("id") == reply.get("post_id"):
                post["replies"].append(reply)
                if len(post["replies"]) == 3:
                    break

    return templates.TemplateResponse(
        "post/show_posts.html",
        {
            "request": request,
            "posts": posts,
            "title": "Followed User's Posts",
            "subtitle": "See what your friends have been up to",
            "user_info": user_info,
            "blog_base_url": config_settings.blog_base_url,
        },
    )
