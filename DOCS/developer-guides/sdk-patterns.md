# SDK Patterns and Best Practices

Production-ready patterns for building robust, scalable agents with the Sovereign SDK.

## Overview

This guide presents battle-tested patterns for:
- Error handling and resilience
- Performance optimization
- Security best practices
- Testing strategies
- Production deployment

## Core Patterns

### 1. The Resilient Agent Pattern

Build agents that gracefully handle failures and recover automatically.

```python
from sovereign_sdk import Agent, RetryPolicy, CircuitBreaker
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

class ResilientAgent(Agent):
    """Production-ready agent with comprehensive error handling"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(
            agent_id=config['agent_id'],
            name=config['name'],
            registry_url=config['registry_url']
        )
        
        # Configure retry policy
        self.retry_policy = RetryPolicy(
            max_attempts=3,
            backoff_factor=2.0,
            max_delay=30,
            retryable_exceptions=(ConnectionError, TimeoutError)
        )
        
        # Circuit breaker for external services
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=Exception
        )
        
        # Health check configuration
        self.health_check_interval = 30
        self.last_health_check = datetime.now()
        
        # Graceful shutdown
        self.shutdown_event = asyncio.Event()
        
    async def start(self):
        """Start agent with health monitoring"""
        try:
            # Register with retry
            await self.retry_policy.execute(self._register)
            
            # Start background tasks
            tasks = [
                asyncio.create_task(self._health_check_loop()),
                asyncio.create_task(self._process_requests()),
                asyncio.create_task(self._monitor_resources())
            ]
            
            # Wait for shutdown
            await self.shutdown_event.wait()
            
            # Graceful cleanup
            await self._cleanup(tasks)
            
        except Exception as e:
            logging.error(f"Agent startup failed: {e}")
            raise
    
    async def _register(self):
        """Register with retry logic"""
        try:
            await self.register()
            logging.info("Successfully registered with registry")
        except Exception as e:
            logging.warning(f"Registration attempt failed: {e}")
            raise
    
    async def _health_check_loop(self):
        """Periodic health checks"""
        while not self.shutdown_event.is_set():
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logging.error(f"Health check failed: {e}")
    
    async def _perform_health_check(self):
        """Comprehensive health check"""
        checks = {
            'registry_connection': await self._check_registry(),
            'resource_usage': self._check_resources(),
            'processing_queue': self._check_queue_health(),
            'last_successful_request': self._time_since_last_request()
        }
        
        self.last_health_check = datetime.now()
        
        if not all(checks.values()):
            await self._handle_unhealthy_state(checks)
    
    async def _process_requests(self):
        """Main request processing loop with error handling"""
        while not self.shutdown_event.is_set():
            try:
                request = await self.get_next_request()
                
                # Process with circuit breaker
                result = await self.circuit_breaker.call(
                    self._handle_request,
                    request
                )
                
                await self.send_response(request.id, result)
                
            except Exception as e:
                logging.error(f"Request processing failed: {e}")
                await self._handle_processing_error(e, request)
    
    async def _handle_request(self, request):
        """Process individual request with timeout"""
        timeout = request.get('timeout', 30)
        
        try:
            async with asyncio.timeout(timeout):
                return await self.process(request)
        except asyncio.TimeoutError:
            logging.warning(f"Request {request.id} timed out")
            raise
    
    async def shutdown(self):
        """Graceful shutdown"""
        logging.info("Initiating graceful shutdown...")
        self.shutdown_event.set()
        
        # Deregister from registry
        try:
            await self.deregister()
        except Exception as e:
            logging.error(f"Deregistration failed: {e}")
```

### 2. The Stateful Agent Pattern

Manage agent state reliably with persistence and recovery.

