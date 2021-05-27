from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from httpx import AsyncClient
from starlette import status

from Blog_FastAPI.util import verify_logged_in
from config import config_settings

router = APIRouter()

templates = Jinja2Templates(directory="templates")


# noinspection PyUnusedLocal
# token not used by dependency - confirms login
@router.get("/post/{post_id}/reply/new")
async def get_new_reply(request: Request, token: str = Depends(verify_logged_in)):
    """Create New Reply - empty form unless round tripped"""
    return templates.TemplateResponse("reply/new_reply.html", {"request": request})


# noinspection DuplicatedCode
# prefer keeping routes as is for clarity
@router.post("/post/{post_id}/reply/new")
async def reply_new_reply(
    request: Request, post_id: int, token: str = Depends(verify_logged_in)
):
    """Create New Reply - pass form data to backend api and handle any errors"""
    form_data = await request.form()
    form_data = dict(form_data)

    # check for blank body and round trip info and errors
    if form_data.get("body") == "":
        form_data["body_error"] = "Body is blank"
        return templates.TemplateResponse(
            "reply/new_reply.html", {"request": request, "form_data": form_data}
        )

    # send user data to backend API - create user endpoint
    header = {"Authorization": f"Bearer {token}"}
    body = {"body": form_data.get("body")}

    async with AsyncClient(base_url=config_settings.api_base_url) as ac:
        resp = await ac.post(f"/post/{post_id}/reply", json=body, headers=header)

    # catch unexpected errors
    if resp.status_code != 201:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server Error - Try again later",
        )

    # success - redirect to post where reply created
    response = RedirectResponse(url=f"/post/{post_id}", status_code=303)
    return response


@router.get("/reply/{reply_id}/delete")
async def get_delete_reply(reply_id: int, token: str = Depends(verify_logged_in)):
    """Delete Reply - pass data to backend api and handle any errors"""
    # get reply info for later redirect - check for errors
    async with AsyncClient(base_url=config_settings.api_base_url) as ac:
        resp = await ac.get(f"/reply/{reply_id}")

    if resp.status_code == 200:
        reply_info = resp.json()

    elif resp.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reply does not exist",
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong",
        )

    # send reply info to backend api
    header = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(base_url=config_settings.api_base_url) as ac:
        resp = await ac.delete(f"/reply/{reply_id}", headers=header)

    # catch error for reply belonging to another user
    if resp.status_code == 401:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This reply belongs to another user",
        )

    # success - redirect back to post and alert user of deleted reply
    response = RedirectResponse(
        url=f"/post/{reply_info.get('post_id')}", status_code=303
    )
    response.set_cookie("alert", "Reply Deleted", max_age=1)
    return response


# noinspection PyUnusedLocal
# token not used by dependency - confirms login
@router.get("/reply/{reply_id}/edit")
async def get_update_reply(
    request: Request, reply_id: int, token: str = Depends(verify_logged_in)
):
    """Update Reply - filled form with existing reply info for user to modify"""
    async with AsyncClient(base_url=config_settings.api_base_url) as ac:
        resp = await ac.get(f"/reply/{reply_id}")

    # if reply does not exist raise 404 error
    if resp.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This reply does not exist",
        )

    form_data = resp.json()

    return templates.TemplateResponse(
        "reply/update_reply.html", {"request": request, "form_data": form_data}
    )


# noinspection DuplicatedCode
# prefer keeping routes as is for clarity
@router.post("/reply/{reply_id}/edit")
async def post_update_reply(
    request: Request, reply_id: int, token: str = Depends(verify_logged_in)
):
    """Update Reply - pass form data to backend api and handle any errors"""
    form_data = await request.form()
    form_data = dict(form_data)

    # check for blank body and round trip info and errors
    if form_data.get("body") == "":
        form_data["body_error"] = "Body is blank"
        return templates.TemplateResponse(
            "reply/update_reply.html", {"request": request, "form_data": form_data}
        )

    # send user data to backend API - create user endpoint
    header = {"Authorization": f"Bearer {token}"}
    body = {"body": form_data.get("body")}

    async with AsyncClient(base_url=config_settings.api_base_url) as ac:
        resp = await ac.put(f"/reply/{reply_id}", json=body, headers=header)

    # catch error for reply belonging to another user
    if resp.status_code == 401:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This reply belongs to another user",
        )

    reply_info = resp.json()

    # success - redirect to post with updated reply
    response = RedirectResponse(
        url=f"/post/{reply_info.get('post_id')}", status_code=303
    )
    return response
