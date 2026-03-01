# TDD: Proxy Support Implementation

> **Version:** 1.0  
> **Date:** 2026-03-01  
> **Task:** 2.4 - Proxy Support  
> **Files:** `crawler/scraper/proxy.py`, `crawler/scraper/proxy_pool.py`

---

## VDD: Value-Driven Design

### Business Value

| Value | Description | Metric |
|-------|-------------|--------|
| **Anti-blocking** | Avoid IP-based blocking from target platforms | Reduce failed scrapes by 40% |
| **Geographic targeting** | Access geo-restricted content via region-specific proxies | Support 5+ regions |
| **Load distribution** | Distribute requests across multiple IPs | 10x throughput increase |
| **Compliance** | Respect platform rate limits per IP | Zero IP bans |

### User Stories

#### US-1: Proxy Configuration
```
As a crawler operator
I want to configure SOCKS5 proxies
So that I can route requests through specific IPs

Acceptance Criteria:
- Given a proxy URL (socks5://host:port)
- When I configure it in the scraper
- Then all requests route through that proxy
- And the proxy authentication works if credentials provided
```

#### US-2: Proxy Rotation
```
As a crawler operator
I want to rotate proxies automatically
So that no single IP gets rate-limited

Acceptance Criteria:
- Given a pool of 5+ proxies
- When making 10+ requests
- Then proxies are rotated in round-robin fashion
- And failed proxies are temporarily blacklisted
```

#### US-3: Tor Integration
```
As a privacy-conscious user
I want to use tor-socks-proxy-service
So that my scraping is anonymized

Acceptance Criteria:
- Given tor-socks-proxy-service is running
- When I configure PROXY_URL=socks5://tor-proxy:9050
- Then requests are routed through Tor network
- And IP changes on circuit renewal
```

---

## DDD: Domain-Driven Design

### Ubiquitous Language

| Term | Definition |
|------|------------|
| **Proxy** | A SOCKS5 intermediary server that routes traffic |
| **Proxy Pool** | A collection of available proxies for rotation |
| **Proxy Rotation** | The act of switching between proxies |
| **Blacklist** | Temporary exclusion of a failed proxy |
| **Health Check** | Verification that a proxy is operational |
| **Circuit** | Tor network path (for Tor proxies) |

### Bounded Context

```
┌─────────────────────────────────────────────────────────────┐
│                    PROXY MANAGEMENT CONTEXT                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Entities:                                                   │
│  - ProxyConfig (value object)                               │
│  - Proxy (entity with identity)                             │
│  - ProxyPool (aggregate root)                               │
│                                                               │
│  Value Objects:                                              │
│  - ProxyUrl (validated SOCKS5 URL)                          │
│  - ProxyStatus (enum: ACTIVE, FAILED, BLACKLISTED)          │
│  - ProxyStats (success_count, failure_count, latency_ms)    │
│                                                               │
│  Services:                                                   │
│  - ProxyManager (applies proxy to browser)                  │
│  - ProxyRotator (selects next proxy)                        │
│  - ProxyHealthChecker (validates proxy connectivity)        │
│                                                               │
│  Repository:                                                 │
│  - ProxyPoolRepository (persistence of proxy state)         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Aggregate Design

```python
# Aggregate Root
class ProxyPool:
    """
    Aggregate Root managing proxy collection and rotation.
    
    Invariants:
    - At least one proxy must be active
    - Blacklisted proxies cannot be selected
    - Pool size <= MAX_POOL_SIZE (100)
    """
    
    # Entities
    proxies: Dict[ProxyId, Proxy]
    
    # Value Objects
    rotation_strategy: RotationStrategy  # ROUND_ROBIN, LEAST_FAILURES, RANDOM
    blacklist_duration: timedelta
    
    # Methods
    add_proxy(proxy: Proxy) -> None
    remove_proxy(proxy_id: ProxyId) -> None
    get_next_proxy() -> Proxy
    blacklist_proxy(proxy_id: ProxyId, duration: timedelta) -> None
    health_check_all() -> HealthReport
```

---

## TDD: Test-Driven Development

### Red-Green-Refactor Cycle

#### Step 1: Write Failing Tests (RED)

```python
# crawler/tests/test_proxy.py
import pytest
from crawler.scraper.proxy import ProxyConfig, ProxyManager
from crawler.scraper.proxy_pool import ProxyPool, Proxy, ProxyStatus


