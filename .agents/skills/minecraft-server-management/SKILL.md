---
name: minecraft-server-management
description: >-
  Standard operating procedures and best practices for managing, configuring, and monitoring
  a Minecraft server using the Pterodactyl Minecraft MCP server. Use whenever performing server tasks,
  editing server.properties, handling player positions, whitelists, or power actions.
---

# Minecraft Server Management Guide

## 1. Power State & Lifecycle Operations
- **Starting & Restarting**: Always allow 20–40 seconds for Paper/Spigot/Forge to initialize chunks, worlds, and plugins before pinging or sending console commands.
- **Graceful Shutdown**: Always attempt `send_command("stop")` or `power_action("stop")` before using `power_action("kill")` to ensure world data and playerdata are properly flushed to disk.

## 2. Server Configuration (`server.properties`)
- Use `edit_server_property(key, value)` to update specific options without mangling comments or other settings.
- Common settings:
  - `online-mode`: Set to `false` for offline-mode / test bot networks, `true` for Mojang authenticated accounts.
  - `max-players`: Controls player limit.
  - `difficulty`: `peaceful`, `easy`, `normal`, `hard`.
  - `view-distance` & `simulation-distance`: Adjust for server performance optimization.
- **Always restart** the server after modifying `server.properties` for values to take effect.

## 3. Player Position & Respawn Rules
- **Quit / Rejoin Position**: Player coordinates are stored in `<world>/playerdata/<uuid>.dat`. Do not force players back to lobby on join unless it is their very first join (`!hasPlayedBefore()`).
- **Death Respawn Points**:
  - Vanilla precedence: Individual bed or respawn anchor location, followed by individual `/spawnpoint`, followed by world spawn.
  - When using Multiverse-Core, ensure `enforce-respawn-at-world-spawn: false` and `enable-join-destination: false` in `plugins/Multiverse-Core/config.yml` so player respawns and logout positions are preserved.

## 4. Plugin Management
- Place plugin `.jar` files in `/plugins`.
- Check `/logs/latest.log` via `read_file("/logs/latest.log")` after reboot to ensure no `ClassNotFoundException` or startup crashes occur.

## 5. Network & Rate Limiting
- Strictly follow the `request-pacing` skill: Never query `/resources` or `/command` in unpaused loops.
- Pace requests with a minimum 10-15s gap during boot phases or transient errors.
