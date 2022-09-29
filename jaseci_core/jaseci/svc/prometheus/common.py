################################################
#                   DEFAULTS                   #
################################################

PROMON_CONFIG = {"enabled": True, "quiet": False, "url": "http://localhost:9090"}


class Info:
    def __init__(self, app):
        self.app = app


class Cpu(Info):
    def utilization_core(self) -> dict:
        util = self.app.get_current_metric_value(
            'sum(irate(node_cpu_seconds_total{mode!="idle"}[10m])) by (node)'
        )
        res = {}
        for node in util:
            node_name = node["metric"]["node"]
            node_util = float(node["value"][1])
            res[node_name] = node_util
        return res

    def utilization_percentage(self) -> dict:
        util = self.app.get_current_metric_value(
            '(sum(irate(node_cpu_seconds_total{mode!="idle"}[10m])) by '
            '(node)) / (sum(irate(node_cpu_seconds_total{mode!=""}[10m])) by '
            "(node)) * 100"
        )
        res = {}
        for node in util:
            node_name = node["metric"]["node"]
            node_util = float(node["value"][1])
            res[node_name] = node_util
        return res

    def utilization_per_pod_cores(self) -> dict:
        util = self.app.get_current_metric_value(
            'sum(irate(container_cpu_usage_seconds_total{pod!=""}[10m])) by (pod)'
        )
        res = {}
        for pod in util:
            pod_name = pod["metric"]["pod"]
            value = float(pod["value"][1])
            res[pod_name] = float(value)
        return res


class Memory(Info):
    def total_bytes(self) -> dict:
        util = self.app.get_current_metric_value(
            "sum(node_memory_MemTotal_bytes) by (node)"
        )
        res = {}
        for node in util:
            node_name = node["metric"]["node"]
            node_util = float(node["value"][1])
            res[node_name] = node_util
        return res

    def utilization_bytes(self) -> dict:
        util = self.app.get_current_metric_value(
            "sum(node_memory_Active_bytes) by (node)"
        )
        res = {}
        for node in util:
            node_name = node["metric"]["node"]
            node_util = float(node["value"][1])
            res[node_name] = node_util
        return res

    def utilization_percentage(self) -> dict:
        util = self.app.get_current_metric_value(
            "sum(node_memory_Active_bytes / node_memory_MemTotal_bytes * 100 ) by "
            "(node)"
        )
        res = {}
        for node in util:
            node_name = node["metric"]["node"]
            node_util = float(node["value"][1])
            res[node_name] = node_util
        return res

    def utilization_per_pod_bytes(self) -> dict:
        util = self.app.get_current_metric_value(
            'sum(container_memory_working_set_bytes{pod!=""}) by (pod)'
        )
        res = {}
        for pod in util:
            pod_name = pod["metric"]["pod"]
            value = float(pod["value"][1])
            res[pod_name] = float(value)
        return res


class Network(Info):
    def receive_bytes(self) -> dict:
        util = self.app.get_current_metric_value(
            "sum (rate (node_network_receive_bytes_total{}[10m])) by (node)"
        )
        res = {}
        for node in util:
            node_name = node["metric"]["node"]
            node_util = float(node["value"][1])
            res[node_name] = node_util
        return res

    def receive_per_pod_bytes(self):
        util = self.app.get_current_metric_value(
            'sum (rate (container_network_receive_bytes_total{pod!=""}[10m])) by (pod)'
        )
        res = {}
        for pod in util:
            pod_name = pod["metric"]["pod"]
            value = pod["value"][1]
            res[pod_name] = float(value)
        return res

    def transmit_bytes(self) -> dict:
        util = self.app.get_current_metric_value(
            "sum (rate (node_network_transmit_bytes_total{}[10m])) by (node)"
        )
        res = {}
        for node in util:
            node_name = node["metric"]["node"]
            node_util = float(node["value"][1])
            res[node_name] = node_util
        return res

    def transmit_per_pod_bytes(self):
        util = self.app.get_current_metric_value(
            'sum (rate (container_network_transmit_bytes_total{pod!=""}[10m])) by (pod)'
        )
        res = {}
        for pod in util:
            pod_name = pod["metric"]["pod"]
            value = pod["value"][1]
            res[pod_name] = float(value)
        return res


class Disk(Info):
    def total_bytes(self) -> dict:
        util = self.app.get_current_metric_value(
            'sum(avg (node_filesystem_size_bytes{mountpoint!="/boot", '
            'fstype!="tmpfs"}) without (mountpoint)) by (node)'
        )
        res = {}
        for node in util:
            node_name = node["metric"]["node"]
            node_util = float(node["value"][1])
            res[node_name] = node_util
        return res

    def free_bytes(self) -> dict:
        util = self.app.get_current_metric_value(
            'sum(avg (node_filesystem_free_bytes{mountpoint!="/boot", '
            'fstype!="tmpfs"}) without (mountpoint)) by (node)'
        )
        res = {}
        for node in util:
            node_name = node["metric"]["node"]
            node_util = float(node["value"][1])
            res[node_name] = node_util
        return res