class TestProxyConfig:
    """Test ProxyConfig value object"""
    
    def test_create_valid_proxy_config(self):
        """Given valid SOCKS5 URL, when created, then config is valid"""
        config = ProxyConfig.from_url("socks5://proxy.example.com:1080")
        
        assert config.host == "proxy.example.com"
        assert config.port == 1080
        assert config.username is None
        assert config.password is None
    
    def test_create_proxy_config_with_auth(self):
        """Given SOCKS5 URL with credentials, when created, then auth is stored"""
        config = ProxyConfig.from_url("socks5://user:pass@proxy.example.com:1080")
        
        assert config.host == "proxy.example.com"
        assert config.port == 1080
        assert config.username == "user"
        assert config.password == "pass"
    
    def test_invalid_proxy_url_raises(self):
        """Given invalid URL, when created, then ValueError is raised"""
        with pytest.raises(ValueError, match="Invalid proxy URL"):
            ProxyConfig.from_url("http://not-a-socks-proxy.com:8080")
    
    def test_supported_schemes(self):
        """Given various SOCKS schemes, when parsed, then all are accepted"""
        valid_urls = [
            "socks5://proxy.com:1080",
            "socks5h://proxy.com:1080",  # with hostname resolution
            "socks4://proxy.com:1080",
        ]
        
        for url in valid_urls:
            config = ProxyConfig.from_url(url)
            assert config.is_valid()


class TestProxyManager:
    """Test ProxyManager service"""
    
    def test_apply_proxy_to_browser(self, mock_browser):
        """Given proxy config, when applied to browser, then proxy is set"""
        config = ProxyConfig.from_url("socks5://proxy.example.com:1080")
        manager = ProxyManager()
        
        manager.apply_to_browser(mock_browser, config)
        
        mock_browser.set_proxy.assert_called_once_with(
            host="proxy.example.com",
            port=1080,
            username=None,
            password=None
        )
    
    def test_apply_proxy_with_auth(self, mock_browser):
        """Given proxy with auth, when applied, then credentials are passed"""
        config = ProxyConfig.from_url("socks5://user:pass@proxy.com:1080")
        manager = ProxyManager()
        
        manager.apply_to_browser(mock_browser, config)
        
        mock_browser.set_proxy.assert_called_once_with(
            host="proxy.com",
            port=1080,
            username="user",
            password="pass"
        )


class TestProxy:
    """Test Proxy entity"""
    
    def test_proxy_creation(self):
        """Given proxy config, when created, then proxy entity has identity"""
        config = ProxyConfig.from_url("socks5://proxy.example.com:1080")
        proxy = Proxy(config)
        
        assert proxy.id is not None
        assert proxy.status == ProxyStatus.ACTIVE
        assert proxy.stats.success_count == 0
        assert proxy.stats.failure_count == 0
    
    def test_proxy_record_success(self):
        """Given proxy, when success recorded, then success_count increments"""
        proxy = Proxy(ProxyConfig.from_url("socks5://proxy.com:1080"))
        
        proxy.record_success()
        proxy.record_success()
        
        assert proxy.stats.success_count == 2
        assert proxy.stats.failure_count == 0
        assert proxy.status == ProxyStatus.ACTIVE
    
    def test_proxy_record_failure(self):
        """Given proxy, when failure recorded, then failure_count increments"""
        proxy = Proxy(ProxyConfig.from_url("socks5://proxy.com:1080"))
        
        proxy.record_failure()
        proxy.record_failure()
        proxy.record_failure()
        
        assert proxy.stats.failure_count == 3
        assert proxy.status == ProxyStatus.FAILED
    
    def test_proxy_auto_blacklist_after_failures(self):
        """Given proxy with 5 failures, when recorded, then status is BLACKLISTED"""
        proxy = Proxy(ProxyConfig.from_url("socks5://proxy.com:1080"))
        
        for _ in range(5):
            proxy.record_failure()
        
        assert proxy.status == ProxyStatus.BLACKLISTED


