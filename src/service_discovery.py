import random
import time

class ServiceDiscovery:
    def __init__(self, services):
        self.services = services
        self.service_instances = {}
        self.load_balancer = {}

    def register_service(self, service_name, instance):
        if service_name not in self.service_instances:
            self.service_instances[service_name] = []
        self.service_instances[service_name].append(instance)
        self.load_balancer[instance] = 0

    def discover_service(self, service_name):
        if service_name not in self.service_instances or not self.service_instances[service_name]:
            return None

        # Load balancing
        least_loaded = min(self.service_instances[service_name], key=lambda x: self.load_balancer[x])
        self.load_balancer[least_loaded] += 1
        return least_loaded

    def heartbeat(self):
        for service_name, instances in self.service_instances.items():
            for instance in instances:
                if random.random() < 0.01:  # 1% chance of instance failure
                    self.service_instances[service_name].remove(instance)
                    del self.load_balancer[instance]
                    print(f'Instance {instance} of service {service_name} has failed.')

        time.sleep(10)  # Check for instance failures every 10 seconds