```python
import json
import aiofiles
from pathlib import Path
from typing import Any, Optional
import asyncio

class StatefulAgent(Agent):
    """Agent with persistent state management"""
    
    def __init__(self, state_dir: str = "./agent_state"):
        super().__init__()
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        
        # In-memory state with write-through cache
        self._state = {}
        self._state_lock = asyncio.Lock()
        self._dirty = False
        
        # Persistence configuration
        self.checkpoint_interval = 60  # seconds
        self.state_file = self.state_dir / f"{self.agent_id}_state.json"
        
    async def initialize(self):
        """Load persisted state on startup"""
        await self._load_state()
        
        # Start background persistence
        asyncio.create_task(self._persistence_loop())
    
    async def get_state(self, key: str, default: Any = None) -> Any:
        """Thread-safe state retrieval"""
        async with self._state_lock:
            return self._state.get(key, default)
    
    async def set_state(self, key: str, value: Any):
        """Thread-safe state update with persistence"""
        async with self._state_lock:
            self._state[key] = value
            self._dirty = True
    
    async def update_state(self, key: str, updater):
        """Atomic state update"""
        async with self._state_lock:
            current = self._state.get(key)
            new_value = updater(current)
            self._state[key] = new_value
            self._dirty = True
            return new_value
    
    async def _load_state(self):
        """Load state from disk"""
        if self.state_file.exists():
            try:
                async with aiofiles.open(self.state_file, 'r') as f:
                    content = await f.read()
                    self._state = json.loads(content)
                logging.info(f"Loaded state from {self.state_file}")
            except Exception as e:
                logging.error(f"Failed to load state: {e}")
                # Create backup
                backup_file = self.state_file.with_suffix('.backup')
                self.state_file.rename(backup_file)
    
    async def _save_state(self):
        """Persist state to disk"""
        if not self._dirty:
            return
            
        async with self._state_lock:
            try:
                # Write to temporary file first
                temp_file = self.state_file.with_suffix('.tmp')
                async with aiofiles.open(temp_file, 'w') as f:
                    await f.write(json.dumps(self._state, indent=2))
                
                # Atomic rename
                temp_file.replace(self.state_file)
                self._dirty = False
                
            except Exception as e:
                logging.error(f"Failed to save state: {e}")
    
    async def _persistence_loop(self):
        """Background state persistence"""
        while True:
            await asyncio.sleep(self.checkpoint_interval)
            await self._save_state()
```

### 3. The Multi-Service Agent Pattern

Build agents that provide multiple services efficiently.

