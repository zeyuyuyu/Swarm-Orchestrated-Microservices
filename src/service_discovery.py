import time
from dataclasses import dataclass
from typing import Dict, List, Optional
import logging

@dataclass
class ServiceHealth:
    is_healthy: bool
    last_check: float
    failure_count: int
    circuit_open: bool

class ServiceDiscovery:
    def __init__(self, health_check_interval: int = 30):
        self._services: Dict[str, Dict[str, str]] = {}
        self._health_status: Dict[str, ServiceHealth] = {}
        self._health_check_interval = health_check_interval
        self.logger = logging.getLogger(__name__)

    def register_service(self, service_id: str, host: str, port: int, metadata: dict = None) -> None:
        """Register a new service with the discovery system"""
        service_data = {
            'host': host,
            'port': str(port),
            'metadata': metadata or {}
        }
        self._services[service_id] = service_data
        self._health_status[service_id] = ServiceHealth(
            is_healthy=True,
            last_check=time.time(),
            failure_count=0,
            circuit_open=False
        )
        self.logger.info(f'Registered service {service_id} at {host}:{port}')

    def deregister_service(self, service_id: str) -> None:
        """Remove a service from the discovery system"""
        if service_id in self._services:
            del self._services[service_id]
            del self._health_status[service_id]
            self.logger.info(f'Deregistered service {service_id}')

    def get_service(self, service_id: str) -> Optional[Dict[str, str]]:
        """Get service details if healthy and circuit is closed"""
        if service_id not in self._services:
            return None
            
        health = self._health_status[service_id]
        if health.circuit_open:
            self.logger.warning(f'Circuit open for service {service_id}')
            return None
            
        if not health.is_healthy:
            self.logger.warning(f'Service {service_id} is unhealthy')
            return None
            
        return self._services[service_id]

    def update_health(self, service_id: str, is_healthy: bool) -> None:
        """Update service health status with circuit breaker logic"""
        if service_id not in self._health_status:
            return

        health = self._health_status[service_id]
        health.last_check = time.time()

        if not is_healthy:
            health.failure_count += 1
            if health.failure_count >= 3:  # Circuit breaker threshold
                health.circuit_open = True
                health.is_healthy = False
                self.logger.error(f'Circuit opened for service {service_id} after {health.failure_count} failures')
        else:
            health.failure_count = 0
            health.circuit_open = False
            health.is_healthy = True

    def get_healthy_services(self) -> List[str]:
        """Return list of healthy service IDs"""
        return [
            service_id for service_id, health in self._health_status.items()
            if health.is_healthy and not health.circuit_open
        ]

    def check_expired_services(self) -> None:
        """Mark services as unhealthy if health check interval has expired"""
        current_time = time.time()
        for service_id, health in self._health_status.items():
            if current_time - health.last_check > self._health_check_interval:
                health.is_healthy = False
                self.logger.warning(f'Service {service_id} marked unhealthy due to expired health check')
