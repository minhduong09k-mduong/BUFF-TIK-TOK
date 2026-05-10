"""
Helper dùng chung cho tất cả endpoint Vercel
"""
import re
import asyncio
import aiohttp

MAX_RETRIES = 3
BASE_HEADERS = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}


async def resolve_short_url(short_url: str) -> str:
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(short_url, allow_redirects=True,
                             timeout=aiohttp.ClientTimeout(total=8)) as r:
                return str(r.url)
    except:
        return short_url


async def extract_aweme_id(url: str):
    if 'vt.tiktok.com' in url or 'vm.tiktok.com' in url:
        url = await resolve_short_url(url)
    for pattern in [r'/video/(\d+)', r'@[\w\.]+/video/(\d+)', r'v/(\d+)', r'/(\d{19})']:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None


async def get_aweme_id_from_api(link: str):
    if 'vt.tiktok.com' in link or 'vm.tiktok.com' in link:
        link = await resolve_short_url(link)
    url = f"https://api.like3s.vn/api/extension/find-uid?link={link}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
                data = await r.json()
                if data.get("code") == 200 and data.get("data"):
                    uid = data["data"].get("uid")
                    if uid:
                        return str(uid)
    except:
        pass
    return None


async def get_token(aweme_id: str):
    """Trả về (token, stats, username)"""
    payload = {"input": aweme_id, "type": "videoDetails"}
    connector = aiohttp.TCPConnector(force_close=True)
    async with aiohttp.ClientSession(connector=connector) as s:
        for attempt in range(MAX_RETRIES):
            try:
                async with s.post(
                    "https://tikfollowers.com/api/search",
                    json=payload, headers=BASE_HEADERS,
                    timeout=aiohttp.ClientTimeout(total=8, connect=4, sock_read=6)
                ) as r:
                    if r.status == 200:
                        data = await r.json()
                        if data.get("success"):
                            return data.get("token"), data.get("stats", {}), data.get("username", "")
                    if r.status in (429, 503):
                        await asyncio.sleep(2)
            except:
                pass
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(1)
    return None, {}, ""


async def send_process(aweme_id: str, token: str, type_action: str):
    payload = {
        "type": type_action,
        "token": token,
        "aweme_id": aweme_id,
        "amount": 20,
        "target_identifier": {"aweme_id": aweme_id}
    }
    connector = aiohttp.TCPConnector(force_close=True)
    async with aiohttp.ClientSession(connector=connector) as s:
        for attempt in range(MAX_RETRIES):
            try:
                async with s.post(
                    "https://tikfollowers.com/api/process",
                    json=payload, headers=BASE_HEADERS,
                    timeout=aiohttp.ClientTimeout(total=8, connect=4, sock_read=6)
                ) as r:
                    data = await r.json()
                    if data.get("success") or "Please wait" in str(data.get("message", "")):
                        return data
                    if r.status in (429, 503):
                        await asyncio.sleep(2)
                        continue
                    return data
            except:
                pass
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(1)
    return {"success": False}


async def get_user_info(username: str):
    payload = {"input": username, "type": "getUserDetails"}
    headers = {**BASE_HEADERS, "X-Requested-With": "XMLHttpRequest"}
    for attempt in range(MAX_RETRIES):
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(
                    "https://tikfollowers.com/api/search",
                    json=payload, headers=headers,
                    timeout=aiohttp.ClientTimeout(total=8, connect=4, sock_read=6)
                ) as r:
                    if r.status == 200:
                        data = await r.json()
                        if data.get("success"):
                            return {
                                'token': data.get("token"),
                                'nickname': data.get("nickname"),
                                'username': data.get("username"),
                                'followers_count': data.get("followers_count"),
                                'region': data.get("region"),
                                'user_id': data.get("user_id"),
                                'sec_uid': data.get("sec_uid"),
                            }
        except:
            pass
        if attempt < MAX_RETRIES - 1:
            await asyncio.sleep(1)
    return None


async def send_followers(user_info: dict, quantity: int = 20):
    payload = {
        "username": user_info.get("username"),
        "user_id": user_info.get("user_id"),
        "sec_uid": user_info.get("sec_uid"),
        "token": user_info.get("token"),
        "type": "followers",
        "quantity": quantity
    }
    headers = {**BASE_HEADERS, "X-Requested-With": "XMLHttpRequest"}
    connector = aiohttp.TCPConnector(force_close=True)
    async with aiohttp.ClientSession(connector=connector) as s:
        for attempt in range(MAX_RETRIES):
            try:
                async with s.post(
                    "https://tikfollowers.com/api/process",
                    json=payload, headers=headers,
                    timeout=aiohttp.ClientTimeout(total=8, connect=4, sock_read=6)
                ) as r:
                    data = await r.json()
                    if data.get("success") or "Please wait" in str(data.get("message", "")):
                        return data
                    if r.status in (429, 503):
                        await asyncio.sleep(2)
                        continue
                    return data
            except:
                pass
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(1)
    return {"success": False}