```python
from typing import Dict, Callable, List
from dataclasses import dataclass
import inspect

@dataclass
class ServiceDefinition:
    name: str
    handler: Callable
    description: str
    input_schema: Dict
    output_schema: Dict
    requires_stake: bool = False
    min_stake: float = 0.0

class MultiServiceAgent(Agent):
    """Agent offering multiple services with routing"""
    
    def __init__(self):
        super().__init__()
        self.services: Dict[str, ServiceDefinition] = {}
        self._service_metrics = {}
        
    def register_service(
        self,
        name: str,
        handler: Callable,
        description: str,
        input_schema: Dict,
        output_schema: Dict,
        requires_stake: bool = False,
        min_stake: float = 0.0
    ):
        """Register a new service"""
        # Validate handler signature
        sig = inspect.signature(handler)
        if not inspect.iscoroutinefunction(handler):
            raise ValueError(f"Handler {name} must be async")
        
        service = ServiceDefinition(
            name=name,
            handler=handler,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema,
            requires_stake=requires_stake,
            min_stake=min_stake
        )
        
        self.services[name] = service
        self._service_metrics[name] = {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'total_time': 0
        }
        
        logging.info(f"Registered service: {name}")
    
    async def handle_request(self, request: Dict) -> Dict:
        """Route request to appropriate service"""
        service_name = request.get('service')
        
        if not service_name:
            return self._error_response("No service specified")
        
        if service_name not in self.services:
            return self._error_response(f"Unknown service: {service_name}")
        
        service = self.services[service_name]
        
        # Validate stake if required
        if service.requires_stake:
            stake = await self.get_client_stake(request['client_id'])
            if stake < service.min_stake:
                return self._error_response(
                    f"Insufficient stake. Required: {service.min_stake}, "
                    f"Current: {stake}"
                )
        
        # Validate input
        try:
            self._validate_schema(request.get('params', {}), 
                                service.input_schema)
        except ValueError as e:
            return self._error_response(f"Invalid input: {e}")
        
        # Execute service
        start_time = asyncio.get_event_loop().time()
        
        try:
            result = await service.handler(request['params'])
            
            # Validate output
            self._validate_schema(result, service.output_schema)
            
            # Update metrics
            elapsed = asyncio.get_event_loop().time() - start_time
            self._update_metrics(service_name, True, elapsed)
            
            return {
                'success': True,
                'service': service_name,
                'result': result,
                'execution_time': elapsed
            }
            
        except Exception as e:
            self._update_metrics(service_name, False, 0)
            logging.error(f"Service {service_name} failed: {e}")
            return self._error_response(str(e))
    
    def get_service_catalog(self) -> List[Dict]:
        """Return available services"""
        return [
            {
                'name': name,
                'description': service.description,
                'input_schema': service.input_schema,
                'output_schema': service.output_schema,
                'requires_stake': service.requires_stake,
                'min_stake': service.min_stake,
                'metrics': self._service_metrics[name]
            }
            for name, service in self.services.items()
        ]

# Example usage
agent = MultiServiceAgent()

# Register data processing service
agent.register_service(
    name="process_data",
    handler=async_data_processor,
    description="Process and analyze data sets",
    input_schema={
        "type": "object",
        "properties": {
            "data": {"type": "array"},
            "algorithm": {"type": "string"}
        },
        "required": ["data", "algorithm"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "result": {"type": "object"},
            "confidence": {"type": "number"}
        }
    },
    requires_stake=True,
    min_stake=100.0
)
```

### 4. The Event-Driven Agent Pattern

Build reactive agents that respond to events efficiently.

```python
from typing import Dict, List, Callable, Any
from collections import defaultdict
import asyncio

class EventDrivenAgent(Agent):
    """Agent with event-driven architecture"""
    
    def __init__(self):
        super().__init__()
        self._event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        
    def on(self, event_type: str, handler: Callable):
        """Register event handler"""
        if not asyncio.iscoroutinefunction(handler):
            raise ValueError("Handler must be async")
        
        self._event_handlers[event_type].append(handler)
        return self
    
    async def emit(self, event_type: str, data: Any = None):
        """Emit an event"""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.now(),
            'source': self.agent_id
        }
        
        await self._event_queue.put(event)
    
    async def start(self):
        """Start event processing"""
        self._running = True
        
        # Start event processor
        asyncio.create_task(self._process_events())
        
        # Register for external events
        await self._subscribe_to_external_events()
        
        await super().start()
    
    async def _process_events(self):
        """Process events from queue"""
        while self._running:
            try:
                # Get event with timeout to allow checking _running
                event = await asyncio.wait_for(
                    self._event_queue.get(), 
                    timeout=1.0
                )
                
                # Process event
                await self._handle_event(event)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logging.error(f"Event processing error: {e}")
    
    async def _handle_event(self, event: Dict):
        """Handle single event"""
        event_type = event['type']
        handlers = self._event_handlers.get(event_type, [])
        
        if not handlers:
            logging.debug(f"No handlers for event: {event_type}")
            return
        
        # Execute handlers concurrently
        tasks = [
            asyncio.create_task(handler(event))
            for handler in handlers
        ]
        
        # Wait for all handlers
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any handler errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logging.error(
                    f"Handler {handlers[i].__name__} failed: {result}"
                )
    
    async def _subscribe_to_external_events(self):
        """Subscribe to registry events"""
        # Subscribe to relevant events
        await self.registry.subscribe_events(
            agent_id=self.agent_id,
            events=['new_request', 'peer_joined', 'peer_left'],
            callback=self._external_event_callback
        )
    
    async def _external_event_callback(self, event: Dict):
        """Handle external events"""
        await self._event_queue.put(event)

# Example usage
agent = EventDrivenAgent()

# Register event handlers
@agent.on('request_received')
async def handle_request(event):
    request = event['data']
    # Process request
    result = await process_request(request)
    await agent.emit('request_completed', result)

@agent.on('peer_joined')
async def handle_peer_joined(event):
    peer_id = event['data']['peer_id']
    # Update peer list
    await agent.update_peer_list(peer_id)

@agent.on('error')
async def handle_error(event):
    error = event['data']
    # Log and potentially recover
    logging.error(f"Error event: {error}")
```

