# Monitoring Setup Guide

Setting up comprehensive monitoring for your Protocol registry and agents to ensure optimal performance, security, and reliability.

## Overview

A well-monitored Protocol deployment tracks:
- Service health and availability
- Performance metrics and resource usage
- Economic activity and token flows
- Security events and anomalies
- Federation connectivity

## Monitoring Stack Components

### Recommended Stack

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   Prometheus    │────▶│   Grafana    │────▶│   Alerts    │
│ (Metrics Store) │     │ (Dashboards) │     │ (PagerDuty) │
└────────┬────────┘     └──────────────┘     └─────────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    │         │          │          │
┌───▼───┐ ┌──▼───┐ ┌────▼────┐ ┌───▼────┐
│Registry│ │ TEG  │ │ Agents  │ │ SPIRE  │
└────────┘ └──────┘ └─────────┘ └────────┘
```

### Components

1. **Prometheus**: Time-series database for metrics
2. **Grafana**: Visualization and dashboards
3. **Node Exporter**: System metrics collection
4. **Custom Exporters**: Protocol-specific metrics
5. **AlertManager**: Alert routing and management

## Quick Start with Docker Compose

### 1. Monitoring Stack Configuration

Create `monitoring/docker-compose.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: protocol_prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: protocol_grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=SovereignMonitor!2025
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - prometheus
    restart: unless-stopped

  node_exporter:
    image: prom/node-exporter:latest
    container_name: protocol_node_exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:latest
    container_name: protocol_alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager_data:/alertmanager
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
  alertmanager_data:
```

### 2. Prometheus Configuration

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

rule_files:
  - "alert_rules.yml"

scrape_configs:
  # System metrics
  - job_name: 'node'
    static_configs:
      - targets: ['node_exporter:9100']

  # Registry metrics
  - job_name: 'registry_a'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/metrics'

  - job_name: 'registry_b'
    static_configs:
      - targets: ['host.docker.internal:8001']
    metrics_path: '/metrics'

  # TEG Layer metrics
  - job_name: 'teg_layer'
    static_configs:
      - targets: ['host.docker.internal:8080']
    metrics_path: '/api/metrics'

  # SPIRE metrics
  - job_name: 'spire_server'
    static_configs:
      - targets: ['host.docker.internal:8081']
    metrics_path: '/metrics'

  # Agent metrics (dynamic discovery)
  - job_name: 'agents'
    consul_sd_configs:
      - server: 'consul:8500'
        services: ['agent-service']
    relabel_configs:
      - source_labels: [__meta_consul_service]
        target_label: job
```

### 3. Alert Rules

Create `monitoring/alert_rules.yml`:

```yaml
groups:
  - name: protocol_alerts
    interval: 30s
    rules:
      # Service availability
      - alert: RegistryDown
        expr: up{job=~"registry_.*"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Registry {{ $labels.instance }} is down"
          description: "Registry has been down for more than 5 minutes"

      - alert: TEGLayerDown
        expr: up{job="teg_layer"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "TEG Layer is down"
          description: "TEG Layer service has been down for more than 5 minutes"

      # Performance alerts
      - alert: HighResponseTime
        expr: http_request_duration_seconds{quantile="0.99"} > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High response time on {{ $labels.instance }}"
          description: "99th percentile response time is above 2 seconds"

      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is above 90%"

      # Economic alerts
      - alert: LowTreasuryBalance
        expr: teg_treasury_balance < 1000
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "TEG Treasury balance is low"
          description: "Treasury balance is below 1000 tokens"

      - alert: UnusualTransactionVolume
        expr: rate(teg_transactions_total[5m]) > 100
        for: 10m
        labels:
          severity: info
        annotations:
          summary: "Unusual transaction volume detected"
          description: "Transaction rate exceeds 100/minute"

      # Security alerts
      - alert: FailedAuthAttempts
        expr: rate(auth_failures_total[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High number of failed auth attempts"
          description: "More than 10 failed auth attempts per minute"

      - alert: CertificateExpiringSoon
        expr: x509_cert_expiry - time() < 7 * 24 * 3600
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Certificate expiring soon"
          description: "Certificate will expire in less than 7 days"
```

### 4. Grafana Dashboard