class TestProxyPool:
    """Test ProxyPool aggregate root"""
    
    def test_create_pool(self):
        """Given empty pool, when created, then pool is empty"""
        pool = ProxyPool()
        
        assert pool.size == 0
        assert pool.active_count == 0
    
    def test_add_proxy_to_pool(self):
        """Given proxy, when added to pool, then pool size increases"""
        pool = ProxyPool()
        proxy = Proxy(ProxyConfig.from_url("socks5://proxy1.com:1080"))
        
        pool.add_proxy(proxy)
        
        assert pool.size == 1
        assert pool.active_count == 1
    
    def test_get_next_proxy_round_robin(self):
        """Given pool with 3 proxies, when getting next, then rotation is round-robin"""
        pool = ProxyPool(rotation_strategy="ROUND_ROBIN")
        proxies = [
            Proxy(ProxyConfig.from_url(f"socks5://proxy{i}.com:1080"))
            for i in range(3)
        ]
        for p in proxies:
            pool.add_proxy(p)
        
        # First rotation
        p1 = pool.get_next_proxy()
        p2 = pool.get_next_proxy()
        p3 = pool.get_next_proxy()
        
        assert p1.id != p2.id
        assert p2.id != p3.id
        assert p3.id != p1.id
        
        # Second rotation (should repeat)
        p4 = pool.get_next_proxy()
        assert p4.id == p1.id
    
    def test_get_next_proxy_skips_blacklisted(self):
        """Given pool with blacklisted proxy, when getting next, then blacklisted is skipped"""
        pool = ProxyPool()
        proxy1 = Proxy(ProxyConfig.from_url("socks5://proxy1.com:1080"))
        proxy2 = Proxy(ProxyConfig.from_url("socks5://proxy2.com:1080"))
        
        pool.add_proxy(proxy1)
        pool.add_proxy(proxy2)
        
        # Blacklist proxy1
        for _ in range(5):
            proxy1.record_failure()
        
        # Should only get proxy2
        next_proxy = pool.get_next_proxy()
        assert next_proxy.id == proxy2.id
    
    def test_pool_health_check(self):
        """Given pool, when health check runs, then report is generated"""
        pool = ProxyPool()
        # Add mocks or test proxies
        
        report = pool.health_check_all()
        
        assert report.total_proxies > 0
        assert report.healthy_count >= 0
        assert report.unhealthy_count >= 0
        assert isinstance(report.latency_avg_ms, (int, float))
    
    def test_pool_from_environment(self):
        """Given PROXY_POOL env var, when pool created, then proxies are parsed"""
        import os
        os.environ["PROXY_POOL"] = "socks5://proxy1.com:1080,socks5://proxy2.com:1080"
        
        pool = ProxyPool.from_environment()
        
        assert pool.size == 2
        del os.environ["PROXY_POOL"]
    
    def test_pool_from_tor_service(self):
        """Given TOR_PROXY_ENABLED, when pool created, then Tor proxy is used"""
        import os
        os.environ["TOR_PROXY_ENABLED"] = "true"
        os.environ["TOR_PROXY_URL"] = "socks5://tor-proxy:9050"
        
        pool = ProxyPool.from_environment()
        
        assert pool.size == 1
        del os.environ["TOR_PROXY_ENABLED"]
        del os.environ["TOR_PROXY_URL"]
```

#### Step 2: Run Tests (Should Fail)

```bash
# Run failing tests
pytest crawler/tests/test_proxy.py -v

# Expected: All tests FAIL (RED phase)
```

#### Step 3: Implement Code (GREEN)

```python
# crawler/scraper/proxy.py
"""
Proxy configuration and management for SOCKS5 proxies.

Domain: Proxy Management Context
Bounded Context: Scraper Module
"""

from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse
import re


@dataclass(frozen=True)
class ProxyConfig:
    """
    Value Object: Proxy configuration.
    
    Immutable configuration for a SOCKS5 proxy.
    """
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    scheme: str = "socks5"
    
    @classmethod
    def from_url(cls, url: str) -> "ProxyConfig":
        """
        Factory method: Parse proxy URL into config.
        
        Supported schemes: socks5, socks5h, socks4
        
        Examples:
            socks5://proxy.example.com:1080
            socks5://user:pass@proxy.example.com:1080
            socks5h://proxy.example.com:1080  (hostname resolution via proxy)
        """
        parsed = urlparse(url)
        
        if parsed.scheme not in ("socks5", "socks5h", "socks4"):
            raise ValueError(
                f"Invalid proxy URL: scheme '{parsed.scheme}' not supported. "
                f"Use socks5://, socks5h://, or socks4://"
            )
        
        if not parsed.hostname or not parsed.port:
            raise ValueError(f"Invalid proxy URL: missing host or port")
        
        return cls(
            host=parsed.hostname,
            port=parsed.port,
            username=parsed.username,
            password=parsed.password,
            scheme=parsed.scheme
        )
    
    def is_valid(self) -> bool:
        """Validate proxy configuration"""
        if not self.host or not self.port:
            return False
        if not (1 <= self.port <= 65535):
            return False
        return True
    
    def to_url(self) -> str:
        """Convert back to URL string"""
        if self.username and self.password:
            return f"{self.scheme}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.scheme}://{self.host}:{self.port}"
    
    def to_selenium_proxy(self) -> dict:
        """Convert to Selenium proxy format"""
        return {
            "proxyType": "MANUAL",
            "socksProxy": f"{self.host}:{self.port}",
            "socksVersion": 5 if "socks5" in self.scheme else 4,
            "socksUsername": self.username,
            "socksPassword": self.password,
        }


