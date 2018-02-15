#!/usr/bin/python

from __future__ import absolute_import, division, print_function, unicode_literals

import unittest

from ethtool_exporter import *


class StatsParserTestCase(unittest.TestCase):

    def setUp(self):
        with open("sample.txt") as f:
            self.testdata = f.read().decode("UTF-8", errors="replace")
        self.sp = StatsParser()

    def test_parse_line_rx_no_dma_resources(self):
        stat = self.sp.parse_line("   rx_no_dma_resources: 590843871")
        self.assertEqual(("ethtool_rx_no_dma_resources", 590843871, []), stat)

    def test_parse_queue_bytes_line(self):
        stat = self.sp.parse_line("     tx_queue_5_bytes: 1467719549558")
        expected = (
            "ethtool_queue_bytes",
            1467719549558,
            [
                ('direction', "tx"),
                ('queue', "5"),
                ],
            )
        self.assertEqual(expected, stat)

    def test_parse_stats(self):
        stats = list(self.sp.collect(self.testdata))
        expected = ("ethtool_rx_no_dma_resources", 590843871, [])
        self.assertIn(expected, stats)
        expected = (
            "ethtool_queue_bytes",
            1467719549558,
            [
                ('direction', "tx"),
                ('queue', "5"),
                ],
            )
        self.assertIn(expected, stats)


if __name__ == "__main__":
    unittest.main()
