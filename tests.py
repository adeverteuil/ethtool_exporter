#!/usr/bin/python

from __future__ import absolute_import, division, print_function, unicode_literals

import unittest

from prometheus_client.core import CounterMetricFamily

from ethtool_exporter import *


class StatsParserTestCase(unittest.TestCase):

    def setUp(self):
        self.collector = EthtoolCollector()
        with open("sample.txt") as f:
            self.collector.fake_data = f.read().decode("UTF-8", errors="replace")

    def test_parse_line_rx_no_dma_resources(self):
        stat = self.collector.parse_line("   rx_no_dma_resources: 590843871")
        self.assertEqual(("ethtool_rx_no_dma_resources", CounterMetricFamily, 590843871, {}), stat)

    def test_parse_queue_bytes_line(self):
        stat = self.collector.parse_line("     tx_queue_5_bytes: 1467719549558")
        expected = (
            "ethtool_tx_queue_bytes",
            CounterMetricFamily,
            1467719549558,
            {
                'queue': "5",
                },
            )
        self.assertEqual(expected, stat)

    def test_parse_stats(self):
        self.collector.fake_data = "   rx_no_dma_resources: 590843871\n"
        self.collector.fake_data += "   tx_queue_5_bytes: 1467719549558\n"
        generator = self.collector.collect()
        metric = generator.next()
        expected = CounterMetricFamily("ethtool_rx_no_dma_resources", "help text", 590843871.0)
        self.assertEqual(expected, metric)
        metric = generator.next()
        expected = CounterMetricFamily("ethtool_tx_queue_bytes", "help text", labels=("queue",))
        expected.add_metric((u"5",), 1467719549558.0)
        self.assertEqual(expected, metric)


if __name__ == "__main__":
    unittest.main()
