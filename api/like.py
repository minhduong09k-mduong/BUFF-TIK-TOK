"""
POST /api/like
Body: { "link": "https://vt.tiktok.com/..." }
"""
import asyncio
import json
from http.server import BaseHTTPRequestHandler
from _helper import extract_aweme_id, get_aweme_id_from_api, get_token, send_process


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))
        result = asyncio.run(self._process(body))
        self._json(result)

    async def _process(self, body):
        link = body.get("link", "").strip()
        if not link:
            return {"success": False, "error": "Thiếu link"}

        aweme_id = await extract_aweme_id(link)
        if not aweme_id:
            aweme_id = await get_aweme_id_from_api(link)
        if not aweme_id:
            return {"success": False, "error": "Không thể lấy ID video"}

        token, stats, username = await get_token(aweme_id)
        if not token:
            return {"success": False, "error": "Lấy token thất bại"}

        result = await send_process(aweme_id, token, "like")
        result["aweme_id"] = aweme_id
        result["stats_before"] = stats
        result["username"] = username
        return result

    def _json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args): pass
