"""
POST /api/fl
Body: { "username": "tiktok_username", "quantity": 20 }
"""
import asyncio
import json
from http.server import BaseHTTPRequestHandler
from _helper import get_user_info, send_followers


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))
        result = asyncio.run(self._process(body))
        self._json(result)

    async def _process(self, body):
        username = body.get("username", "").replace("@", "").strip()
        quantity = int(body.get("quantity", 20))
        if not username:
            return {"success": False, "error": "Thiếu username"}

        user_info = await get_user_info(username)
        if not user_info or not user_info.get("token"):
            return {"success": False, "error": f"Không lấy được thông tin user: {username}"}

        result = await send_followers(user_info, quantity)
        result["user_info"] = {
            "nickname": user_info.get("nickname"),
            "username": user_info.get("username"),
            "region": user_info.get("region"),
            "followers_count": user_info.get("followers_count"),
        }
        return result

    def _json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args): pass
