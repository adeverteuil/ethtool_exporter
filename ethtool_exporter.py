#!/usr/bin/env python3

import http.server
import math
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
            rx_no_dma_resources|Speed|Duplex|
            (tx|rx)_queue_(\d+)_(bytes|packets)|
            (rx|tx)_(packets|bytes|broadcast|multicast|errors)
            )
        """,
        re.VERBOSE
        )

    def collect(self, test_data=None, test_info=None):
        self.metric_families = {}

        #interface info
        if test_info is not None:
            self.get_ethtool_info("eth0", test_info)
        else:
            for interface in self.find_physical_interfaces():
                self.get_ethtool_info(interface)

        #statistics
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
                data = subprocess.check_output(
                    ["ethtool", "-S", interface],
                    ).decode()
            except subprocess.CalledProcessError as err:
                logging.error(
                    "ethtool returned {} for interface {}".format(
                        err.returncode,
                        interface
                        )
                    )
                sys.exit()
        for line in data.splitlines():
            if self.item_is_interesting(line):
                name, documentation, labels, value  = self.parse_line(line)
                labels.insert(0, ("interface", interface))
                self.add_counter_metric(name, documentation, labels, value)
    def get_ethtool_info(self, interface, test_info=None):
        if test_info is not None:
            data = test_info
        else:
            try:
                data = subprocess.check_output(["ethtool", interface]).decode()
            except subprocess.CalledProcessError as err:
                pass
        speed = 0
        duplex = "n/a"
        for line in data.splitlines():
            if self.item_is_interesting(line):
                name, documentation, labels, value  = self.parse_line(line)
                if documentation == "Speed":
                    speed = value
                elif documentation == "Duplex":
                    duplex = value

        labels = []
        labels.append(("interface", interface))
        labels.append(("duplex", duplex))

        self.add_gauge_metric("ethtool_interface_speed", "", labels, speed)

    def add_counter_metric(self, name, documentation, labels, value):
        if name not in self.metric_families:
            label_names = [label[0] for label in labels]
            self.metric_families[name] = CounterMetricFamily(
                name,
                documentation,
                labels=label_names
                )
        label_values = [label[1] for label in labels]
        self.metric_families[name].add_metric(label_values, value)
    def add_gauge_metric(self, name, documentation, labels, value):
        if name not in self.metric_families:
            label_names = [label[0] for label in labels]
            self.metric_families[name] = GaugeMetricFamily(
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
        if not stat_match:
            duplex_match = re.match(r"\W+Duplex: (\w+)", line)
            if duplex_match:
                return ("Duplex", "Duplex", labels, duplex_match.group(1))
            return (None, None, None, None)
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
        speed_match = re.match(r"\W+Speed:\W+\d+((K|M|G|T|P|E|Z|Y)b)\/s", line)
        if speed_match:
            value = self.convert_size(int(value), speed_match.group(1))
        return (name, documentation, labels, float(value))

    def find_physical_interfaces(self):
        # https://serverfault.com/a/833577/393474
        root = "/sys/class/net"
        for file in os.listdir(root):
            path = os.path.join(root, file)
            if os.path.islink(path) and "virtual" not in os.readlink(path):
                yield file

    def convert_size(self, size_bytes, unit):
        if size_bytes == 0:
            return 0
        size_name = ["b", "Kb", "Mb", "Gb", "Tb", "Pb", "Eb", "Zb", "Yb"]

        power = 0
        i = 0
        for dictunit in size_name:
            if dictunit == unit:
                power = i
                break
            i=i+1

        p = math.pow(1024, power)
        return size_bytes * p

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