class ProxyManager:
    """
    Service: Apply proxy configuration to browser.
    
    Responsible for configuring SeleniumBase browser with proxy settings.
    """
    
    def apply_to_browser(self, browser, config: ProxyConfig) -> None:
        """
        Apply proxy configuration to SeleniumBase browser.
        
        Args:
            browser: SeleniumBase browser instance
            config: Proxy configuration
        """
        if not config.is_valid():
            raise ValueError(f"Cannot apply invalid proxy: {config.to_url()}")
        
        browser.set_proxy(
            host=config.host,
            port=config.port,
            username=config.username,
            password=config.password
        )
    
    def create_browser_with_proxy(self, browser_class, config: ProxyConfig, **kwargs):
        """
        Factory method: Create browser instance with proxy pre-configured.
        
        Args:
            browser_class: BrowserManager class
            config: Proxy configuration
            **kwargs: Additional browser arguments
            
        Returns:
            Configured browser instance
        """
        browser = browser_class(**kwargs)
        self.apply_to_browser(browser, config)
        return browser
```

```python
# crawler/scraper/proxy_pool.py
"""
Proxy pool management with rotation and health checking.

Domain: Proxy Management Context
Bounded Context: Scraper Module
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4
import os


class ProxyStatus(Enum):
    """Proxy health status"""
    ACTIVE = "active"
    FAILED = "failed"
    BLACKLISTED = "blacklisted"
    CHECKING = "checking"


class RotationStrategy(Enum):
    """Proxy rotation strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_FAILURES = "least_failures"
    RANDOM = "random"
    WEIGHTED = "weighted"  # based on success rate


@dataclass
class ProxyStats:
    """Proxy performance statistics"""
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[datetime] = None
    avg_latency_ms: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        return self.success_count / total
    
    @property
    def reliability_score(self) -> float:
        """Calculate reliability score (0-1)"""
        return self.success_rate * (1 - min(self.failure_count / 10, 1.0))


@dataclass
class ProxyId:
    """Proxy identity"""
    value: str = field(default_factory=lambda: str(uuid4()))
    
    def __hash__(self):
        return hash(self.value)
    
    def __eq__(self, other):
        if isinstance(other, ProxyId):
            return self.value == other.value
        return False


@dataclass
class Proxy:
    """
    Entity: Individual proxy with identity and state.
    
    Invariants:
    - Status changes based on failure count
    - Stats are updated atomically
    """
    config: 'ProxyConfig'
    id: ProxyId = field(default_factory=ProxyId)
    status: ProxyStatus = ProxyStatus.ACTIVE
    stats: ProxyStats = field(default_factory=ProxyStats)
    blacklist_until: Optional[datetime] = None
    
    def record_success(self, latency_ms: Optional[float] = None) -> None:
        """Record successful proxy usage"""
        self.stats.success_count += 1
        self.stats.last_used = datetime.utcnow()
        if latency_ms:
            # Moving average
            self.stats.avg_latency_ms = (
                (self.stats.avg_latency_ms * (self.stats.success_count - 1) + latency_ms)
                / self.stats.success_count
            )
        
        # Restore to active if was failed
        if self.status == ProxyStatus.FAILED:
            self.status = ProxyStatus.ACTIVE
    
    def record_failure(self) -> None:
        """Record proxy failure"""
        self.stats.failure_count += 1
        
        # Auto-fail after 3 failures
        if self.stats.failure_count >= 3:
            self.status = ProxyStatus.FAILED
        
        # Auto-blacklist after 5 failures
        if self.stats.failure_count >= 5:
            self.status = ProxyStatus.BLACKLISTED
    
    def blacklist(self, duration: timedelta) -> None:
        """Temporarily blacklist proxy"""
        self.status = ProxyStatus.BLACKLISTED
        self.blacklist_until = datetime.utcnow() + duration
    
    def unblacklist(self) -> None:
        """Remove from blacklist"""
        self.status = ProxyStatus.ACTIVE
        self.blacklist_until = None
        self.stats.failure_count = 0  # Reset failure count
    
    def is_available(self) -> bool:
        """Check if proxy is available for use"""
        if self.status == ProxyStatus.BLACKLISTED:
            if self.blacklist_until and datetime.utcnow() > self.blacklist_until:
                self.unblacklist()
                return True
            return False
        return self.status in (ProxyStatus.ACTIVE, ProxyStatus.FAILED)


