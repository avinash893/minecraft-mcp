#!/usr/bin/env python3
"""
Minecraft Server MCP - Pterodactyl Panel Integration
Connects AI agents to manage Minecraft servers hosted on Pterodactyl panels.
Uses undetected-chromedriver to seamlessly bypass Cloudflare protection if enabled.
"""

import asyncio
import json
import os
import sys
import time
import urllib.parse
from typing import Any

# Optional: load .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import undetected_chromedriver as uc
from mcp.server.mcpserver import MCPServer

# ─── CONFIGURATION ───────────────────────────────────────────────────────────
PANEL_URL = os.environ.get("PTERO_URL", "").rstrip("/")
API_KEY = os.environ.get("PTERO_KEY", "")
SERVER_ID = os.environ.get("PTERO_SERVER", "")
HEADLESS = os.environ.get("PTERO_HEADLESS", "false").lower() in ("true", "1", "yes")

# Validate configuration on import / start
if not PANEL_URL or not API_KEY or not SERVER_ID:
    missing = []
    if not PANEL_URL:
        missing.append("PTERO_URL (e.g. https://panel.yourserverhost.com)")
    if not API_KEY:
        missing.append("PTERO_KEY (Account API Key starting with ptlc_)")
    if not SERVER_ID:
        missing.append("PTERO_SERVER (Your server short identifier)")
    print(f"[MCP] Notice: Missing environment variables: {', '.join(missing)}", file=sys.stderr)
    print("[MCP] Please configure them in your environment, .env file, or mcp_config.json.", file=sys.stderr)

mcp = MCPServer("minecraft")
_driver = None


def get_driver(force_restart=False):
    """Get or create an authenticated Chrome session."""
    global _driver
    if force_restart and _driver is not None:
        try:
            _driver.quit()
        except Exception:
            pass
        _driver = None

    if _driver is None:
        if not PANEL_URL:
            raise ValueError("PTERO_URL is not set. Please provide your panel URL.")
        print(f"[MCP] Starting Chrome browser session for {PANEL_URL}...", file=sys.stderr)
        options = uc.ChromeOptions()
        options.add_argument("--window-size=1280,800")
        
        # Check standard cache location or system PATH
        driver_path = os.path.expandvars(r"%APPDATA%\undetected_chromedriver\undetected_chromedriver.exe")
        if os.path.exists(driver_path):
            _driver = uc.Chrome(options=options, driver_executable_path=driver_path, use_subprocess=True, headless=HEADLESS)
        else:
            _driver = uc.Chrome(options=options, use_subprocess=True, headless=HEADLESS)
            
        _driver.get(PANEL_URL)
        for _ in range(30):
            if "just a moment" not in _driver.title.lower():
                break
            time.sleep(2)
        print(f"[MCP] Browser session initialized. Page title: {_driver.title}", file=sys.stderr)
    return _driver


def api_fetch(method: str, path: str, body: Any = None, retries: int = 1) -> Any:
    """Make a Pterodactyl API call through the authenticated Chrome browser."""
    try:
        driver = get_driver()
        url = f"{PANEL_URL}/api/client/servers/{SERVER_ID}{path}"
        body_js = f"body: JSON.stringify({json.dumps(body)})," if body else ""

        script = f"""
        var done = arguments[0];
        fetch({json.dumps(url)}, {{
            method: '{method}',
            headers: {{
                'Authorization': 'Bearer {API_KEY}',
                'Accept': 'Application/vnd.pterodactyl.v1+json',
                'Content-Type': 'application/json',
            }},
            {body_js}
        }}).then(r => r.text().then(t => done({{status: r.status, body: t}})))
          .catch(e => done({{error: String(e)}}));
        """
        result = driver.execute_async_script(script)
        if "error" in result:
            raise RuntimeError(f"Fetch error: {result['error']}")
        if result["status"] >= 400:
            raise RuntimeError(f"API {result['status']}: {result['body'][:300]}")
        text = result["body"]
        time.sleep(1.0)  # Request pacing to avoid rapid bursts
        return json.loads(text) if text.strip() else {"ok": True}
    except Exception as e:
        if "429" in str(e):
            print(f"[MCP] 429 Rate Limit hit. Waiting 15s before retry...", file=sys.stderr)
            time.sleep(15)
            return api_fetch(method, path, body, retries=retries)
        if any(code in str(e) for code in ("504", "502", "503", "524")):
            if retries > 0:
                print(f"[MCP] Gateway Timeout ({e}). Waiting 15s before retry...", file=sys.stderr)
                time.sleep(15)
                return api_fetch(method, path, body, retries=retries - 1)
        if retries > 0 and ("403" in str(e) or "Just a moment" in str(e)):
            print(f"[MCP] Cloudflare challenge / 403: {e}. Refreshing session...", file=sys.stderr)
            time.sleep(5)
            get_driver(force_restart=True)
            return api_fetch(method, path, body, retries=retries - 1)
        raise


