from pathlib import Path
from playwright.async_api import async_playwright
from config import get_config
from database import add_log

PROFILE_DIR = str(Path(__file__).parent / "browser_profile")

# 常见中文高校签到系统的字段选择器（按优先级尝试）
ID_SELECTORS = [
    'input[name="username"]', 'input[name="loginName"]',
    'input[name="studentId"]', 'input[name="account"]',
    'input[name="userId"]', 'input[name="user"]',
    'input[placeholder*="学号"]', 'input[placeholder*="账号"]',
    'input[placeholder*="用户名"]',
    'input[type="text"]',
]
PWD_SELECTORS = [
    'input[type="password"]',
]
SUBMIT_SELECTORS = [
    'button[type="submit"]', 'input[type="submit"]',
    'button:text("登录")', 'button:text("签到")',
    'button:text("确认")', 'button:text("提交")',
    'a:text("登录")',
]

# 单例：浏览器上下文复用，保持登录 session
_pw = None
_ctx = None


async def _get_ctx():
    global _pw, _ctx
    if _pw is None:
        _pw = await async_playwright().start()
    if _ctx is None or _ctx.is_closed():
        # 优先用系统已安装的 Chrome，保留原有登录 session
        for launch_kwargs in [
            {"channel": "chrome"},            # 系统 Chrome
            {"channel": "msedge"},            # 系统 Edge
            {},                               # Playwright 内置 Chromium
        ]:
            try:
                _ctx = await _pw.chromium.launch_persistent_context(
                    user_data_dir=PROFILE_DIR,
                    headless=False,
                    no_viewport=True,
                    args=["--no-sandbox", "--disable-dev-shm-usage"],
                    **launch_kwargs,
                )
                break
            except Exception:
                continue
    return _ctx


async def _try_fill(page, selectors: list[str], value: str) -> bool:
    custom = selectors[0] if len(selectors) == 1 else None
    candidates = [custom] if custom else selectors
    for sel in candidates:
        try:
            el = page.locator(sel).first
            if await el.count():
                await el.fill(value)
                return True
        except Exception:
            continue
    return False


async def _try_click(page, selectors: list[str]) -> bool:
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if await el.count():
                await el.click()
                return True
        except Exception:
            continue
    return False


async def do_checkin(qr_url: str) -> tuple[bool, str]:
    if not qr_url.startswith(("http://", "https://")):
        add_log(qr_url, "failed", "非网址，已跳过")
        return False, "非网址，已跳过"

    config = get_config()
    student_id   = config.get("student_id", "")
    password     = config.get("password", "")
    id_sel_cfg   = config.get("id_selector", "").strip()
    pwd_sel_cfg  = config.get("pwd_selector", "").strip()
    sub_sel_cfg  = config.get("submit_selector", "").strip()

    id_sels  = [id_sel_cfg]  if id_sel_cfg  else ID_SELECTORS
    pwd_sels = [pwd_sel_cfg] if pwd_sel_cfg else PWD_SELECTORS
    sub_sels = [sub_sel_cfg] if sub_sel_cfg else SUBMIT_SELECTORS

    try:
        ctx  = await _get_ctx()
        page = await ctx.new_page()
        await page.goto(qr_url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(1000)

        filled = False
        if student_id and password:
            id_ok  = await _try_fill(page, id_sels, student_id)
            pwd_ok = await _try_fill(page, pwd_sels, password)
            if id_ok and pwd_ok:
                clicked = await _try_click(page, sub_sels)
                if not clicked:
                    # 兜底：在密码框按 Enter
                    try:
                        await page.locator(pwd_sels[0]).first.press("Enter")
                        clicked = True
                    except Exception:
                        pass
                filled = clicked

        await page.wait_for_timeout(2000)
        msg = "已自动填写并提交" if filled else "已打开页面（未检测到登录表单）"
        add_log(qr_url, "success", msg)
        return True, msg

    except Exception as e:
        add_log(qr_url, "failed", str(e))
        return False, str(e)