### 5. The Federated Agent Pattern

Build agents that work seamlessly across multiple registries.

```python
from typing import List, Dict, Optional
import asyncio

class FederatedAgent(Agent):
    """Agent capable of operating across federated registries"""
    
    def __init__(self, primary_registry: str, secondary_registries: List[str] = None):
        super().__init__(registry_url=primary_registry)
        
        self.primary_registry = primary_registry
        self.secondary_registries = secondary_registries or []
        self.registry_connections = {}
        self.federation_cache = {}
        
    async def initialize(self):
        """Initialize connections to all registries"""
        # Connect to primary
        await super().initialize()
        
        # Connect to secondary registries
        for registry_url in self.secondary_registries:
            try:
                connection = await self._connect_to_registry(registry_url)
                self.registry_connections[registry_url] = connection
                logging.info(f"Connected to registry: {registry_url}")
            except Exception as e:
                logging.error(f"Failed to connect to {registry_url}: {e}")
    
    async def find_service(self, service_type: str, 
                          requirements: Dict = None) -> Optional[Dict]:
        """Find service across all connected registries"""
        # Check cache first
        cache_key = f"{service_type}:{json.dumps(requirements or {})}"
        if cache_key in self.federation_cache:
            cached = self.federation_cache[cache_key]
            if cached['expires'] > datetime.now():
                return cached['service']
        
        # Search registries in parallel
        search_tasks = [
            self._search_registry(registry_url, service_type, requirements)
            for registry_url in [self.primary_registry] + self.secondary_registries
        ]
        
        results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Find best match
        best_service = self._select_best_service(results, requirements)
        
        # Cache result
        if best_service:
            self.federation_cache[cache_key] = {
                'service': best_service,
                'expires': datetime.now() + timedelta(minutes=5)
            }
        
        return best_service
    
    async def _search_registry(self, registry_url: str, 
                              service_type: str, 
                              requirements: Dict) -> List[Dict]:
        """Search single registry for services"""
        try:
            connection = self.registry_connections.get(
                registry_url, 
                self.registry
            )
            
            return await connection.search_agents(
                capabilities=[service_type],
                min_reputation=requirements.get('min_reputation', 0),
                max_price=requirements.get('max_price')
            )
        except Exception as e:
            logging.warning(f"Search failed on {registry_url}: {e}")
            return []
    
    def _select_best_service(self, results: List[List[Dict]], 
                           requirements: Dict) -> Optional[Dict]:
        """Select best service from search results"""
        all_services = []
        
        for result in results:
            if isinstance(result, list):
                all_services.extend(result)
        
        if not all_services:
            return None
        
        # Score services
        scored_services = []
        for service in all_services:
            score = self._calculate_service_score(service, requirements)
            scored_services.append((score, service))
        
        # Return highest scoring service
        scored_services.sort(reverse=True, key=lambda x: x[0])
        return scored_services[0][1]
    
    def _calculate_service_score(self, service: Dict, 
                                requirements: Dict) -> float:
        """Calculate service quality score"""
        score = 0.0
        
        # Reputation weight
        score += service.get('reputation', 0) * 0.4
        
        # Price weight (lower is better)
        max_price = requirements.get('max_price', 1000)
        price = service.get('price', max_price)
        score += (1 - price / max_price) * 0.3
        
        # Availability weight
        score += service.get('availability', 0) * 0.2
        
        # Registry preference (primary registry preferred)
        if service.get('registry_url') == self.primary_registry:
            score += 0.1
        
        return score

    async def execute_cross_registry_transaction(
        self, 
        target_agent: str,
        target_registry: str,
        operation: Dict
    ) -> Dict:
        """Execute transaction across registry boundaries"""
        # Get federation path
        path = await self._get_federation_path(target_registry)
        
        if not path:
            raise ValueError(f"No federation path to {target_registry}")
        
        # Build routed request
        request = {
            'type': 'federated_request',
            'source_registry': self.primary_registry,
            'target_registry': target_registry,
            'target_agent': target_agent,
            'federation_path': path,
            'operation': operation,
            'timestamp': datetime.now().isoformat()
        }
        
        # Sign request
        signature = await self.sign_message(json.dumps(request))
        request['signature'] = signature
        
        # Send through federation
        return await self._send_federated_request(request)
```

