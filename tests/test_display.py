"""Tests for the fzf display line and search result dates (stdlib unittest only).

Run: python3 -m unittest discover -s tests
"""
import importlib.machinery
import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest import mock

_YTV = Path(__file__).resolve().parent.parent / "ytv"
_loader = importlib.machinery.SourceFileLoader("ytv_mod_display", str(_YTV))
_spec = importlib.util.spec_from_loader("ytv_mod_display", _loader)
ytv = importlib.util.module_from_spec(_spec)
_loader.exec_module(ytv)


def _video(**over) -> dict:
    v = {
        "url": "https://www.youtube.com/watch?v=abc123",
        "id": "abc123",
        "title": "Windows Are Absurd",
        "channel": "Practical Engineering",
        "channel_id": "UCxyz",
        "date": "2026-11-04",
        "views": "1.0M",
    }
    v.update(over)
    return v


class ShortDateTest(unittest.TestCase):
    def test_iso_date_becomes_dd_mm_yy(self):
        self.assertEqual(ytv._short_date("2026-11-04"), "04/11/26")

    def test_missing_date_is_blank_padded(self):
        self.assertEqual(ytv._short_date(""), " " * 8)

    def test_bad_date_is_blank_padded(self):
        self.assertEqual(ytv._short_date("not-a-date"), " " * 8)


class FmtLineTest(unittest.TestCase):
    def test_short_date_sits_just_before_title(self):
        display = ytv._fmt_line(_video()).split("\t")[5]
        self.assertTrue(display.endswith("04/11/26  Windows Are Absurd"), display)
        self.assertTrue(display.startswith("Practical Engineering"), display)

    def test_hidden_date_field_keeps_full_iso_date(self):
        fields = ytv._fmt_line(_video()).split("\t")
        self.assertEqual(fields[2], "2026-11-04")

    def test_titles_align_when_date_missing(self):
        with_date = ytv._fmt_line(_video()).split("\t")[5]
        no_date = ytv._fmt_line(_video(date="")).split("\t")[5]
        title = "Windows Are Absurd"
        self.assertEqual(with_date.index(title), no_date.index(title))


class SearchDateTest(unittest.TestCase):
    def test_search_results_carry_publish_date(self):
        out = (
            "Transmission Towers\tvid00000001\tUCxyz\tPractical Engineering\t"
            "5000\thttps://www.youtube.com/watch?v=vid00000001\t1795046400\n"
        )
        done = subprocess.CompletedProcess([], 0, stdout=out, stderr="")
        with mock.patch.object(ytv.subprocess, "run", return_value=done):
            videos = ytv.search_youtube("towers", {}, limit=1)
        self.assertEqual(videos[0]["date"], "2026-11-19")
        self.assertEqual(videos[0]["ts"], 1795046400.0)

    def test_search_result_without_timestamp_has_blank_date(self):
        out = (
            "No Date\tvid00000002\tUCxyz\tSomeone\tNA\t"
            "https://www.youtube.com/watch?v=vid00000002\tNA\n"
        )
        done = subprocess.CompletedProcess([], 0, stdout=out, stderr="")
        with mock.patch.object(ytv.subprocess, "run", return_value=done):
            videos = ytv.search_youtube("x", {}, limit=1)
        self.assertEqual(videos[0]["date"], "")


if __name__ == "__main__":
    unittest.main()