Create `monitoring/grafana/provisioning/dashboards/protocol-overview.json`:

```json
{
  "dashboard": {
    "title": "Protocol Overview",
    "panels": [
      {
        "title": "Service Status",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "targets": [{
          "expr": "up",
          "legendFormat": "{{ job }}"
        }],
        "type": "stat"
      },
      {
        "title": "Request Rate",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
        "targets": [{
          "expr": "rate(http_requests_total[5m])",
          "legendFormat": "{{ job }} - {{ method }}"
        }],
        "type": "graph"
      },
      {
        "title": "Token Transactions",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
        "targets": [{
          "expr": "rate(teg_transactions_total[5m])",
          "legendFormat": "{{ type }}"
        }],
        "type": "graph"
      },
      {
        "title": "Active Agents",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
        "targets": [{
          "expr": "registry_active_agents",
          "legendFormat": "{{ registry }}"
        }],
        "type": "stat"
      }
    ]
  }
}
```

## Application Metrics

### Registry Metrics

Add to your Registry service:

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response

# Metrics
agent_registrations = Counter('registry_agent_registrations_total', 
                            'Total agent registrations')
active_agents = Gauge('registry_active_agents', 
                     'Number of active agents')
request_duration = Histogram('http_request_duration_seconds',
                           'HTTP request duration')
federation_peers = Gauge('registry_federation_peers',
                       'Number of federation peers')

# Endpoint
@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), 
                   media_type="text/plain")

# Use in your code
@app.post("/api/agents/register")
async def register_agent(...):
    agent_registrations.inc()
    active_agents.inc()
    # ... rest of your logic
```

### TEG Layer Metrics

```python
# Economic metrics
token_transfers = Counter('teg_transfers_total', 
                         'Total token transfers',
                         ['type'])
treasury_balance = Gauge('teg_treasury_balance',
                        'Current treasury balance')
staking_total = Gauge('teg_staking_total',
                     'Total staked tokens')
transaction_fees = Counter('teg_fees_collected_total',
                          'Total fees collected')

# Track in your code
async def transfer_tokens(from_did, to_did, amount):
    token_transfers.labels(type='transfer').inc()
    transaction_fees.inc(amount * 0.01)  # 1% fee
    # ... transfer logic
```

### Agent Metrics

For agents, use the SDK's built-in metrics:

```python
from sovereign_sdk import Agent, Metrics

class MonitoredAgent(Agent):
    def __init__(self):
        super().__init__()
        self.metrics = Metrics(port=9200)
        
    async def handle_request(self, request):
        with self.metrics.timer('request_duration'):
            result = await self.process(request)
        
        self.metrics.counter('requests_total').inc()
        return result
```

## Health Check Scripts

### Registry Health Check

Create `scripts/check_registry_health.sh`:

```bash
#!/bin/bash

REGISTRY_A="http://localhost:8000"
REGISTRY_B="http://localhost:8001"

check_health() {
    local url=$1
    local name=$2
    
    response=$(curl -s -o /dev/null -w "%{http_code}" $url/health)
    
    if [ $response -eq 200 ]; then
        echo "✓ $name is healthy"
        return 0
    else
        echo "✗ $name is unhealthy (HTTP $response)"
        return 1
    fi
}

echo "=== Registry Health Check ==="
check_health $REGISTRY_A "Registry A"
check_health $REGISTRY_B "Registry B"

# Check federation
federation_status=$(curl -s $REGISTRY_A/api/federation/status | jq -r '.status')
echo "Federation Status: $federation_status"
```

### Comprehensive System Check

Create `scripts/system_health_check.py`:

```python
#!/usr/bin/env python3
import asyncio
import aiohttp
import psutil
import json
from datetime import datetime