@dataclass
class HealthReport:
    """Proxy pool health check report"""
    timestamp: datetime
    total_proxies: int
    healthy_count: int
    unhealthy_count: int
    blacklisted_count: int
    latency_avg_ms: float
    latency_p95_ms: float
    latency_p99_ms: float


class ProxyPool:
    """
    Aggregate Root: Manages collection of proxies with rotation.
    
    Invariants:
    - At least one proxy must be active
    - Blacklisted proxies cannot be selected
    - Pool size <= MAX_POOL_SIZE (100)
    """
    
    MAX_POOL_SIZE = 100
    DEFAULT_BLACKLIST_DURATION = timedelta(minutes=5)
    
    def __init__(
        self,
        rotation_strategy: RotationStrategy = RotationStrategy.ROUND_ROBIN,
        blacklist_duration: timedelta = DEFAULT_BLACKLIST_DURATION,
    ):
        self.proxies: Dict[ProxyId, Proxy] = {}
        self.rotation_strategy = rotation_strategy
        self.blacklist_duration = blacklist_duration
        self._round_robin_index = 0
    
    @property
    def size(self) -> int:
        """Total proxy count"""
        return len(self.proxies)
    
    @property
    def active_count(self) -> int:
        """Count of available proxies"""
        return sum(1 for p in self.proxies.values() if p.is_available())
    
    def add_proxy(self, proxy: Proxy) -> None:
        """
        Add proxy to pool.
        
        Raises:
            ValueError: If pool is at max capacity
        """
        if self.size >= self.MAX_POOL_SIZE:
            raise ValueError(f"Proxy pool is full (max {self.MAX_POOL_SIZE})")
        
        self.proxies[proxy.id] = proxy
    
    def remove_proxy(self, proxy_id: ProxyId) -> None:
        """Remove proxy from pool"""
        if proxy_id in self.proxies:
            del self.proxies[proxy_id]
    
    def get_next_proxy(self) -> Proxy:
        """
        Get next available proxy based on rotation strategy.
        
        Returns:
            Next proxy to use
            
        Raises:
            RuntimeError: If no proxies available
        """
        available = [p for p in self.proxies.values() if p.is_available()]
        
        if not available:
            raise RuntimeError("No proxies available in pool")
        
        if self.rotation_strategy == RotationStrategy.ROUND_ROBIN:
            proxy = self._round_robin_next(available)
        elif self.rotation_strategy == RotationStrategy.LEAST_FAILURES:
            proxy = self._least_failures_next(available)
        elif self.rotation_strategy == RotationStrategy.RANDOM:
            import random
            proxy = random.choice(available)
        else:
            proxy = available[0]
        
        proxy.stats.last_used = datetime.utcnow()
        return proxy
    
    def _round_robin_next(self, available: List[Proxy]) -> Proxy:
        """Round-robin proxy selection"""
        self._round_robin_index = self._round_robin_index % len(available)
        proxy = available[self._round_robin_index]
        self._round_robin_index += 1
        return proxy
    
    def _least_failures_next(self, available: List[Proxy]) -> Proxy:
        """Select proxy with fewest failures"""
        return min(available, key=lambda p: p.stats.failure_count)
    
    def blacklist_proxy(self, proxy_id: ProxyId, duration: Optional[timedelta] = None) -> None:
        """Blacklist a proxy temporarily"""
        if proxy_id in self.proxies:
            duration = duration or self.blacklist_duration
            self.proxies[proxy_id].blacklist(duration)
    
    def health_check_all(self) -> HealthReport:
        """
        Perform health check on all proxies.
        
        In production, this would make test requests through each proxy.
        For now, returns stats-based report.
        """
        latencies = [p.stats.avg_latency_ms for p in self.proxies.values() if p.stats.avg_latency_ms > 0]
        
        healthy = [p for p in self.proxies.values() if p.status == ProxyStatus.ACTIVE]
        unhealthy = [p for p in self.proxies.values() if p.status == ProxyStatus.FAILED]
        blacklisted = [p for p in self.proxies.values() if p.status == ProxyStatus.BLACKLISTED]
        
        return HealthReport(
            timestamp=datetime.utcnow(),
            total_proxies=self.size,
            healthy_count=len(healthy),
            unhealthy_count=len(unhealthy),
            blacklisted_count=len(blacklisted),
            latency_avg_ms=sum(latencies) / len(latencies) if latencies else 0.0,
            latency_p95_ms=sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else 0.0,
            latency_p99_ms=sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 1 else 0.0,
        )
    
    @classmethod
    def from_environment(cls) -> "ProxyPool":
        """
        Factory: Create pool from environment variables.
        
        Environment Variables:
            PROXY_POOL: Comma-separated list of proxy URLs
            TOR_PROXY_ENABLED: Set to "true" to use Tor
            TOR_PROXY_URL: Tor proxy URL (default: socks5://tor-proxy:9050)
        """
        from .proxy import ProxyConfig
        
        pool = cls()
        
        # Check for Tor proxy
        if os.environ.get("TOR_PROXY_ENABLED", "").lower() == "true":
            tor_url = os.environ.get("TOR_PROXY_URL", "socks5://tor-proxy:9050")
            config = ProxyConfig.from_url(tor_url)
            pool.add_proxy(Proxy(config=config))
        
        # Check for proxy pool
        proxy_pool_env = os.environ.get("PROXY_POOL")
        if proxy_pool_env:
            urls = [u.strip() for u in proxy_pool_env.split(",")]
            for url in urls:
                if url:
                    config = ProxyConfig.from_url(url)
                    pool.add_proxy(Proxy(config=config))
        
        return pool