def api_text(path: str, retries: int = 2) -> str:
    """Read a raw text file from the server."""
    try:
        driver = get_driver()
        url = f"{PANEL_URL}/api/client/servers/{SERVER_ID}{path}"
        script = f"""
        var done = arguments[0];
        fetch({json.dumps(url)}, {{
            headers: {{
                'Authorization': 'Bearer {API_KEY}',
                'Accept': 'text/plain',
            }}
        }}).then(r => r.text().then(t => done({{status: r.status, body: t}})))
          .catch(e => done({{error: String(e)}}));
        """
        result = driver.execute_async_script(script)
        if "error" in result:
            raise RuntimeError(result["error"])
        if result["status"] >= 400:
            raise RuntimeError(f"API {result['status']}: {result['body'][:300]}")
        time.sleep(1.0)
        return result["body"]
    except Exception as e:
        if "429" in str(e):
            print(f"[MCP] 429 Rate Limit in api_text. Waiting 15s...", file=sys.stderr)
            time.sleep(15)
            return api_text(path, retries=retries)
        if any(code in str(e) for code in ("504", "502", "503", "524")):
            if retries > 0:
                print(f"[MCP] Gateway Timeout in api_text ({e}). Waiting 15s before retry...", file=sys.stderr)
                time.sleep(15)
                return api_text(path, retries=retries - 1)
        if retries > 0 and ("403" in str(e) or "Just a moment" in str(e)):
            print(f"[MCP] api_text retry on Cloudflare challenge: {e}", file=sys.stderr)
            time.sleep(5)
            get_driver(force_restart=True)
            return api_text(path, retries=retries - 1)
        raise


def api_write(file_path: str, content: str) -> None:
    """Write a file via raw text body."""
    driver = get_driver()
    url = f"{PANEL_URL}/api/client/servers/{SERVER_ID}/files/write?file={urllib.parse.quote(file_path)}"
    script = f"""
    var done = arguments[0];
    fetch({json.dumps(url)}, {{
        method: 'POST',
        headers: {{
            'Authorization': 'Bearer {API_KEY}',
            'Content-Type': 'text/plain',
        }},
        body: {json.dumps(content)},
    }}).then(r => r.text().then(t => done({{status: r.status, body: t}})))
      .catch(e => done({{error: String(e)}}));
    """
    result = driver.execute_async_script(script)
    if "error" in result:
        raise RuntimeError(result["error"])
    if result["status"] >= 400:
        raise RuntimeError(f"Write error {result['status']}: {result['body'][:300]}")
    time.sleep(1.0)


# ── MCP TOOLS ────────────────────────────────────────────────────────────────

@mcp.tool(description="Get Minecraft server status: online/offline, RAM usage, CPU, disk, player count.")
def server_status() -> str:
    info = api_fetch("GET", "")
    res  = api_fetch("GET", "/resources")
    a    = info.get("attributes", {})
    r    = res.get("attributes", {}).get("resources", {})
    return json.dumps({
        "name":        a.get("name"),
        "description": a.get("description"),
        "status":      res.get("attributes", {}).get("current_state"),
        "ram_mb":      round(r.get("memory_bytes", 0) / 1048576, 1),
        "cpu_%":       round(r.get("cpu_absolute", 0), 2),
        "disk_mb":     round(r.get("disk_bytes", 0) / 1048576, 1),
        "node":        a.get("node"),
        "sftp_host":   a.get("sftp_details", {}).get("ip"),
        "sftp_port":   a.get("sftp_details", {}).get("port"),
    }, indent=2)


@mcp.tool(description="Control server power state. action can be: 'start', 'stop', 'restart', 'kill'")
def power_action(action: str) -> str:
    api_fetch("POST", "/power", {"signal": action})
    return json.dumps({"ok": True, "action": action, "message": f"Server {action} signal sent."})


@mcp.tool(description="Send any Minecraft console command. Examples: 'say Hello', 'op Player', 'whitelist add Player', 'time set day'")
def send_command(command: str) -> str:
    api_fetch("POST", "/command", {"command": command})
    return json.dumps({"ok": True, "command": command})


@mcp.tool(description="List files and folders in a server directory. Use '/' for root, '/plugins' for plugins folder, etc.")
def list_files(directory: str = "/") -> str:
    data  = api_fetch("GET", f"/files/list?directory={urllib.parse.quote(directory)}")
    files = [
        {
            "name":    i["attributes"].get("name"),
            "is_file": i["attributes"].get("is_file"),
            "size_kb": round(i["attributes"].get("size", 0) / 1024, 1),
            "mime":    i["attributes"].get("mimetype"),
        }
        for i in data.get("data", [])
    ]
    return json.dumps({"directory": directory, "count": len(files), "files": files}, indent=2)


@mcp.tool(description="Read the full text content of any file on the server. Examples: '/server.properties', '/whitelist.json'")
def read_file(file: str) -> str:
    content = api_text(f"/files/contents?file={urllib.parse.quote(file)}")
    return json.dumps({"file": file, "content": content})


