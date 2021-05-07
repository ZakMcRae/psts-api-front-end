from fastapi import Request, HTTPException
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
