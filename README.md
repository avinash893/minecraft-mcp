# 🎮 Minecraft MCP Server (Pterodactyl Panel Integration)

An intelligent Model Context Protocol (MCP) server that empowers AI agents (Antigravity, Claude Desktop, Cursor, etc.) to manage, configure, and operate Minecraft servers hosted on Pterodactyl panels.

Built-in support for:
- 🛡️ **Cloudflare Turnstile / Challenge Bypass** (via `undetected-chromedriver`)
- ⏱️ **Automatic Request Pacing & Rate Limiting** to prevent 429/504 gateway timeouts
- 🧠 **Pre-packaged Agent Skills** (`request-pacing` and `minecraft-server-management`)

---

## 🚀 Features & Tools

| Tool | Description |
|---|---|
| `server_status` | View real-time server status, CPU, RAM, disk usage, and node info |
| `power_action` | Power operations: `start`, `stop`, `restart`, `kill` |
| `send_command` | Execute any console command (e.g. `op`, `whitelist`, `say`, `teleport`) |
| `list_files` | Browse server directories (`/`, `/plugins`, `/world`, etc.) |
| `read_file` | Read content of configuration files, logs, or playerdata |
| `write_file` | Create or update files on the server |
| `edit_server_property` | Safely update a single key in `server.properties` |
| `delete_file` | Delete files or directories |
| `rename_file` | Rename or move files across directories |
| `create_folder` | Create directories |
| `install_plugin` | Download and install plugins directly from URLs into `/plugins` |
| `get_download_url` | Obtain temporary signed download URLs for server files |
| `compress_files` | Create `.tar.gz` backups on the server |
| `decompress_file` | Extract `.tar.gz` and `.zip` archives directly on the server |

---

## 📦 Requirements

- **Python**: 3.10 or higher
- **Google Chrome** installed (required by `undetected-chromedriver` for Cloudflare-protected panels)
- A **Pterodactyl Panel account** with an API key

---

## 🛠️ Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Credentials
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Fill in your details in `.env`:
```env
PTERO_URL=https://panel.yourserverhost.com
PTERO_KEY=ptlc_your_account_api_key_here
PTERO_SERVER=your_server_identifier_here
```

> **Where to get your credentials:**
> - `PTERO_URL`: The URL you use to log into your Pterodactyl panel.
> - `PTERO_KEY`: In your panel, go to **Account Settings** -> **API Credentials** -> **Create New**. Copy the token (starts with `ptlc_`).
> - `PTERO_SERVER`: Open your server on the panel. The URL looks like `https://panel.yourhost.com/server/a1b2c3d4` — `a1b2c3d4` is your server identifier.

---

## ⚙️ Connecting to AI Clients

### Antigravity / Gemini CLI
Add this entry to your `mcp_config.json`:
```json
{
  "mcpServers": {
    "minecraft": {
      "command": "python",
      "args": ["path/to/server.py"],
      "env": {
        "PTERO_URL": "https://panel.yourserverhost.com",
        "PTERO_KEY": "ptlc_your_api_key_here",
        "PTERO_SERVER": "your_server_identifier_here"
      }
    }
  }
}
```

### Claude Desktop
Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "minecraft": {
      "command": "python",
      "args": ["<FULL_PATH_TO_SERVER.PY>"],
      "env": {
        "PTERO_URL": "https://panel.yourserverhost.com",
        "PTERO_KEY": "ptlc_your_api_key_here",
        "PTERO_SERVER": "your_server_identifier_here"
      }
    }
  }
}
```

---

## 🧠 Included Agent Skills

This repository includes custom agent skills in `.agents/skills/`:
- **`request-pacing`**: Enforces rate limiting, backoff, and respectful intervals to prevent hitting Cloudflare or panel limits.
- **`minecraft-server-management`**: Guidance for agents handling server power cycles, config edits, and player position / respawn handling.

---

## 📄 License
MIT License. Free to use, adapt, and share.