@mcp.tool(description="Write or overwrite a file on the server with new text content.")
def write_file(file: str, content: str) -> str:
    api_write(file, content)
    return json.dumps({"ok": True, "file": file, "bytes_written": len(content)})


@mcp.tool(description="Edit a single key=value in server.properties without affecting other settings. Examples: 'max-players', 'difficulty', 'motd', 'online-mode'")
def edit_server_property(key: str, value: str) -> str:
    raw = api_text(f"/files/contents?file={urllib.parse.quote('/server.properties')}")
    lines, found = [], False
    for line in raw.splitlines():
        if line.startswith(f"{key}="):
            lines.append(f"{key}={value}")
            found = True
        else:
            lines.append(line)
    if not found:
        lines.append(f"{key}={value}")
    api_write("/server.properties", "\n".join(lines))
    return json.dumps({
        "ok": True, "key": key, "value": value,
        "was_existing": found,
        "note": "Restart the server for this change to take effect."
    })


@mcp.tool(description="Delete files or folders on the server. root is the parent directory, files is a list of names.")
def delete_file(root: str, files: list) -> str:
    api_fetch("POST", "/files/delete", {"root": root, "files": files})
    return json.dumps({"ok": True, "deleted": files, "from": root})


@mcp.tool(description="Rename or move a file or directory on the server.")
def rename_file(root: str, from_name: str, to_name: str) -> str:
    api_fetch("PUT", "/files/rename", {
        "root": root,
        "files": [{"from": from_name, "to": to_name}]
    })
    return json.dumps({"ok": True, "from": from_name, "to": to_name})


@mcp.tool(description="Create a new folder on the server.")
def create_folder(root: str, name: str) -> str:
    api_fetch("POST", "/files/create-folder", {"root": root, "name": name})
    return json.dumps({"ok": True, "created": f"{root}/{name}"})


@mcp.tool(description="Download and install a plugin JAR from a direct download URL into the /plugins folder.")
def install_plugin(url: str, filename: str) -> str:
    upload_data = api_fetch("GET", "/files/upload")
    upload_url  = upload_data.get("attributes", {}).get("url", "")
    if not upload_url:
        return json.dumps({"error": "Could not get upload URL from panel."})

    driver = get_driver()
    script = f"""
    var done = arguments[0];
    (async function() {{
        try {{
            const dlResp = await fetch({json.dumps(url)});
            if (!dlResp.ok) {{ done({{error: 'Download failed: ' + dlResp.status}}); return; }}
            const blob = await dlResp.blob();
            const form = new FormData();
            form.append('files', blob, {json.dumps(filename)});
            const upResp = await fetch({json.dumps(upload_url)}, {{ method: 'POST', body: form }});
            done({{ ok: upResp.ok, status: upResp.status }});
        }} catch(e) {{ done({{error: String(e)}}); }}
    }})();
    """
    result = driver.execute_async_script(script)
    if not result.get("ok"):
        return json.dumps({"error": f"Upload failed: {result}"})

    try:
        api_fetch("PUT", "/files/rename", {
            "root": "/",
            "files": [{"from": filename, "to": f"/plugins/{filename}"}]
        })
    except Exception:
        pass

    return json.dumps({
        "ok": True,
        "plugin": filename,
        "installed_to": f"/plugins/{filename}",
        "note": "Restart the server for the plugin to load. Use power_action('restart')."
    })


@mcp.tool(description="Get a temporary signed download URL for a file on the server.")
def get_download_url(file: str) -> str:
    data = api_fetch("GET", f"/files/download?file={urllib.parse.quote(file)}")
    return json.dumps({"url": data.get("attributes", {}).get("url")})


@mcp.tool(description="Compress files or folders into a .tar.gz archive on the server.")
def compress_files(root: str, files: list) -> str:
    data = api_fetch("POST", "/files/compress", {"root": root, "files": files})
    return json.dumps({"ok": True, "archive": data.get("attributes", {}).get("name")})


@mcp.tool(description="Extract/decompress an archive (.tar.gz, .zip) on the server.")
def decompress_file(root: str, file: str) -> str:
    api_fetch("POST", "/files/decompress", {"root": root, "file": file})
    return json.dumps({"ok": True, "decompressed": file, "in": root})


# ── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not API_KEY or not SERVER_ID or not PANEL_URL:
        print("[MCP] ERROR: Missing required configuration variables.", file=sys.stderr)
        print("[MCP] Ensure PTERO_URL, PTERO_KEY, and PTERO_SERVER are configured.", file=sys.stderr)
        sys.exit(1)

    # Pre-warm the browser session so the first tool call responds quickly
    try:
        get_driver()
    except Exception as e:
        print(f"[MCP] Warning: Browser session pre-warm encountered: {e}", file=sys.stderr)

    mcp.run(transport="stdio")
