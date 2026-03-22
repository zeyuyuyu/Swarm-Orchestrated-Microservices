import docker
import time
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ServiceHealth:
    status: str
    last_check: datetime
    container_id: str
    restarts: int

class ServiceDiscovery:
    def __init__(self):
        self.client = docker.from_env()
        self.services: Dict[str, ServiceHealth] = {}
        self.health_check_interval = 30  # seconds

    def discover_services(self) -> List[str]:
        """Discover all running services in the swarm"""
        services = []
        try:
            for container in self.client.containers.list():
                if 'com.docker.swarm.service.name' in container.labels:
                    service_name = container.labels['com.docker.swarm.service.name']
                    services.append(service_name)
                    
                    # Update health status
                    self.services[service_name] = ServiceHealth(
                        status='healthy' if container.status == 'running' else 'unhealthy',
                        last_check=datetime.now(),
                        container_id=container.id,
                        restarts=container.attrs['RestartCount']
                    )
        except Exception as e:
            print(f'Error discovering services: {str(e)}')
        return services

    def get_service_health(self, service_name: str) -> ServiceHealth:
        """Get health status for a specific service"""
        return self.services.get(service_name)

    def monitor_services(self):
        """Continuous monitoring of services"""
        while True:
            self.discover_services()
            
            # Log health status
            for service, health in self.services.items():
                print(f'Service {service}: {health.status} '
                      f'(Restarts: {health.restarts})')
            
            time.sleep(self.health_check_interval)

    def get_unhealthy_services(self) -> List[str]:
        """Return list of services currently marked as unhealthy"""
        return [name for name, health in self.services.items() 
                if health.status == 'unhealthy']

if __name__ == '__main__':
    discovery = ServiceDiscovery()
    discovery.monitor_services()