## Error Handling Patterns

### Comprehensive Error Strategy

```python
from enum import Enum
from typing import Optional, Union

class ErrorSeverity(Enum):
    LOW = "low"        # Log and continue
    MEDIUM = "medium"  # Retry with backoff
    HIGH = "high"      # Circuit break
    CRITICAL = "critical"  # Shutdown

class ErrorHandler:
    """Centralized error handling with recovery strategies"""
    
    def __init__(self):
        self.error_counts = defaultdict(int)
        self.error_handlers = {}
        self.recovery_strategies = {}
        
    def register_handler(
        self, 
        error_type: type, 
        handler: Callable,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ):
        """Register error-specific handler"""
        self.error_handlers[error_type] = {
            'handler': handler,
            'severity': severity
        }
    
    async def handle_error(
        self, 
        error: Exception, 
        context: Dict = None
    ) -> Optional[Any]:
        """Handle error with appropriate strategy"""
        error_type = type(error)
        self.error_counts[error_type.__name__] += 1
        
        # Get specific handler or default
        handler_info = self.error_handlers.get(
            error_type,
            {'handler': self._default_handler, 'severity': ErrorSeverity.MEDIUM}
        )
        
        handler = handler_info['handler']
        severity = handler_info['severity']
        
        # Log error
        logging.error(
            f"Error occurred: {error}",
            extra={
                'error_type': error_type.__name__,
                'severity': severity.value,
                'context': context,
                'count': self.error_counts[error_type.__name__]
            }
        )
        
        # Apply severity-based strategy
        if severity == ErrorSeverity.CRITICAL:
            await self._handle_critical_error(error, context)
        elif severity == ErrorSeverity.HIGH:
            await self._handle_high_severity_error(error, context)
        
        # Execute handler
        try:
            return await handler(error, context)
        except Exception as handler_error:
            logging.error(f"Error handler failed: {handler_error}")
            return None
    
    async def _handle_critical_error(self, error: Exception, context: Dict):
        """Handle critical errors"""
        # Alert operators
        await self._send_alert(
            level="critical",
            message=f"Critical error: {error}",
            context=context
        )
        
        # Initiate graceful shutdown
        asyncio.create_task(self._graceful_shutdown())
    
    async def _handle_high_severity_error(self, error: Exception, context: Dict):
        """Handle high severity errors"""
        error_type = type(error).__name__
        
        # Check if circuit should break
        if self.error_counts[error_type] > 10:
            await self._circuit_break(error_type)

# Integration with agent
class ErrorHandlingAgent(ResilientAgent):
    def __init__(self):
        super().__init__()
        self.error_handler = ErrorHandler()
        
        # Register handlers
        self.error_handler.register_handler(
            ConnectionError,
            self._handle_connection_error,
            ErrorSeverity.HIGH
        )
        
        self.error_handler.register_handler(
            ValueError,
            self._handle_validation_error,
            ErrorSeverity.LOW
        )
    
    async def _handle_connection_error(self, error: ConnectionError, context: Dict):
        """Handle connection errors with retry"""
        # Implement exponential backoff
        retry_count = context.get('retry_count', 0)
        delay = min(2 ** retry_count, 60)
        
        await asyncio.sleep(delay)
        
        # Retry operation
        return await self._retry_operation(context)
```