```

#### Step 4: Run Tests (Should Pass)

```bash
# Run tests
pytest crawler/tests/test_proxy.py -v

# Expected: All tests PASS (GREEN phase)
```

#### Step 5: Refactor

```bash
# Check code quality
ruff check crawler/scraper/proxy.py crawler/scraper/proxy_pool.py
pytest --cov=crawler/scraper crawler/tests/test_proxy.py
```

---

## Integration with Existing Code

### Scraper Integration

```python
# crawler/scraper/scraper.py (modification)
from .proxy import ProxyManager, ProxyConfig
from .proxy_pool import ProxyPool

class Scraper:
    def __init__(
        self,
        platform: str,
        proxy_pool: Optional[ProxyPool] = None,
        # ... other params
    ):
        self.proxy_pool = proxy_pool
        self.proxy_manager = ProxyManager()
        self.current_proxy = None
    
    def scrape_url(self, url: str) -> ScrapedContent:
        # Get proxy from pool if available
        if self.proxy_pool:
            try:
                self.current_proxy = self.proxy_pool.get_next_proxy()
                self.proxy_manager.apply_to_browser(self.browser, self.current_proxy.config)
            except RuntimeError:
                # No proxies available, continue without proxy
                pass
        
        try:
            # Perform scraping
            result = self._do_scrape(url)
            
            # Record success
            if self.current_proxy:
                self.current_proxy.record_success()
            
            return result
            
        except Exception as e:
            # Record failure
            if self.current_proxy:
                self.current_proxy.record_failure()
            raise
```

### Configuration

```yaml
# config/platforms/{platform}/manifest.yaml
proxy:
  enabled: true
  rotation_strategy: "round_robin"  # round_robin, least_failures, random
  blacklist_duration_minutes: 5
  max_failures_before_blacklist: 5
```

---

## Acceptance Criteria Checklist

- [ ] Tests written and passing (RED → GREEN)
- [ ] Code refactored and clean
- [ ] Integration with Scraper complete
- [ ] Proxy rotation working
- [ ] Blacklist mechanism working
- [ ] Tor proxy support working
- [ ] Environment variable configuration working
- [ ] Documentation updated
- [ ] No linting errors
- [ ] Coverage > 90%
