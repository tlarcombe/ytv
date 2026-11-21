"""Tests for the download feature (stdlib unittest only).

Run: python3 -m unittest discover -s tests
"""
import importlib.machinery
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_YTV = Path(__file__).resolve().parent.parent / "ytv"
_loader = importlib.machinery.SourceFileLoader("ytv_dl_mod", str(_YTV))
_spec = importlib.util.spec_from_loader("ytv_dl_mod", _loader)
ytv = importlib.util.module_from_spec(_spec)
_loader.exec_module(ytv)

URL = "https://www.youtube.com/watch?v=abcdefghijk"


class DownloadDirTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_existing_dir_is_used(self):
        dest, err = ytv.download_dir({"download_dir": str(self.root)})
        self.assertEqual((dest, err), (self.root, ""))

    def test_missing_leaf_is_created(self):
        target = self.root / "videos"
        dest, err = ytv.download_dir({"download_dir": str(target)})
        self.assertEqual(dest, target)
        self.assertTrue(target.is_dir())
        self.assertEqual(err, "")

    def test_missing_parent_is_an_error_and_creates_nothing(self):
        target = self.root / "unmounted" / "videos"
        dest, err = ytv.download_dir({"download_dir": str(target)})
        self.assertIsNone(dest)
        self.assertIn("mounted", err)
        self.assertFalse((self.root / "unmounted").exists())

    def test_tilde_is_expanded(self):
        with mock.patch.dict("os.environ", {"HOME": str(self.root)}):
            dest, _ = ytv.download_dir({"download_dir": "~/videos"})
        self.assertEqual(dest, self.root / "videos")


class DownloadCmdTests(unittest.TestCase):
    def test_command_shape(self):
        dest = Path("/nas/videos")
        cmd = ytv.download_cmd([URL], dest, dict(ytv.DEFAULT_CONFIG))
        self.assertEqual(cmd[0], "yt-dlp")
        self.assertEqual(cmd[-2:], ["--", URL])
        self.assertIn("--no-playlist", cmd)
        self.assertEqual(cmd[cmd.index("-P") + 1], "/nas/videos")
        self.assertEqual(cmd[cmd.index("--merge-output-format") + 1], "mp4")
        self.assertEqual(cmd[cmd.index("--download-archive") + 1],
                         "/nas/videos/.ytv-archive")
        self.assertIn("avc1", cmd[cmd.index("-f") + 1])

    def test_custom_format_respected(self):
        cmd = ytv.download_cmd([URL], Path("/x"), {"download_format": "best"})
        self.assertEqual(cmd[cmd.index("-f") + 1], "best")


class DownloadVideosTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.cfg = {**ytv.DEFAULT_CONFIG, "download_dir": str(self.root / "videos")}
        patcher = mock.patch.object(ytv, "_DOWNLOAD_LOG", self.root / "dl.log")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def test_background_spawns_detached_yt_dlp(self):
        with mock.patch.object(ytv.subprocess, "Popen") as popen, \
             mock.patch("sys.stderr", io.StringIO()):
            self.assertTrue(ytv.download_videos([URL], self.cfg))
        args, kwargs = popen.call_args
        argv = args[0]
        self.assertEqual(argv[:2], ["sh", "-c"])
        self.assertIn("yt-dlp", argv)
        self.assertEqual(argv[-1], URL)
        self.assertTrue(kwargs["start_new_session"])
        self.assertIn(str(self.root / "videos"), kwargs["env"]["YTV_OK"])
        self.assertIn(URL, (self.root / "dl.log").read_text())

    def test_unmounted_share_does_not_spawn(self):
        cfg = {**self.cfg, "download_dir": str(self.root / "nope" / "videos")}
        with mock.patch.object(ytv.subprocess, "Popen") as popen, \
             mock.patch("sys.stderr", io.StringIO()):
            self.assertFalse(ytv.download_videos([URL], cfg))
        popen.assert_not_called()

    def test_foreground_returns_exit_status(self):
        with mock.patch.object(ytv.subprocess, "run") as run:
            run.return_value.returncode = 1
            self.assertFalse(ytv.download_videos([URL], self.cfg, background=False))
            run.return_value.returncode = 0
            self.assertTrue(ytv.download_videos([URL], self.cfg, background=False))


if __name__ == "__main__":
    unittest.main()
