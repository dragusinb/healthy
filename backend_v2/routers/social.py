"""Facebook Page auto-posting — OAuth setup + manual controls."""
import os
import logging
import httpx
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel

try:
    from backend_v2.services.social_poster import (
        generate_post_content, generate_full_post, publish_to_facebook,
        exchange_code_for_token, _get_fb_config
    )
    from backend_v2.routers.documents import get_current_user
except ImportError:
    from services.social_poster import (
        generate_post_content, generate_full_post, publish_to_facebook,
        exchange_code_for_token, _get_fb_config
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

    redirect_uri = f"{BASE_URL}/admin/facebook/callback"
    scope = "pages_show_list,pages_manage_posts"

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

    redirect_uri = f"{BASE_URL}/admin/facebook/callback"
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
        raise HTTPException(status_code=400, detail="Facebook not connected. Visit /admin/facebook/auth first.")

    if body.message:
        result = publish_to_facebook(body.message)
        message = body.message
    else:
        post = generate_full_post()
        result = publish_to_facebook(post["content"], image_url=post.get("image_url"))
        message = post["content"]

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    return {"success": True, "post_id": result.get("post_id"), "message": message}


@router.get("/admin/facebook/preview")
def preview_post(user=Depends(get_current_user)):
    """Preview today's auto-generated post without publishing."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    content = generate_post_content()
    return {"content": content}


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
        "auth_url": f"{BASE_URL}/admin/facebook/auth" if not connected else None,
    }


@router.get("/admin/facebook/posts")
def facebook_recent_posts(user=Depends(get_current_user)):
    """Fetch recent posts from the Facebook Page."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    config = _get_fb_config()
    if not config["page_token"] or not config["page_id"]:
        return {"posts": []}

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                f"{FB_GRAPH_URL}/{config['page_id']}/feed",
                params={
                    "access_token": config["page_token"],
                    "fields": "id,message,created_time,full_picture,permalink_url,likes.summary(true),comments.summary(true),shares",
                    "limit": 10,
                },
            )
        if resp.status_code != 200:
            return {"posts": [], "error": resp.json().get("error", {}).get("message", "Failed to fetch")}

        data = resp.json().get("data", [])
        posts = []
        for p in data:
            posts.append({
                "id": p.get("id"),
                "message": p.get("message", ""),
                "created_time": p.get("created_time"),
                "image": p.get("full_picture"),
                "url": p.get("permalink_url"),
                "likes": p.get("likes", {}).get("summary", {}).get("total_count", 0),
                "comments": p.get("comments", {}).get("summary", {}).get("total_count", 0),
                "shares": p.get("shares", {}).get("count", 0),
            })
        return {"posts": posts}
    except Exception as e:
        logger.error(f"Failed to fetch Facebook posts: {e}")
        return {"posts": [], "error": str(e)}


@router.delete("/admin/facebook/posts/{post_id}")
def delete_facebook_post(post_id: str, user=Depends(get_current_user)):
    """Delete a Facebook post."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    config = _get_fb_config()
    if not config["page_token"]:
        raise HTTPException(status_code=400, detail="Facebook not connected")

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.delete(
                f"{FB_GRAPH_URL}/{post_id}",
                params={"access_token": config["page_token"]},
            )
        if resp.status_code == 200:
            return {"success": True}
        else:
            error = resp.json().get("error", {}).get("message", "Delete failed")
            raise HTTPException(status_code=400, detail=error)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
