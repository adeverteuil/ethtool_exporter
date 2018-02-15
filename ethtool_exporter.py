#!/usr/bin/python

from __future__ import absolute_import, division, print_function, unicode_literals

import re

from prometheus_client import start_http_server, Summary
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY


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

class StatsParser(object):

    interesting_items = re.compile(
        r"""\W*(
            rx_no_dma_resources|
            (tx|rx)_queue_(\d+)_(bytes|packets)|
            (rx|tx)_(packets|bytes|broadcast|multicast|errors)
            )
        """,
        re.VERBOSE
        )

    def collect(self, data):
        for line in data.splitlines():
            if self.item_is_interesting(line):
                yield self.parse_line(line)

    def item_is_interesting(self, item):
        return self.interesting_items.match(item)

    def parse_line(self, line):
        tags = []
        stat_match = re.match(r"\W+(\w+): (\d+)", line)
        item, value = stat_match.group(1), stat_match.group(2)
        queue_match = re.match(r"(tx|rx)_queue_(\d+)_(bytes|packets)", item)
        if queue_match:
            tags = [
                ('direction', queue_match.group(1)),
                ('queue', queue_match.group(2)),
                ]
            item = "queue_{}".format(queue_match.group(3))
        item = "ethtool_" + item
        return (item, int(value), tags)


def find_physical_interfaces():
    # https://serverfault.com/a/833577/393474
    root = "/sys/class/net"
    for file in os.listdir(root):
        path = os.path.join(root, file)
        if os.path.islink(path) and "virtual" not in os.readlink(path):
            yield file
