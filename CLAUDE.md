# ytv - Claude Project Notes

## What this project is
A terminal YouTube viewer (`ytv`) that reads subscriptions from FreeTube's local
database and lets you browse/play recent videos using fzf + mpv. No YouTube
account, no API key, no ads.

## Architecture
- **Single script**: `ytv` (Python 3, stdlib only — no pip dependencies)
- **Feeds**: YouTube Atom RSS feeds (`/feeds/videos.xml?channel_id=...`) — free,
  no auth, returns 15 most recent videos per channel
- **Subscriptions**: Read directly from FreeTube's `profiles.db` (NDJSON format)
- **Cache**: `~/.cache/ytv/feeds/<channel_id>.xml`, TTL-based (default 1 hour)
- **Player**: mpv with `--geometry=50%x50%-0+0` (top-right quarter of screen)
- **Selector**: fzf with hidden URL field, multi-select, CTRL-R refresh

## Key files
| File | Purpose |
|------|---------|
| `ytv` | Main executable script |
| `install.sh` | Dependency checker + symlinker to ~/.local/bin |
| `CLAUDE.md` | This file |
| `README.md` | Public-facing documentation |

## User's environment (winifred)
- OS: Manjaro Linux (Arch-based), hostname `winifred`
- Shell: zsh
- Installed: fzf (`/usr/bin/fzf`), yt-dlp (`/usr/bin/yt-dlp`)
- NOT installed: mpv (install.sh handles this)
- FreeTube DB: `~/.config/FreeTube/profiles.db` (134 subscriptions, NDJSON)
- VLC used for local video — mpv is only for ytv

## Config
- Config file: `~/.config/ytv/config.json` (optional, defaults in script)
- Run `ytv --init-config` to generate it
- Key settings: `mpv_geometry`, `cache_ttl`, `quality`, `freetube_db`

## Update process
```bash
cd ~/projects/FreeTube_Alternative
git pull
# symlink means the update is live immediately
```

## Common tasks for Claude
- **Adding features**: The script is self-contained in `ytv`. Keep it stdlib-only.
- **Changing mpv geometry**: Edit `DEFAULT_CONFIG["mpv_geometry"]` or `config.json`
- **Changing fzf layout**: Edit `run_fzf()` function
- **Debugging feed parsing**: Use `ytv --list-subs` and `ytv --verbose`
- **Testing without mpv**: Set player to `echo` in config for dry-run

## Design constraints
- No external Python packages (stdlib only for portability)
- yt-dlp is available but NOT used for feed fetching (RSS is faster)
- yt-dlp IS used internally by mpv's ytdl hook for actual playback
- Must not interfere with VLC (system default for local video)
- GitHub repo: https://github.com/tlarcombe/ytv
