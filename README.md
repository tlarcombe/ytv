# ytv

A terminal YouTube viewer that reads your subscriptions from [FreeTube](https://freetubeapp.io/) and lets you browse and play recent videos — no account, no API key, no ads.

```
ytv> █
2024-11-20  Fireship               1.2M  I tried every JS framework (it got weird)
2024-11-20  Theo - t3.gg            89K  The REAL reason I left Vercel
2024-11-19  ThePrimeagen           342K  10x Engineer vs 100x Engineer
2024-11-19  NetworkChuck           512K  I hacked my own network (and it was easy)
2024-11-18  Linus Tech Tips        1.8M  We Bought Every RTX 5090
```

## How it works

1. Reads your FreeTube subscription list (`~/.config/FreeTube/profiles.db`)
2. Fetches YouTube's Atom RSS feeds for each channel in parallel
3. Presents videos sorted by date in **fzf**
4. Plays the selection with **mpv** in the top-right quarter of your screen

Feeds are cached for 1 hour — startup is instant after the first run.

## Requirements

| Tool | Purpose |
|------|---------|
| Python 3.8+ | Runs the script (stdlib only, no pip deps) |
| [mpv](https://mpv.io/) | Video playback |
| [fzf](https://github.com/junegunn/fzf) | Interactive video picker |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Used by mpv to stream YouTube |
| [FreeTube](https://freetubeapp.io/) | Source of your subscription list |

## Install

```bash
git clone https://github.com/tlarcombe/ytv
cd ytv
bash install.sh
```

The installer checks for dependencies (and installs missing ones on Arch/Debian/Fedora), then symlinks `ytv` to `~/.local/bin/ytv`.

## Usage

```
ytv                 Browse and play videos
ytv --refresh       Force-refresh all feeds (ignore cache)
ytv --audio         Audio-only playback
ytv --list-subs     List all subscribed channels
ytv --config        Show current configuration
ytv --init-config   Write a default config.json to edit
ytv --verbose       Show feed fetch progress
```

### fzf keybindings

| Key | Action |
|-----|--------|
| `ENTER` | Play selected video(s) |
| `CTRL-A` | Play audio only |
| `CTRL-Y` | Copy URL(s) to clipboard |
| `CTRL-R` | Force-refresh feeds and reopen |
| `TAB` | Toggle multi-select |

## Configuration

Run `ytv --init-config` to create `~/.config/ytv/config.json`:

```json
{
  "freetube_db":    "~/.config/FreeTube/profiles.db",
  "cache_ttl":      3600,
  "max_videos":     500,
  "mpv_geometry":   "50%x50%-0+0",
  "quality":        "bestvideo[height<=720]+bestaudio/best[height<=720]",
  "mpv_extra_args": []
}
```

### `mpv_geometry` positions

| Value | Position |
|-------|----------|
| `50%x50%-0+0` | Top-right quarter (default) |
| `50%x50%+0+0` | Top-left quarter |
| `50%x50%-0-0` | Bottom-right quarter |
| `50%x50%+0-0` | Bottom-left quarter |
| `100%x100%+0+0` | Fullscreen |

### `mpv_extra_args` examples

```json
"mpv_extra_args": ["--ontop", "--no-border"]
```

## Updating

```bash
cd ~/path/to/ytv
git pull
```

The symlink means updates are live immediately — no reinstall needed.

## How subscriptions are read

FreeTube stores your subscriptions in `~/.config/FreeTube/profiles.db` as NDJSON.
Each channel has an ID like `UCxxxxxxxxxxxxxxxxxxxxxxx`, which maps directly to
YouTube's RSS feed URL:

```
https://www.youtube.com/feeds/videos.xml?channel_id=UCxxxxxxxxxxxxxxxxxxxxxxx
```

No scraping, no API key — this is a public, undocumented but stable YouTube endpoint.

## Privacy

- **No Google account required** — feeds are fetched anonymously
- **No API key** — YouTube RSS feeds are public
- Your IP makes requests to `youtube.com` to fetch feeds and stream video;
  this is identical to what any RSS reader or media player does

## Troubleshooting

**`error: FreeTube database not found`**
Run `ytv --config` to see the expected path. If FreeTube is installed as a
Flatpak or Snap, the path may differ — update `freetube_db` in `config.json`.

**mpv geometry ignored**
Some tiling window managers (i3, sway, Hyprland) manage window placement
themselves. Add `--floating` rules for `mpv` in your WM config, or use
`mpv_extra_args` to float it.

**Feeds show old videos**
Run `ytv --refresh` to bypass the cache and re-fetch all feeds.

## Licence

MIT
