from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from auth_utils import get_current_user

templates = Jinja2Templates(directory="templates")


def get_auth_user(request: Request):
    """Dependency to require authentication for HTML pages, redirects to the login page"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url=f"/auth/login?next={request.url.path}", status_code=303)
    return user
