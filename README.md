# ytv

A terminal YouTube viewer. Browse and play recent videos from your subscriptions — no account, no API key, no ads.

```
ytv> █
2024-11-20  Fireship               1.2M  I tried every JS framework (it got weird)
2024-11-20  Theo - t3.gg            89K  The REAL reason I left Vercel
2024-11-19  ThePrimeagen           342K  10x Engineer vs 100x Engineer
2024-11-19  NetworkChuck           512K  I hacked my own network (and it was easy)
2024-11-18  Linus Tech Tips        1.8M  We Bought Every RTX 5090
```

## How it works

1. Reads your subscriptions from `~/.config/ytv/subscriptions.json`
2. Fetches YouTube's Atom RSS feeds for each channel in parallel
3. Presents videos sorted by date in **fzf**
4. Plays with **mpv** in the top-right quarter of your screen

Feeds are cached for 1 hour — startup is instant after the first run.

## Requirements

| Tool | Purpose |
|------|---------|
| Python 3.8+ | Runs the script (stdlib only, no pip deps) |
| [mpv](https://mpv.io/) | Video playback |
| [fzf](https://github.com/junegunn/fzf) | Interactive video picker |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Used by mpv to stream YouTube; also powers search |

## Install

```bash
git clone https://github.com/tlarcombe/ytv
cd ytv
bash install.sh
```

The installer checks for dependencies (installs missing ones on Arch/Debian/Fedora), then symlinks `ytv` to `~/.local/bin/ytv`.

## Subscriptions

ytv manages its own subscription list at `~/.config/ytv/subscriptions.json`.

```bash
# Subscribe to a channel
ytv add @Fireship                           # by handle
ytv add https://www.youtube.com/@Fireship  # by URL
ytv add                                    # interactive: search or paste URL

# Unsubscribe
ytv remove         # fzf picker with multi-select

# List
ytv subs

# Import from a file (OPML, JSON, or plain text URLs)
ytv import subscriptions.opml
```

### Importing an existing subscription list

```bash
# From a YouTube OPML export
ytv import youtube-subscriptions.opml

# From a plain text file (one channel URL per line)
ytv import channels.txt

# From a JSON array [{id, name}, ...]
ytv import subs.json
```

YouTube's OPML export is available via [Google Takeout](https://takeout.google.com/)
under **YouTube and YouTube Music → subscriptions**.

## Usage

```
ytv                      Browse subscription feed
ytv -r                   Force-refresh all feeds
ytv -a                   Audio-only playback
ytv search linux tips    Search YouTube directly
ytv add @Fireship        Subscribe to a channel
ytv remove               Unsubscribe via fzf
ytv subs                 List subscriptions
ytv import subs.opml     Import from file
ytv config               Show configuration
ytv init-config          Write editable config.json
```

### fzf keybindings

**Browse mode** (main feed):

| Key | Action |
|-----|--------|
| `ENTER` | Play selected video(s) |
| `CTRL-A` | Play audio only |
| `CTRL-Y` | Copy URL(s) to clipboard |
| `CTRL-S` | Search YouTube |
| `CTRL-N` | Load more videos from this channel |
| `CTRL-R` | Force-refresh all feeds |
| `TAB` | Toggle multi-select |
| `ESC` | Quit |

**Search / channel panel** (opened via CTRL-S or CTRL-N):

| Key | Action |
|-----|--------|
| `ENTER` | Play |
| `CTRL-A` | Audio only |
| `CTRL-B` | Subscribe to this channel |
| `CTRL-Y` | Copy URL |
| `ESC` | Back to browse |

ytv stays open after launching a video, so you can queue up the next one or keep browsing while it plays.

## Configuration

Run `ytv init-config` to create `~/.config/ytv/config.json`:

```json
{
  "cache_ttl":      3600,
  "max_videos":     500,
  "fetch_workers":  20,
  "mpv_geometry":   "50%x50%-0+0",
  "mpv_extra_args": [],
  "quality":        "bestvideo[height<=720]+bestaudio/best[height<=720]",
  "audio_quality":  "bestaudio/best"
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

### Floating window (tiling WM users)

If your window manager tiles mpv, add a floating rule for windows with title `ytv`, or use:

```json
"mpv_extra_args": ["--ontop", "--no-border"]
```

## Updating

```bash
cd ~/path/to/ytv
git pull
```

The symlink means updates are live immediately — no reinstall needed.

## How feeds work

ytv uses YouTube's public Atom RSS feeds:

```
https://www.youtube.com/feeds/videos.xml?channel_id=UCxxxxxxxxxxxxxxxxxxxxxxx
```

No scraping, no API key. These are public, stable endpoints that return the
15 most recent uploads per channel. Feeds are cached locally; use `CTRL-R` or
`ytv -r` to force a refresh.

For deeper channel browsing (CTRL-N) and search (CTRL-S), ytv uses yt-dlp
to fetch more results directly from YouTube.

## Privacy

- **No Google account** — feeds and search are fetched without authentication
- **No API key** — RSS feeds are public; search is handled by yt-dlp
- Your IP contacts `youtube.com` to fetch feeds and stream video, identical
  to any RSS reader or media player

## Troubleshooting

**mpv geometry ignored** — some tiling WMs override window placement.
Add a floating rule for windows with title `ytv`, or add `--ontop --no-border`
to `mpv_extra_args` in `config.json`.

**Feeds show old videos** — run `ytv -r` to bypass the cache.

**`error: No subscriptions`** — run `ytv add` to subscribe to channels.

## Licence

MIT