class SystemHealthChecker:
    def __init__(self):
        self.checks = []
        
    async def check_service(self, name, url):
        """Check if a service is responding"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/health", timeout=5) as response:
                    is_healthy = response.status == 200
                    self.checks.append({
                        'service': name,
                        'url': url,
                        'status': 'healthy' if is_healthy else 'unhealthy',
                        'response_time': response.headers.get('X-Response-Time', 'N/A')
                    })
        except Exception as e:
            self.checks.append({
                'service': name,
                'url': url,
                'status': 'error',
                'error': str(e)
            })
    
    def check_system_resources(self):
        """Check system resource usage"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'network_connections': len(psutil.net_connections())
        }
    
    async def check_database(self):
        """Check database connectivity"""
        # Implementation depends on your database setup
        pass
    
    async def run_health_check(self):
        """Run all health checks"""
        # Check services
        services = [
            ('Registry A', 'http://localhost:8000'),
            ('Registry B', 'http://localhost:8001'),
            ('TEG Layer', 'http://localhost:8080'),
            ('SPIRE Server', 'http://localhost:8081')
        ]
        
        tasks = [self.check_service(name, url) for name, url in services]
        await asyncio.gather(*tasks)
        
        # Check system resources
        resources = self.check_system_resources()
        
        # Generate report
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'services': self.checks,
            'system': resources,
            'overall_status': 'healthy' if all(
                c['status'] == 'healthy' for c in self.checks
            ) else 'degraded'
        }
        
        return report

async def main():
    checker = SystemHealthChecker()
    report = await checker.run_health_check()
    
    print(json.dumps(report, indent=2))
    
    # Exit with appropriate code
    exit(0 if report['overall_status'] == 'healthy' else 1)

if __name__ == '__main__':
    asyncio.run(main())
```

## Log Aggregation

### Centralized Logging with ELK Stack

Add to your `docker-compose.yml`:

```yaml
elasticsearch:
  image: elasticsearch:8.11.0
  environment:
    - discovery.type=single-node
    - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
  ports:
    - "9200:9200"
  volumes:
    - es_data:/usr/share/elasticsearch/data

logstash:
  image: logstash:8.11.0
  volumes:
    - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
  depends_on:
    - elasticsearch

kibana:
  image: kibana:8.11.0
  ports:
    - "5601:5601"
  environment:
    - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
  depends_on:
    - elasticsearch
```

### Application Logging

Configure structured logging in your services:

```python
import structlog
from pythonjsonlogger import jsonlogger

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Use in your code
logger.info("agent_registered", 
           agent_id=agent.id,
           capabilities=agent.capabilities,
           registry="registry_a")
```

## Monitoring Best Practices

### 1. Key Metrics to Track

**Service Level**
- Request rate and latency (p50, p95, p99)
- Error rate and types
- Service availability (uptime)
- Resource usage (CPU, memory, disk)

**Business Level**
- Active agents count
- Transaction volume and value
- Token circulation metrics
- Federation link health

**Security Level**
- Authentication failures
- Unusual activity patterns
- Certificate expiration
- Policy violations

### 2. Alert Configuration

**Critical Alerts** (Immediate action required)
- Service down > 5 minutes
- Database unreachable
- Security breach detected
- Treasury depleted

**Warning Alerts** (Investigate soon)
- High response times
- Resource usage > 80%
- Certificate expiring < 7 days
- Unusual transaction patterns

**Info Alerts** (Awareness only)
- New agent registrations
- Scheduled maintenance reminders
- Performance degradation trends

### 3. Dashboard Organization

Create role-specific dashboards:

**Operations Dashboard**
- Service health overview
- Resource utilization
- Error rates and logs
- Active incidents

**Business Dashboard**
- Agent growth metrics
- Transaction volumes
- Token economics
- Federation statistics

**Security Dashboard**
- Authentication metrics
- Policy violations
- Certificate status
- Threat indicators

## Monitoring Checklist

- [ ] Prometheus and Grafana deployed
- [ ] Service metrics exposed
- [ ] Alert rules configured
- [ ] Dashboards created
- [ ] Log aggregation setup
- [ ] Health check scripts deployed
- [ ] Alert routing configured
- [ ] Documentation updated
- [ ] Team trained on dashboards
- [ ] Runbooks created for alerts

## Next Steps

1. **Customize Alerts**: Adjust thresholds based on your SLAs
2. **Add Custom Metrics**: Track business-specific KPIs
3. **Integrate with Ops Tools**: Connect to PagerDuty, Slack, etc.
4. **Regular Reviews**: Monthly monitoring retrospectives
5. **Capacity Planning**: Use metrics for scaling decisions

---

*"What cannot be measured cannot be improved. Monitor wisely."*
- The Warrior Owl Doctrine