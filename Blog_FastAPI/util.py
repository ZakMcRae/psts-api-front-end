from fastapi import Request, HTTPException
from httpx import AsyncClient
from starlette import status


async def verify_logged_in(request: Request) -> str:
    """dependency for returning token if user logged in"""
    # check if logged in (has token cookie jlt)
    if request.cookies.get("jlt") is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized - Please Login",
        )

    return request.cookies.get("jlt")


async def get_user_info(request: Request):
    """Get user info if currently logged in from token/cookie - returns dict with 'id':0 if not logged in. Using to
    compare if logged in user_id is the same as post.user_id and then display links to edit or delete own content."""
    if request.cookies.get("jlt"):
        header = {"Authorization": f"Bearer {request.cookies.get('jlt')}"}
        async with AsyncClient(base_url="http://127.0.0.1:8000") as ac:
            resp = await ac.get("/user/me", headers=header)

        if resp.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=resp.json().get("detail"),
            )

        user_info = resp.json()

    else:
        user_info = {"id": 0}

    return user_info
