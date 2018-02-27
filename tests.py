#!/usr/bin/env python3

import unittest

from prometheus_client.core import CounterMetricFamily

from ethtool_exporter import *


class StatsParserTestCase(unittest.TestCase):

    def setUp(self):
        self.collector = EthtoolCollector()
        with open("sample.txt") as f:
            self.fake_data = f.read()
        with open("sample_info.txt") as f:
            self.fake_info = f.read()

    def test_parse_line_rx_no_dma_resources(self):
        stat = self.collector.parse_line("   rx_no_dma_resources: 590843871")
        expected = (
            "ethtool_rx_no_dma_resources_total",
            "rx_no_dma_resources",
            [],
            590843871,
            )
        self.assertEqual(expected, stat)

    def test_parse_queue_bytes_line(self):
        stat = self.collector.parse_line("     tx_queue_5_bytes: 1467719549558")
        expected = (
            "ethtool_tx_queue_bytes_total",
            "tx_queue_N_bytes",
            [
                ("queue", "5"),
                ],
            1467719549558,
            )
        self.assertEqual(expected, stat)

    def test_parse_stats(self):
        metrics = list(self.collector.collect(self.fake_data, self.fake_info))
        expected = CounterMetricFamily(
            "ethtool_rx_no_dma_resources_total",
            "rx_no_dma_resources",
            labels=("interface",),
            )
        expected.add_metric(["eth0"], 590843871.0)
        self.assertIn(expected, metrics)
        expected = CounterMetricFamily(
            "ethtool_tx_queue_bytes_total",
            "tx_queue_bytes",
            labels=("interface", "queue"),
            )
        expected.add_metric(("eth0", "5"), 1467719549558.0)
        for m in metrics:
            if m.name == "ethtool_tx_queue_bytes_total":
                self.assertIn(expected.samples[0], m.samples)
            if m.name == "ethtool_interface_speed":
                self.assertEqual(m.samples[0][2], 1048576000.0)


if __name__ == "__main__":
    unittest.main()
