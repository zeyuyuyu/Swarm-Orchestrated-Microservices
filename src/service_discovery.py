import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import threading

@dataclass
class ServiceNode:
    name: str
    host: str
    port: int
    last_heartbeat: datetime
    status: str = 'healthy'
    metadata: Dict = None

class ServiceDiscovery:
    def __init__(self, heartbeat_interval: int = 30):
        self._services: Dict[str, List[ServiceNode]] = {}
        self._lock = threading.Lock()
        self._heartbeat_interval = heartbeat_interval
        self.logger = logging.getLogger(__name__)
        
        # Start health monitoring thread
        self._monitor_thread = threading.Thread(
            target=self._health_monitor,
            daemon=True
        )
        self._monitor_thread.start()

    def register_service(self, name: str, host: str, port: int, metadata: Dict = None) -> None:
        """Register a new service instance"""
        with self._lock:
            if name not in self._services:
                self._services[name] = []
            
            node = ServiceNode(
                name=name,
                host=host,
                port=port,
                last_heartbeat=datetime.now(),
                metadata=metadata or {}
            )
            self._services[name].append(node)
            self.logger.info(f'Registered service {name} at {host}:{port}')

    def deregister_service(self, name: str, host: str, port: int) -> None:
        """Remove a service instance from registry"""
        with self._lock:
            if name in self._services:
                self._services[name] = [
                    s for s in self._services[name]
                    if not (s.host == host and s.port == port)
                ]
                self.logger.info(f'Deregistered service {name} at {host}:{port}')

    def get_service(self, name: str) -> Optional[ServiceNode]:
        """Get a healthy instance of the requested service"""
        with self._lock:
            if name in self._services:
                healthy_nodes = [
                    node for node in self._services[name]
                    if node.status == 'healthy'
                ]
                if healthy_nodes:
                    # Simple round-robin selection
                    return healthy_nodes[0]
        return None

    def heartbeat(self, name: str, host: str, port: int) -> None:
        """Update service heartbeat timestamp"""
        with self._lock:
            if name in self._services:
                for service in self._services[name]:
                    if service.host == host and service.port == port:
                        service.last_heartbeat = datetime.now()
                        service.status = 'healthy'
                        break

    def _health_monitor(self) -> None:
        """Monitor service health based on heartbeats"""
        while True:
            with self._lock:
                current_time = datetime.now()
                for service_name, nodes in self._services.items():
                    for node in nodes:
                        time_since_heartbeat = (current_time - node.last_heartbeat).seconds
                        
                        if time_since_heartbeat > self._heartbeat_interval * 2:
                            if node.status != 'dead':
                                node.status = 'dead'
                                self.logger.warning(
                                    f'Service {service_name} at {node.host}:{node.port} '
                                    f'marked as dead. No heartbeat for {time_since_heartbeat}s'
                                )
                        elif time_since_heartbeat > self._heartbeat_interval:
                            if node.status == 'healthy':
                                node.status = 'unhealthy'
                                self.logger.warning(
                                    f'Service {service_name} at {node.host}:{node.port} '
                                    f'marked as unhealthy. Last heartbeat {time_since_heartbeat}s ago'
                                )
            
            time.sleep(5)  # Check health every 5 seconds

    def get_all_services(self) -> Dict[str, List[ServiceNode]]:
        """Get all registered services and their status"""
        with self._lock:
            return self._services.copy()
