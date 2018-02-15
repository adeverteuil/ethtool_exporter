#!/usr/bin/python3

import http.server
import os
import re
import subprocess
import sys
import time

from prometheus_client import start_http_server, Summary
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY
from prometheus_client.exposition import MetricsHandler


class EthtoolCollector(object):

    interesting_items = re.compile(
        r"""\W*(
            rx_no_dma_resources|
            (tx|rx)_queue_(\d+)_(bytes|packets)|
            (rx|tx)_(packets|bytes|broadcast|multicast|errors)
            )
        """,
        re.VERBOSE
        )

    def collect(self, test_data=None):
        self.metric_families = {}
        if test_data is not None:
            self.get_ethtool_stats("eth0", test_data)
        else:
            for interface in self.find_physical_interfaces():
                self.get_ethtool_stats(interface)
        for metric in self.metric_families:
            yield self.metric_families[metric]

    def get_ethtool_stats(self, interface, test_data=None):
        if test_data is not None:
            data = test_data
        else:
            try:
                data = subprocess.check_output(["ethtool", "-S", interface]).decode()
            except subprocess.CalledProcessError as err:
                pass
                #logger.error(
                #    "ethtool returned {} for interface {}".format(
                #        err.returncode,
                #        interface
                #        )
                #    )
        for line in data.splitlines():
            if self.item_is_interesting(line):
                name, documentation, labels, value  = self.parse_line(line)
                labels.insert(0, ("interface", interface))
                self.add_metric(name, documentation, labels, value)

    def add_metric(self, name, documentation, labels, value):
        if name not in self.metric_families:
            label_names = [label[0] for label in labels]
            self.metric_families[name] = CounterMetricFamily(
                name,
                documentation,
                labels=label_names
                )
        label_values = [label[1] for label in labels]
        self.metric_families[name].add_metric(label_values, value)

    def item_is_interesting(self, item):
        return self.interesting_items.match(item)

    def parse_line(self, line):
        labels = []
        stat_match = re.match(r"\W+(\w+): (\d+)", line)
        item, value = stat_match.group(1), stat_match.group(2)
        documentation = item
        queue_match = re.match(r"(tx|rx)_queue_(\d+)_(bytes|packets)", item)
        if queue_match:
            labels.append(('queue', queue_match.group(2)))
            item = "{}_queue_{}".format(
                queue_match.group(1),
                queue_match.group(3)
                )
            documentation = "{}_queue_N_{}".format(
                queue_match.group(1),
                queue_match.group(3)
                )
        name = "ethtool_" + item + "_total"
        return (name, documentation, labels, float(value))

    def find_physical_interfaces(self):
        # https://serverfault.com/a/833577/393474
        root = "/sys/class/net"
        for file in os.listdir(root):
            path = os.path.join(root, file)
            if os.path.islink(path) and "virtual" not in os.readlink(path):
                yield file


if __name__ == "__main__":
    try:
        REGISTRY.register(EthtoolCollector())
        httpd = http.server.HTTPServer(
            ("", 9417),
            MetricsHandler,
            )
        httpd.serve_forever()
    except KeyboardInterrupt:
        sys.exit()
