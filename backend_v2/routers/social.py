"""Facebook Page auto-posting — OAuth setup + manual controls."""
import os
import logging
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel

try:
    from backend_v2.services.social_poster import (
        generate_post_content, publish_to_facebook, exchange_code_for_token, _get_fb_config
    )
    from backend_v2.routers.documents import get_current_user
except ImportError:
    from services.social_poster import (
        generate_post_content, publish_to_facebook, exchange_code_for_token, _get_fb_config
    )
    from routers.documents import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["social"])

BASE_URL = "https://analize.online"
FB_GRAPH_URL = "https://graph.facebook.com/v25.0"


@router.get("/admin/facebook/auth", include_in_schema=False)
def facebook_auth_redirect(request: Request):
    """Redirect admin to Facebook OAuth to authorize page posting."""
    config = _get_fb_config()
    if not config["app_id"]:
        raise HTTPException(status_code=500, detail="FB_APP_ID not configured in .env")

    redirect_uri = f"{BASE_URL}/api/admin/facebook/callback"
    scope = "pages_manage_posts,pages_read_engagement,pages_show_list"

    oauth_url = (
        f"https://www.facebook.com/v25.0/dialog/oauth?"
        f"client_id={config['app_id']}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&response_type=code"
    )

    return RedirectResponse(url=oauth_url)


@router.get("/admin/facebook/callback", include_in_schema=False)
def facebook_auth_callback(code: str = None, error: str = None):
    """Handle Facebook OAuth callback — exchange code for page token."""
    if error:
        return HTMLResponse(content=f"""
        <html><body style="font-family:sans-serif;padding:40px;text-align:center">
        <h2 style="color:red">Facebook Authorization Failed</h2>
        <p>{error}</p>
        <a href="/admin/facebook/auth">Try Again</a>
        </body></html>
        """, status_code=400)

    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received")

    redirect_uri = f"{BASE_URL}/api/admin/facebook/callback"
    result = exchange_code_for_token(code, redirect_uri)

    if result.get("error"):
        return HTMLResponse(content=f"""
        <html><body style="font-family:sans-serif;padding:40px;text-align:center">
        <h2 style="color:red">Token Exchange Failed</h2>
        <p>{result['error']}</p>
        <a href="/admin/facebook/auth">Try Again</a>
        </body></html>
        """, status_code=400)

    page_id = result["page_id"]
    page_name = result.get("page_name", "Unknown")
    page_token = result["page_token"]

    return HTMLResponse(content=f"""
    <html><body style="font-family:sans-serif;padding:40px;max-width:600px;margin:auto">
    <h2 style="color:green">Facebook Connected Successfully!</h2>
    <p><strong>Page:</strong> {page_name}</p>
    <p><strong>Page ID:</strong> {page_id}</p>
    <p style="margin-top:20px">Add these to your <code>.env</code> file on the server:</p>
    <pre style="background:#f0f0f0;padding:15px;border-radius:8px;overflow-x:auto;font-size:14px">
FB_PAGE_ID={page_id}
FB_PAGE_TOKEN={page_token}
    </pre>
    <p style="margin-top:20px">Then restart the API:</p>
    <pre style="background:#f0f0f0;padding:15px;border-radius:8px;font-size:14px">sudo systemctl restart healthy-api</pre>
    <p style="color:#666;margin-top:20px;font-size:13px">This token never expires as long as the app stays authorized.</p>
    </body></html>
    """)


class PostRequest(BaseModel):
    message: str = None


@router.post("/admin/facebook/post")
def manual_facebook_post(body: PostRequest, user=Depends(get_current_user)):
    """Manually publish a post to Facebook Page (admin only)."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    config = _get_fb_config()
    if not config["page_token"]:
        raise HTTPException(status_code=400, detail="Facebook not connected. Visit /api/admin/facebook/auth first.")

    message = body.message
    if not message:
        message = generate_post_content()

    result = publish_to_facebook(message)
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    return {"success": True, "post_id": result.get("post_id"), "message": message}


@router.get("/admin/facebook/preview")
def preview_post(user=Depends(get_current_user)):
    """Preview today's auto-generated post without publishing."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    content = generate_post_content()
    return {"content": content, "note": "This is a preview. Use POST /admin/facebook/post to publish."}


@router.get("/admin/facebook/status")
def facebook_status(user=Depends(get_current_user)):
    """Check Facebook connection status."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    config = _get_fb_config()
    connected = bool(config["page_token"] and config["page_id"])

    return {
        "connected": connected,
        "page_id": config["page_id"] if connected else None,
        "app_id": config["app_id"] or None,
        "auth_url": f"{BASE_URL}/api/admin/facebook/auth" if not connected else None,
    }
