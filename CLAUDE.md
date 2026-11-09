# ytv - Claude Project Notes

## What this project is
A terminal YouTube viewer (`ytv`). Browse/play YouTube videos from subscriptions
using fzf + mpv. No account, no API key, no ads.

## Architecture
- **Single script**: `ytv` (Python 3, stdlib only — no pip dependencies)
- **Feeds**: YouTube Atom RSS feeds (`/feeds/videos.xml?channel_id=...`) — free,
  no auth, returns 15 most recent videos per channel
- **Subscriptions**: `~/.config/ytv/subscriptions.json` (list of {id, name})
  - Auto-migrates from `~/.config/FreeTube/profiles.db` on first run if present
- **Search / recommendations**: yt-dlp `ytsearch` and flat-playlist
- **Feed fallback**: YouTube's RSS endpoint has been 404ing for long stretches
  (Oct/Nov 2026). `fetch_channel_videos()` tries fresh cache → RSS → yt-dlp
  (`/channel/<id>/videos`, 15 items) → stale cache. Channels served stale are
  counted and shown as a "⚠ N feeds stale" line in the fzf header.
- **Cache**: `~/.cache/ytv/feeds/<channel_id>.xml` (RSS) or `.json` (yt-dlp),
  newest wins, TTL-based (default 1 hour)
- **Tests**: `python3 -m unittest discover -s tests` (stdlib only, mocked network)
- **Player**: mpv with `--geometry=50%x50%-0+0` (top-right quarter of screen)
- **Selector**: fzf, 6-field tab-separated (url+channel_id hidden, display shown)

## fzf line format
`url\tchannel_id\tdate\tchannel\tviews\tdisplay_string`
- `--with-nth=6` shows only display_string
- `{1}`=url `{2}`=channel_id `{3}`=date `{4}`=channel `{5}`=views in preview

## Key commands (v2.0)
- `ytv` / `ytv browse` — main feed
- `ytv add [channel]` — subscribe (URL, @handle, or search term)
- `ytv remove` — unsubscribe via fzf
- `ytv import <file>` — import OPML/JSON/NDJSON/text
- `ytv search [query]` — search YouTube
- `ytv subs` / `ytv config` / `ytv init-config`

## fzf keybindings
- ENTER/CTRL-A: play / audio-only — **ytv stays open after play**
- CTRL-S: search YouTube (opens search panel)
- CTRL-N: more from channel (opens channel panel via yt-dlp)
- CTRL-R: refresh feeds
- CTRL-B: subscribe to channel (in search/channel panels)
- CTRL-Y: copy URL

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
- Installed: fzf, yt-dlp, mpv (all at /usr/bin/)
- Subscriptions: `~/.config/ytv/subscriptions.json` (134 channels, auto-migrated)
- VLC used for local video — mpv is only for ytv

## Config
- Config file: `~/.config/ytv/config.json` (optional, defaults in script)
- Run `ytv init-config` to generate it
- Key settings: `mpv_geometry`, `cache_ttl`, `quality`

## Update process
```bash
cd ~/projects/FreeTube_Alternative
git pull
# symlink means the update is live immediately
```

## Common tasks for Claude
- **Adding features**: Self-contained in `ytv`. Keep it stdlib-only.
- **Changing mpv geometry**: Edit `DEFAULT_CONFIG["mpv_geometry"]` or `config.json`
- **Changing fzf layout**: Edit `run_fzf()` function
- **Debugging feeds**: `ytv subs` to list, `ytv -v` for verbose fetch
- **Import formats**: OPML, NDJSON, JSON array, plain text (auto-detected)

## Design constraints
- No external Python packages (stdlib only for portability)
- RSS feeds for subscribed channels (fast, cached); yt-dlp for search/deep-dive
- yt-dlp IS used by mpv's ytdl hook for actual streaming
- Must not interfere with VLC (system default for local video)
- GitHub repo: https://github.com/tlarcombe/ytv
- README must not mention FreeTube by name (CLAUDE.md/comments can)
