"""Tests for feed fetching with yt-dlp fallback (stdlib unittest only).

Run: python3 -m unittest discover -s tests
"""
import importlib.machinery
import importlib.util
import json
import os
import tempfile
import time
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

_YTV = Path(__file__).resolve().parent.parent / "ytv"
_loader = importlib.machinery.SourceFileLoader("ytv_mod", str(_YTV))
_spec = importlib.util.spec_from_loader("ytv_mod", _loader)
ytv = importlib.util.module_from_spec(_spec)
_loader.exec_module(ytv)

CID = "UCabcdefghijklmnopqrstuv"

RSS_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
      xmlns:media="http://search.yahoo.com/mrss/"
      xmlns="http://www.w3.org/2005/Atom">
 <yt:channelId>{CID}</yt:channelId>
 <entry>
  <yt:videoId>rssVideo001</yt:videoId>
  <yt:channelId>{CID}</yt:channelId>
  <title>RSS video</title>
  <published>2026-11-08T10:00:00+00:00</published>
 </entry>
</feed>"""

YTDLP_OUT = (
    "Fallback video\tdlpVideo001\t1794614400\tNA\t1234\t"
    "https://www.youtube.com/watch?v=dlpVideo001\n"
)


class _Resp:
    def __init__(self, body: str):
        self._body = body.encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _http_404(*_a, **_k):
    raise urllib.error.HTTPError("u", 404, "Not Found", {}, None)


def _ytdlp_ok(*_a, **_k):
    return mock.Mock(stdout=YTDLP_OUT, returncode=0)


def _ytdlp_empty(*_a, **_k):
    return mock.Mock(stdout="", returncode=1)


class FeedFallbackTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cache = Path(self._tmp.name)
        p = mock.patch.object(ytv, "FEED_CACHE", self.cache)
        p.start()
        self.addCleanup(p.stop)
        self.addCleanup(self._tmp.cleanup)

    def _age(self, path: Path, seconds: int) -> None:
        t = time.time() - seconds
        os.utime(path, (t, t))

    # ── RSS works ──────────────────────────────────────────────────────────
    def test_rss_success_returns_fresh_videos_and_caches_xml(self):
        with mock.patch.object(ytv.urllib.request, "urlopen", return_value=_Resp(RSS_XML)), \
             mock.patch.object(ytv.subprocess, "run") as run:
            videos, fresh = ytv.fetch_channel_videos(CID, "Chan", 3600, force=True)
        self.assertTrue(fresh)
        self.assertEqual([v["id"] for v in videos], ["rssVideo001"])
        self.assertTrue((self.cache / f"{CID}.xml").exists())
        run.assert_not_called()

    # ── RSS 404 → yt-dlp ───────────────────────────────────────────────────
    def test_rss_404_falls_back_to_ytdlp_and_caches_json(self):
        with mock.patch.object(ytv.urllib.request, "urlopen", side_effect=_http_404), \
             mock.patch.object(ytv.subprocess, "run", side_effect=_ytdlp_ok):
            videos, fresh = ytv.fetch_channel_videos(CID, "Chan", 3600, force=True)
        self.assertTrue(fresh)
        self.assertEqual([v["id"] for v in videos], ["dlpVideo001"])
        self.assertEqual(videos[0]["channel"], "Chan")      # NA → sub name
        self.assertEqual(videos[0]["channel_id"], CID)
        cached = json.loads((self.cache / f"{CID}.json").read_text())
        self.assertEqual(cached[0]["id"], "dlpVideo001")

    def test_fresh_json_cache_is_used_without_network(self):
        (self.cache / f"{CID}.json").write_text(json.dumps(
            [{"url": "u", "id": "cachedJson1", "title": "t", "channel": "Chan",
              "channel_id": CID, "date": "", "ts": 1.0, "views": ""}]))
        with mock.patch.object(ytv.urllib.request, "urlopen") as uo, \
             mock.patch.object(ytv.subprocess, "run") as run:
            videos, fresh = ytv.fetch_channel_videos(CID, "Chan", 3600)
        self.assertTrue(fresh)
        self.assertEqual(videos[0]["id"], "cachedJson1")
        uo.assert_not_called()
        run.assert_not_called()

    # ── Both fail → stale cache, flagged ───────────────────────────────────
    def test_both_fail_uses_stale_cache_and_flags_it(self):
        xml = self.cache / f"{CID}.xml"
        xml.write_text(RSS_XML)
        self._age(xml, 4 * 86400)
        with mock.patch.object(ytv.urllib.request, "urlopen", side_effect=_http_404), \
             mock.patch.object(ytv.subprocess, "run", side_effect=_ytdlp_empty):
            videos, fresh = ytv.fetch_channel_videos(CID, "Chan", 3600)
        self.assertFalse(fresh)
        self.assertEqual([v["id"] for v in videos], ["rssVideo001"])

    def test_stale_cache_prefers_newest_of_xml_and_json(self):
        xml = self.cache / f"{CID}.xml"
        js = self.cache / f"{CID}.json"
        xml.write_text(RSS_XML)
        js.write_text(json.dumps([{"url": "u", "id": "newerJson01", "title": "t",
                                   "channel": "Chan", "channel_id": CID,
                                   "date": "", "ts": 1.0, "views": ""}]))
        self._age(xml, 5 * 86400)
        self._age(js, 2 * 86400)
        with mock.patch.object(ytv.urllib.request, "urlopen", side_effect=_http_404), \
             mock.patch.object(ytv.subprocess, "run", side_effect=_ytdlp_empty):
            videos, fresh = ytv.fetch_channel_videos(CID, "Chan", 3600)
        self.assertFalse(fresh)
        self.assertEqual(videos[0]["id"], "newerJson01")

    def test_everything_fails_with_no_cache(self):
        with mock.patch.object(ytv.urllib.request, "urlopen", side_effect=_http_404), \
             mock.patch.object(ytv.subprocess, "run", side_effect=_ytdlp_empty):
            videos, fresh = ytv.fetch_channel_videos(CID, "Chan", 3600)
        self.assertFalse(fresh)
        self.assertEqual(videos, [])

    def test_corrupt_json_cache_is_ignored(self):
        (self.cache / f"{CID}.json").write_text("{not json")
        with mock.patch.object(ytv.urllib.request, "urlopen", side_effect=_http_404), \
             mock.patch.object(ytv.subprocess, "run", side_effect=_ytdlp_empty):
            videos, fresh = ytv.fetch_channel_videos(CID, "Chan", 3600)
        self.assertEqual(videos, [])
        self.assertFalse(fresh)

    # ── Aggregation ────────────────────────────────────────────────────────
    def test_get_all_videos_reports_stale_count(self):
        subs = [{"id": "A", "name": "a"}, {"id": "B", "name": "b"}]
        results = {
            "A": ([{"id": "x", "ts": 2.0}], True),
            "B": ([{"id": "y", "ts": 1.0}], False),
        }
        cfg = {"fetch_workers": 2, "cache_ttl": 3600, "max_videos": 10}
        with mock.patch.object(ytv, "fetch_channel_videos",
                               side_effect=lambda cid, *_a, **_k: results[cid]):
            videos, stale = ytv.get_all_videos(subs, cfg)
        self.assertEqual([v["id"] for v in videos], ["x", "y"])
        self.assertEqual(stale, 1)

    def test_header_mentions_stale_feeds(self):
        self.assertEqual(ytv.main_header(0), ytv._MAIN_HDR)
        self.assertIn("3 feeds stale", ytv.main_header(3))


if __name__ == "__main__":
    unittest.main()