## Performance Optimization Patterns

### 1. Connection Pooling

```python
from asyncio import Queue
import aiohttp

class ConnectionPool:
    """Reusable connection pool for HTTP clients"""
    
    def __init__(self, size: int = 10):
        self.size = size
        self.pool: Queue = Queue(maxsize=size)
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self):
        """Initialize the connection pool"""
        self._session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                limit=self.size,
                ttl_dns_cache=300,
                keepalive_timeout=30
            )
        )
        
    async def acquire(self) -> aiohttp.ClientSession:
        """Acquire a connection from the pool"""
        return self._session
    
    async def close(self):
        """Close all connections"""
        if self._session:
            await self._session.close()

class PerformantAgent(Agent):
    def __init__(self):
        super().__init__()
        self.connection_pool = ConnectionPool(size=20)
        self._request_cache = TTLCache(maxsize=1000, ttl=300)
        
    async def initialize(self):
        await super().initialize()
        await self.connection_pool.initialize()
    
    @cached(cache='_request_cache')
    async def cached_request(self, url: str, params: Dict) -> Dict:
        """Cached HTTP request"""
        session = await self.connection_pool.acquire()
        
        async with session.get(url, params=params) as response:
            return await response.json()
```

### 2. Batch Processing

```python
class BatchProcessor:
    """Efficient batch processing for multiple operations"""
    
    def __init__(self, batch_size: int = 100, batch_timeout: float = 1.0):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self._pending_items = []
        self._batch_lock = asyncio.Lock()
        self._process_task = None
        
    async def add_item(self, item: Any) -> asyncio.Future:
        """Add item to batch"""
        future = asyncio.Future()
        
        async with self._batch_lock:
            self._pending_items.append((item, future))
            
            # Start processor if not running
            if not self._process_task:
                self._process_task = asyncio.create_task(
                    self._process_batches()
                )
            
            # Process immediately if batch is full
            if len(self._pending_items) >= self.batch_size:
                self._trigger_processing()
        
        return future
    
    async def _process_batches(self):
        """Process batches with timeout"""
        while True:
            await asyncio.sleep(self.batch_timeout)
            
            async with self._batch_lock:
                if not self._pending_items:
                    self._process_task = None
                    break
                
                # Process current batch
                batch = self._pending_items[:self.batch_size]
                self._pending_items = self._pending_items[self.batch_size:]
                
            await self._process_batch(batch)
    
    async def _process_batch(self, batch: List[Tuple[Any, asyncio.Future]]):
        """Process a single batch"""
        items = [item for item, _ in batch]
        futures = [future for _, future in batch]
        
        try:
            # Process all items together
            results = await self._batch_operation(items)
            
            # Set results
            for future, result in zip(futures, results):
                future.set_result(result)
                
        except Exception as e:
            # Set exception for all futures
            for future in futures:
                future.set_exception(e)
```

## Security Patterns

### Secure Communication

