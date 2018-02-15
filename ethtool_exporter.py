#!/usr/bin/python3

import time
import http.server
import re

from prometheus_client import start_http_server, Summary
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY
from prometheus_client.exposition import MetricsHandler


#class EthtoolCollector(object):
#
#    def collect(self):
#        yield GaugeMetricFamily('my_gauge', 'Help text', value=7)
#        c = CounterMetricFamily('my_counter_total', 'Help text', labels=['foo'])
#        c.add_metric(['bar'], 1.7)
#        c.add_metric(['baz'], 3.8)
#        yield c
#
#
#REGISTRY.register(CustomCollector())

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

    def __init__(self):
        self.fake_data = None

    def read_ethtool_statistics(self):
        if self.fake_data is not None:
            return self.fake_data
        else:
            return "   rx_no_dma_resources: 590843871\n"

    def collect(self):
        self.metric_families = {}
        for line in self.read_ethtool_statistics().splitlines():
            if self.item_is_interesting(line):
                metric, family, value, labels = self.parse_line(line)
                if metric not in self.metric_families:
                    self.metric_families[metric] = family(metric, "help text", labels=labels.keys())
                self.metric_families[metric].add_metric(labels.values(), value)
        for metric in self.metric_families:
            yield self.metric_families[metric]

    def item_is_interesting(self, item):
        return self.interesting_items.match(item)

    def parse_line(self, line):
        labels = {}
        stat_match = re.match(r"\W+(\w+): (\d+)", line)
        item, value = stat_match.group(1), stat_match.group(2)
        queue_match = re.match(r"(tx|rx)_queue_(\d+)_(bytes|packets)", item)
        if queue_match:
            labels = {
                'queue': queue_match.group(2),
                }
            item = "{}_queue_{}".format(queue_match.group(1), queue_match.group(3))
        metric_name = "ethtool_" + item
        metric_type = CounterMetricFamily  # They're all counters.
        return (metric_name, metric_type, float(value), labels)


def find_physical_interfaces():
    # https://serverfault.com/a/833577/393474
    root = "/sys/class/net"
    for file in os.listdir(root):
        path = os.path.join(root, file)
        if os.path.islink(path) and "virtual" not in os.readlink(path):
            yield file


if __name__ == "__main__":
    REGISTRY.register(EthtoolCollector())

    httpd = http.server.HTTPServer(
        ("", 8000),
        MetricsHandler
    )
    httpd.serve_forever()