```python
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64

class SecureAgent(Agent):
    """Agent with end-to-end encryption"""
    
    def __init__(self):
        super().__init__()
        self._private_key = None
        self._public_key = None
        self._peer_keys = {}
        
    async def initialize_crypto(self):
        """Initialize cryptographic keys"""
        # Generate key pair
        self._private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self._public_key = self._private_key.public_key()
        
        # Register public key with registry
        public_key_pem = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        await self.registry.update_agent_metadata(
            agent_id=self.agent_id,
            metadata={'public_key': public_key_pem.decode()}
        )
    
    async def send_secure_message(self, recipient_id: str, message: Dict) -> Dict:
        """Send encrypted message to another agent"""
        # Get recipient's public key
        recipient_key = await self._get_peer_public_key(recipient_id)
        
        # Generate symmetric key for this message
        symmetric_key = os.urandom(32)
        
        # Encrypt message with symmetric key
        encrypted_message = self._encrypt_symmetric(
            json.dumps(message).encode(),
            symmetric_key
        )
        
        # Encrypt symmetric key with recipient's public key
        encrypted_key = recipient_key.encrypt(
            symmetric_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Sign the message
        signature = self._sign_message(encrypted_message)
        
        # Send encrypted package
        return await self.send_message(recipient_id, {
            'encrypted_message': base64.b64encode(encrypted_message).decode(),
            'encrypted_key': base64.b64encode(encrypted_key).decode(),
            'signature': base64.b64encode(signature).decode(),
            'sender_id': self.agent_id
        })
    
    async def receive_secure_message(self, encrypted_package: Dict) -> Dict:
        """Decrypt and verify received message"""
        # Decode components
        encrypted_message = base64.b64decode(
            encrypted_package['encrypted_message']
        )
        encrypted_key = base64.b64decode(
            encrypted_package['encrypted_key']
        )
        signature = base64.b64decode(
            encrypted_package['signature']
        )
        sender_id = encrypted_package['sender_id']
        
        # Get sender's public key
        sender_key = await self._get_peer_public_key(sender_id)
        
        # Verify signature
        try:
            sender_key.verify(
                signature,
                encrypted_message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        except Exception:
            raise ValueError("Invalid message signature")
        
        # Decrypt symmetric key
        symmetric_key = self._private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Decrypt message
        decrypted_message = self._decrypt_symmetric(
            encrypted_message,
            symmetric_key
        )
        
        return json.loads(decrypted_message.decode())
```

## Testing Patterns

### Comprehensive Test Suite

```python
import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

class TestableAgent(Agent):
    """Agent designed for testing"""
    
    def __init__(self, mock_registry=None):
        # Allow dependency injection for testing
        self._registry = mock_registry
        super().__init__()
        
    @property
    def registry(self):
        return self._registry or self._real_registry

# Test fixtures
@pytest.fixture
async def mock_registry():
    """Mock registry for testing"""
    registry = AsyncMock()
    registry.register_agent.return_value = {'agent_id': 'test-agent-123'}
    registry.search_agents.return_value = [
        {'agent_id': 'peer-1', 'capabilities': ['compute']},
        {'agent_id': 'peer-2', 'capabilities': ['storage']}
    ]
    return registry

@pytest.fixture
async def test_agent(mock_registry):
    """Test agent instance"""
    agent = TestableAgent(mock_registry=mock_registry)
    await agent.initialize()
    return agent

# Test cases
class TestAgentBehavior:
    """Comprehensive agent tests"""
    
    @pytest.mark.asyncio
    async def test_agent_registration(self, test_agent, mock_registry):
        """Test agent registers correctly"""
        await test_agent.register()
        
        mock_registry.register_agent.assert_called_once()
        assert test_agent.agent_id == 'test-agent-123'
    
    @pytest.mark.asyncio
    async def test_error_handling(self, test_agent):
        """Test agent handles errors gracefully"""
        # Simulate error
        test_agent.process = AsyncMock(
            side_effect=ConnectionError("Network error")
        )
        
        # Should not crash
        result = await test_agent.handle_request({'data': 'test'})
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, test_agent):
        """Test agent handles concurrent requests"""
        # Create multiple concurrent requests
        requests = [
            test_agent.handle_request({'id': i, 'data': f'test-{i}'})
            for i in range(10)
        ]
        
        # All should complete
        results = await asyncio.gather(*requests)
        
        assert len(results) == 10
        assert all(r['success'] for r in results)
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self, test_agent, mock_registry):
        """Test agent shuts down gracefully"""
        # Start agent
        task = asyncio.create_task(test_agent.start())
        
        # Give it time to start
        await asyncio.sleep(0.1)
        
        # Trigger shutdown
        await test_agent.shutdown()
        
        # Should deregister
        mock_registry.deregister_agent.assert_called_once()
        
        # Task should complete
        await task

# Integration tests
class TestAgentIntegration:
    """Integration tests with real components"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_registry_integration(self):
        """Test real registry integration"""
        async with TestRegistry() as registry:
            agent = Agent(registry_url=registry.url)
            
            await agent.register()
            
            # Verify in registry
            agents = await registry.list_agents()
            assert any(a['id'] == agent.agent_id for a in agents)
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_p2p_communication(self):
        """Test peer-to-peer communication"""
        async with TestRegistry() as registry:
            # Create two agents
            agent1 = Agent(registry_url=registry.url)
            agent2 = Agent(registry_url=registry.url)
            
            await agent1.register()
            await agent2.register()
            
            # Agent 1 sends message to Agent 2
            message = {'type': 'test', 'data': 'hello'}
            response = await agent1.send_message(agent2.agent_id, message)
            
            assert response['success'] is True
```

## Production Deployment Patterns

### Container-Ready Agent

```python
# Dockerfile
"""
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY poetry.lock pyproject.toml ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Copy agent code
COPY src/ ./src/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health').raise_for_status()"

# Run agent
CMD ["python", "-m", "src.agent"]
"""

# docker-compose.yml
"""
version: '3.8'

services:
  agent:
    build: .
    environment:
      - AGENT_ID=${AGENT_ID}
      - REGISTRY_URL=${REGISTRY_URL}
      - LOG_LEVEL=INFO
    volumes:
      - agent_state:/app/state
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

volumes:
  agent_state:
"""

# Kubernetes deployment
"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sovereign-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sovereign-agent
  template:
    metadata:
      labels:
        app: sovereign-agent
    spec:
      containers:
      - name: agent
        image: myregistry/sovereign-agent:latest
        resources:
          requests:
            memory: "1Gi"
            cpu: "1"
          limits:
            memory: "2Gi"
            cpu: "2"
        env:
        - name: AGENT_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: REGISTRY_URL
          value: "http://registry-service:8000"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
"""
```

## Best Practices Summary

### 1. Design Principles
- **Single Responsibility**: Each agent should do one thing well
- **Fail Fast**: Detect and handle errors early
- **Graceful Degradation**: Maintain partial functionality during failures
- **Observability**: Comprehensive logging and metrics

### 2. Code Organization
```
my_agent/
├── src/
│   ├── __init__.py
│   ├── agent.py          # Main agent class
│   ├── handlers/         # Request handlers
│   ├── services/         # Business logic
│   ├── utils/           # Utilities
│   └── config.py        # Configuration
├── tests/
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── fixtures/       # Test fixtures
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs/
│   └── api.md         # API documentation
├── pyproject.toml
└── README.md
```

### 3. Performance Guidelines
- Use connection pooling for external services
- Implement caching for expensive operations
- Batch operations when possible
- Profile and optimize hot paths
- Set appropriate timeouts

### 4. Security Checklist
- [ ] Validate all inputs
- [ ] Use encryption for sensitive data
- [ ] Implement rate limiting
- [ ] Regular security audits
- [ ] Least privilege principle
- [ ] Secure key management

### 5. Operational Excellence
- Comprehensive health checks
- Structured logging
- Metrics and monitoring
- Graceful shutdown
- Configuration management
- Automated deployment

## Conclusion

These patterns provide a foundation for building production-ready agents. Remember:
- Start simple and iterate
- Test thoroughly at all levels
- Monitor everything
- Document your patterns
- Share knowledge with the community

---

*"Patterns are the language of experience. Master them to speak fluently."*
- The Warrior Owl Doctrine