# TDD: Rate Limiting Implementation

> **Version:** 1.0  
> **Date:** 2026-03-01  
> **Task:** 2.5 - Rate Limiting  
> **Files:** `crawler/scraper/rate_limiter.py`

---

## VDD: Value-Driven Design

### Business Value

| Value | Description | Metric |
|-------|-------------|--------|
| **Compliance** | Respect target platform rate limits | Zero IP bans |
| **Reliability** | Prevent request floods that trigger anti-bot | 99% success rate |
| **Ethics** | Be a good internet citizen | Follow robots.txt |
| **Stability** | Predictable, controlled scraping behavior | Consistent throughput |

### User Stories

#### US-1: Per-Domain Rate Limiting
```
As a crawler operator
I want to configure rate limits per domain
So that I don't overwhelm target servers

Acceptance Criteria:
- Given a rate limit of 10 requests/minute for beacon.com
- When I make 15 requests
- Then the last 5 requests wait until the next minute window
- And no errors occur
```

#### US-2: Default Rate Limits
```
As a crawler operator
I want a safe default rate limit for unknown domains
So that new platforms are scraped conservatively

Acceptance Criteria:
- Given an unknown domain
- When scraping starts
- Then default rate limit of 10 requests/minute is applied
- And this can be overridden in config
```

#### US-3: Adaptive Rate Limiting
```
As a crawler operator
I want rate limits to adapt based on server responses
So that I can maximize throughput without getting blocked

Acceptance Criteria:
- Given rate limit of 10 req/min
- When server responds with 429 (Too Many Requests)
- Then rate limit is reduced by 50%
- And backoff is applied
```

---

## DDD: Domain-Driven Design

### Ubiquitous Language

| Term | Definition |
|------|------------|
| **Rate Limit** | Maximum requests allowed per time window |
| **Domain** | Target hostname (e.g., beacon.com) |
| **Window** | Time period for rate limit (e.g., 1 minute) |
| **Token Bucket** | Algorithm for rate limiting with burst support |
| **Backoff** | Delay before retry after rate limit hit |
| **Throttle** | Slow down request rate |

### Bounded Context

```
┌─────────────────────────────────────────────────────────────┐
│                   RATE LIMITING CONTEXT                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Entities:                                                   │
│  - RateLimitRule (aggregate root)                           │
│  - DomainConfig (value object)                              │
│                                                               │
│  Value Objects:                                              │
│  - RequestsPerMinute (value object)                         │
│  - TimeWindow (value object)                                │
│  - BackoffStrategy (enum)                                   │
│                                                               │
│  Services:                                                   │
│  - RateLimiter (main service)                               │
│  - TokenBucket (algorithm implementation)                   │
│  - AdaptiveRateController (adjusts limits based on response)│
│                                                               │
│  Repository:                                                 │
│  - RateLimitRepository (persistence of rate limit state)    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Aggregate Design

```python
# Aggregate Root
class RateLimitRule:
    """
    Aggregate Root for rate limiting rules.
    
    Invariants:
    - Rate limit must be positive
    - Window must be positive
    - Backoff multiplier must be >= 1.0
    """
    
    # Value Objects
    domain: str
    requests_per_minute: int
    window_seconds: int
    burst_size: int  # Max requests in a burst
    
    # Configuration
    backoff_strategy: BackoffStrategy
    backoff_multiplier: float
    min_rate_limit: int  # Floor for adaptive limiting
    
    # Methods
    acquire() -> bool  # Try to acquire a slot
    wait_and_acquire()  # Block until slot available
    record_response(status_code: int)  # For adaptive limiting
    reset()  # Reset adaptive adjustments
```

---

## TDD: Test-Driven Development

### Test File Structure

```python
# crawler/tests/test_rate_limiter.py
import pytest
import time
from concurrent.futures import ThreadPoolExecutor
from crawler.scraper.rate_limiter import (
    RateLimiter,
    RateLimitRule,
    TokenBucket,
    BackoffStrategy,
    AdaptiveRateController,
    RequestsPerMinute,
    TimeWindow,
    DomainConfig,
)


class TestValueObjects:
    """Test value objects"""
    
    def test_requests_per_minute_valid(self):
        """Given valid RPM, when created, then value is stored"""
        rpm = RequestsPerMinute(10)
        assert rpm.value == 10
    
    def test_requests_per_minute_invalid(self):
        """Given invalid RPM, when created, then ValueError is raised"""
        with pytest.raises(ValueError, match="must be positive"):
            RequestsPerMinute(0)
        with pytest.raises(ValueError, match="must be positive"):
            RequestsPerMinute(-5)
    
    def test_time_window_creation(self):
        """Given valid window, when created, then seconds are stored"""
        window = TimeWindow(60)
        assert window.seconds == 60
    
    def test_time_window_invalid(self):
        """Given invalid window, when created, then ValueError is raised"""
        with pytest.raises(ValueError, match="must be positive"):
            TimeWindow(0)


class TestTokenBucket:
    """Test Token Bucket algorithm"""
    
    def test_bucket_creation(self):
        """Given rate and capacity, when created, then bucket is full"""
        bucket = TokenBucket(rate=10, capacity=10)  # 10 tokens/sec, max 10
        
        assert bucket.tokens == 10
        assert bucket.rate == 10
        assert bucket.capacity == 10
    
    def test_consume_token(self):
        """Given full bucket, when consuming, then token is removed"""
        bucket = TokenBucket(rate=10, capacity=10)
        
        result = bucket.consume(1)
        
        assert result is True
        assert bucket.tokens == 9
    
    def test_consume_multiple_tokens(self):
        """Given enough tokens, when consuming multiple, then all are removed"""
        bucket = TokenBucket(rate=10, capacity=10)
        
        result = bucket.consume(5)
        
        assert result is True
        assert bucket.tokens == 5
    
    def test_consume_insufficient_tokens(self):
        """Given insufficient tokens, when consuming, then False is returned"""
        bucket = TokenBucket(rate=10, capacity=10)
        
        # Consume all tokens
        for _ in range(10):
            bucket.consume(1)
        
        result = bucket.consume(1)
        
        assert result is False
        assert bucket.tokens == 0
    
    def test_token_regeneration(self):
        """Given empty bucket, when time passes, then tokens regenerate"""
        bucket = TokenBucket(rate=10, capacity=10)
        
        # Empty the bucket
        bucket.consume(10)
        
        # Wait for regeneration (0.5 sec = 5 tokens at 10/sec)
        time.sleep(0.5)
        
        assert bucket.tokens >= 4  # Allow some timing variance
    
    def test_burst_handling(self):
        """Given burst capacity, when burst occurs, then burst is allowed"""
        bucket = TokenBucket(rate=5, capacity=20)  # Allow burst of 20
        
        # Burst of 15 requests
        for _ in range(15):
            result = bucket.consume(1)
            assert result is True


class TestRateLimitRule:
    """Test RateLimitRule entity"""
    
    def test_rule_creation(self):
        """Given domain and rate, when created, then rule is configured"""
        rule = RateLimitRule(
            domain="beacon.com",
            requests_per_minute=10,
            window_seconds=60
        )
        
        assert rule.domain == "beacon.com"
        assert rule.requests_per_minute.value == 10
        assert rule.window_seconds == 60
    
    def test_rule_default_backoff(self):
        """Given rule without backoff, when created, then exponential backoff is default"""
        rule = RateLimitRule(
            domain="beacon.com",
            requests_per_minute=10,
            window_seconds=60
        )
        
        assert rule.backoff_strategy == BackoffStrategy.EXPONENTIAL
        assert rule.backoff_multiplier == 2.0
    
    def test_rule_custom_backoff(self):
        """Given custom backoff, when created, then values are stored"""
        rule = RateLimitRule(
            domain="beacon.com",
            requests_per_minute=10,
            window_seconds=60,
            backoff_strategy=BackoffStrategy.LINEAR,
            backoff_multiplier=1.5
        )
        
        assert rule.backoff_strategy == BackoffStrategy.LINEAR
        assert rule.backoff_multiplier == 1.5


class TestRateLimiter:
    """Test RateLimiter service"""
    
    def test_limiter_creation(self):
        """Given limiter, when created, then it's empty"""
        limiter = RateLimiter()
        
        assert limiter.get_all_domains() == []
    
    def test_add_rate_limit_rule(self):
        """Given rule, when added, then domain is tracked"""
        limiter = RateLimiter()
        rule = RateLimitRule(domain="beacon.com", requests_per_minute=10, window_seconds=60)
        
        limiter.add_rule(rule)
        
        assert "beacon.com" in limiter.get_all_domains()
    
    def test_acquire_allowed(self):
        """Given rule allows, when acquire called, then True is returned"""
        limiter = RateLimiter()
        rule = RateLimitRule(domain="beacon.com", requests_per_minute=10, window_seconds=60)
        limiter.add_rule(rule)
        
        result = limiter.acquire("beacon.com")
        
        assert result is True
    
    def test_acquire_rate_limited(self):
        """Given rate limit reached, when acquire called, then False is returned"""
        limiter = RateLimiter()
        rule = RateLimitRule(domain="beacon.com", requests_per_minute=5, window_seconds=60)
        limiter.add_rule(rule)
        
        # Exhaust the rate limit
        for _ in range(5):
            limiter.acquire("beacon.com")
        
        # Next should be rate limited
        result = limiter.acquire("beacon.com")
        
        assert result is False
    
    def test_acquire_unknown_domain_uses_default(self):
        """Given unknown domain, when acquire called, then default limit is used"""
        limiter = RateLimiter(default_rpm=10)
        
        result = limiter.acquire("unknown.com")
        
        assert result is True
    
    def test_wait_and_acquire(self):
        """Given rate limit, when wait_and_acquire called, then blocks until allowed"""
        limiter = RateLimiter()
        rule = RateLimitRule(domain="beacon.com", requests_per_minute=60, window_seconds=1)
        limiter.add_rule(rule)
        
        # Exhaust limit
        for _ in range(60):
            limiter.acquire("beacon.com")
        
        # This should wait and then succeed
        start = time.time()
        result = limiter.wait_and_acquire("beacon.com")
        elapsed = time.time() - start
        
        assert result is True
        assert elapsed >= 0.9  # Should have waited ~1 second
    
    def test_concurrent_acquire(self):
        """Given concurrent requests, when acquired, then rate limit is respected"""
        limiter = RateLimiter()
        rule = RateLimitRule(domain="beacon.com", requests_per_minute=10, window_seconds=1)
        limiter.add_rule(rule)
        
        successful = []
        
        def try_acquire():
            if limiter.acquire("beacon.com"):
                successful.append(1)
        
        # Try 20 concurrent requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(try_acquire) for _ in range(20)]
            for f in futures:
                f.result()
        
        # Only 10 should succeed
        assert len(successful) == 10
    
    def test_record_response_429(self):
        """Given 429 response, when recorded, then rate limit is reduced"""
        limiter = RateLimiter()
        rule = RateLimitRule(
            domain="beacon.com",
            requests_per_minute=10,
            window_seconds=60,
            adaptive=True
        )
        limiter.add_rule(rule)
        
        limiter.record_response("beacon.com", 429)
        
        # Rate limit should be reduced
        current_rule = limiter.get_rule("beacon.com")
        assert current_rule.requests_per_minute.value < 10
    
    def test_record_response_200(self):
        """Given 200 response, when recorded, then rate limit is maintained"""
        limiter = RateLimiter()
        rule = RateLimitRule(
            domain="beacon.com",
            requests_per_minute=10,
            window_seconds=60,
            adaptive=True
        )
        limiter.add_rule(rule)
        
        limiter.record_response("beacon.com", 200)
        
        current_rule = limiter.get_rule("beacon.com")
        assert current_rule.requests_per_minute.value == 10


class TestAdaptiveRateController:
    """Test AdaptiveRateController"""
    
    def test_controller_creation(self):
        """Given controller, when created, then defaults are set"""
        controller = AdaptiveRateController()
        
        assert controller.reduce_factor == 0.5
        assert controller.increase_factor == 1.1
        assert controller.min_rpm == 1
    
    def test_on_rate_limit_response(self):
        """Given 429 response, when handled, then rate is reduced"""
        controller = AdaptiveRateController()
        rule = RateLimitRule(domain="beacon.com", requests_per_minute=10, window_seconds=60)
        
        new_rpm = controller.on_rate_limit_response(rule)
        
        assert new_rpm == 5  # 50% reduction
    
    def test_on_success_response(self):
        """Given 200 response, when handled, then rate is slightly increased"""
        controller = AdaptiveRateController()
        rule = RateLimitRule(domain="beacon.com", requests_per_minute=10, window_seconds=60)
        
        new_rpm = controller.on_success_response(rule)
        
        assert new_rpm == 11  # 10% increase
    
    def test_on_success_respects_max(self):
        """Given rate at max, when success, then rate doesn't exceed original"""
        controller = AdaptiveRateController()
        rule = RateLimitRule(
            domain="beacon.com",
            requests_per_minute=10,
            window_seconds=60,
            original_rpm=10  # Original configured limit
        )
        
        # Increase beyond original
        rule.requests_per_minute = RequestsPerMinute(15)
        
        new_rpm = controller.on_success_response(rule)
        
        assert new_rpm == 10  # Capped at original


class TestDomainConfig:
    """Test DomainConfig value object"""
    
    def test_config_from_dict(self):
        """Given dict, when parsed, then config is created"""
        config_dict = {
            "beacon.com": {"requests_per_minute": 10, "window_seconds": 60},
            "qpublic.net": {"requests_per_minute": 20, "window_seconds": 60},
        }
        
        config = DomainConfig.from_dict(config_dict)
        
        assert config.get("beacon.com").requests_per_minute.value == 10
        assert config.get("qpublic.net").requests_per_minute.value == 20
    
    def test_config_with_defaults(self):
        """Given partial config, when accessed, then defaults are used"""
        config_dict = {
            "beacon.com": {"requests_per_minute": 10},  # No window_seconds
        }
        
        config = DomainConfig.from_dict(config_dict, default_window_seconds=60)
        
        assert config.get("beacon.com").window_seconds == 60
    
    def test_config_from_yaml(self, tmp_path):
        """Given YAML file, when loaded, then config is parsed"""
        yaml_content = """
domains:
  beacon.com:
    requests_per_minute: 10
    window_seconds: 60
  qpublic.net:
    requests_per_minute: 20
    window_seconds: 60
default:
  requests_per_minute: 5
  window_seconds: 60
"""
        yaml_file = tmp_path / "rate_limits.yaml"
        yaml_file.write_text(yaml_content)
        
        config = DomainConfig.from_yaml(yaml_file)
        
        assert config.get("beacon.com").requests_per_minute.value == 10
        assert config.default.requests_per_minute.value == 5


class TestIntegration:
    """Integration tests for rate limiting"""
    
    def test_full_scrape_flow_with_rate_limiting(self):
        """Given scraper with rate limiting, when scraping, then limits are respected"""
        from crawler.scraper.scraper import Scraper
        from crawler.scraper.rate_limiter import RateLimiter, RateLimitRule
        
        # Setup
        limiter = RateLimiter()
        rule = RateLimitRule(domain="example.com", requests_per_minute=5, window_seconds=1)
        limiter.add_rule(rule)
        
        scraper = Scraper(platform="test", rate_limiter=limiter)
        
        # Try to scrape 10 URLs quickly
        start = time.time()
        for i in range(10):
            # Simulate scrape (will be rate limited)
            limiter.wait_and_acquire("example.com")
        elapsed = time.time() - start
        
        # Should have taken at least 1 second (rate limit window)
        assert elapsed >= 0.9
    
    def test_adaptive_rate_limiting_simulation(self):
        """Given adaptive limiting, when 429s occur, then rate adapts"""
        limiter = RateLimiter()
        rule = RateLimitRule(
            domain="example.com",
            requests_per_minute=10,
            window_seconds=60,
            adaptive=True,
            original_rpm=10
        )
        limiter.add_rule(rule)
        
        # Simulate: 3 successes, then 429, then more successes
        for _ in range(3):
            limiter.record_response("example.com", 200)
        
        # Hit rate limit
        limiter.record_response("example.com", 429)
        
        # Rate should be reduced
        current_rule = limiter.get_rule("example.com")
        assert current_rule.requests_per_minute.value == 5
        
        # Simulate recover with successes
        for _ in range(5):
            limiter.record_response("example.com", 200)
        
        # Rate should gradually increase but not exceed original
        current_rule = limiter.get_rule("example.com")
        assert current_rule.requests_per_minute.value <= 10
```

---

## Implementation

```python
# crawler/scraper/rate_limiter.py
"""
Rate limiting for web scraping.

Domain: Rate Limiting Context
Bounded Context: Scraper Module

Algorithms:
- Token Bucket: For smooth rate limiting with burst support
- Sliding Window: For accurate per-minute limits
- Exponential Backoff: For rate limit recovery
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
import threading
import time
import yaml
from pathlib import Path


class BackoffStrategy(Enum):
    """Backoff strategies for rate limit recovery"""
    EXPONENTIAL = "exponential"  # Double wait time each retry
    LINEAR = "linear"  # Add fixed time each retry
    CONSTANT = "constant"  # Fixed wait time


@dataclass(frozen=True)
class RequestsPerMinute:
    """Value Object: Requests per minute rate"""
    value: int
    
    def __post_init__(self):
        if self.value <= 0:
            raise ValueError("RequestsPerMinute must be positive")


@dataclass(frozen=True)
class TimeWindow:
    """Value Object: Time window for rate limiting"""
    seconds: int
    
    def __post_init__(self):
        if self.seconds <= 0:
            raise ValueError("TimeWindow seconds must be positive")
    
    @property
    def as_timedelta(self) -> timedelta:
        return timedelta(seconds=self.seconds)


@dataclass
class TokenBucket:
    """
    Token Bucket algorithm implementation.
    
    Allows for burst traffic while maintaining average rate limit.
    """
    rate: float  # Tokens per second
    capacity: float  # Maximum tokens
    tokens: float = field(init=False)
    last_update: datetime = field(default_factory=datetime.utcnow)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    
    def __post_init__(self):
        self.tokens = self.capacity  # Start full
    
    def consume(self, tokens: float = 1.0) -> bool:
        """
        Try to consume tokens.
        
        Returns:
            True if tokens were consumed, False if insufficient
        """
        with self._lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def _refill(self) -> None:
        """Refill tokens based on elapsed time"""
        now = datetime.utcnow()
        elapsed = (now - self.last_update).total_seconds()
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now
    
    def time_until_tokens(self, tokens: float = 1.0) -> float:
        """Calculate time until specified tokens are available"""
        with self._lock:
            self._refill()
            
            if self.tokens >= tokens:
                return 0.0
            
            needed = tokens - self.tokens
            return needed / self.rate


@dataclass
class RateLimitRule:
    """
    Entity: Rate limiting rule for a domain.
    
    Invariants:
    - requests_per_minute must be positive
    - window_seconds must be positive
    - backoff_multiplier must be >= 1.0
    """
    domain: str
    requests_per_minute: RequestsPerMinute
    window_seconds: int = 60
    burst_size: Optional[int] = None
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    backoff_multiplier: float = 2.0
    min_rate_limit: int = 1
    
    # Adaptive limiting
    adaptive: bool = False
    original_rpm: Optional[int] = None  # Track original for adaptive recovery
    
    # Internal state
    _bucket: Optional[TokenBucket] = field(default=None, init=False)
    _current_rpm: Optional[int] = field(default=None, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    
    def __post_init__(self):
        if self.burst_size is None:
            self.burst_size = self.requests_per_minute.value
        
        if self.original_rpm is None:
            self.original_rpm = self.requests_per_minute.value
        
        self._current_rpm = self.requests_per_minute.value
        self._init_bucket()
    
    def _init_bucket(self) -> None:
        """Initialize token bucket"""
        tokens_per_second = self.requests_per_minute.value / 60.0
        self._bucket = TokenBucket(
            rate=tokens_per_second,
            capacity=float(self.burst_size)
        )
    
    def acquire(self, tokens: float = 1.0) -> bool:
        """Try to acquire permission to make a request"""
        with self._lock:
            if self._bucket is None:
                self._init_bucket()
            return self._bucket.consume(tokens)
    
    def wait_and_acquire(self, tokens: float = 1.0, timeout: Optional[float] = None) -> bool:
        """Block until tokens are available"""
        start = time.time()
        
        while True:
            if self.acquire(tokens):
                return True
            
            wait_time = self._bucket.time_until_tokens(tokens)
            
            if timeout and (time.time() - start) + wait_time > timeout:
                return False
            
            if wait_time > 0:
                time.sleep(min(wait_time, 0.1))  # Sleep in small increments
    
    def record_success(self) -> None:
        """Record successful request"""
        pass  # Token already consumed
    
    def record_failure(self, status_code: int) -> None:
        """Record failed request for adaptive limiting"""
        if self.adaptive and status_code == 429:
            self._reduce_rate()
    
    def _reduce_rate(self) -> None:
        """Reduce rate limit due to 429 response"""
        with self._lock:
            new_rpm = max(
                self._current_rpm // 2,
                self.min_rate_limit
            )
            if new_rpm != self._current_rpm:
                self._current_rpm = new_rpm
                self._init_bucket()
    
    def reset_rate(self) -> None:
        """Reset to original rate limit"""
        with self._lock:
            self._current_rpm = self.original_rpm
            self._init_bucket()
    
    @property
    def current_rpm(self) -> int:
        """Get current requests per minute (may be adjusted for adaptive)"""
        return self._current_rpm or self.requests_per_minute.value


@dataclass
class DomainConfig:
    """Value Object: Configuration for multiple domains"""
    rules: Dict[str, RateLimitRule] = field(default_factory=dict)
    default: Optional[RateLimitRule] = None
    
    def get(self, domain: str) -> Optional[RateLimitRule]:
        """Get rule for domain"""
        return self.rules.get(domain)
    
    @classmethod
    def from_dict(cls, data: dict, default_window_seconds: int = 60) -> "DomainConfig":
        """Create from dictionary"""
        rules = {}
        default_rule = None
        
        for domain, config in data.get("domains", {}).items():
            rules[domain] = RateLimitRule(
                domain=domain,
                requests_per_minute=RequestsPerMinute(config.get("requests_per_minute", 10)),
                window_seconds=config.get("window_seconds", default_window_seconds),
                adaptive=config.get("adaptive", False),
            )
        
        if "default" in data:
            default_config = data["default"]
            default_rule = RateLimitRule(
                domain="default",
                requests_per_minute=RequestsPerMinute(default_config.get("requests_per_minute", 10)),
                window_seconds=default_config.get("window_seconds", default_window_seconds),
            )
        
        return cls(rules=rules, default=default_rule)
    
    @classmethod
    def from_yaml(cls, path: Path) -> "DomainConfig":
        """Load from YAML file"""
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)


class AdaptiveRateController:
    """
    Service: Adaptive rate limit adjustment.
    
    Adjusts rate limits based on server responses.
    """
    
    def __init__(
        self,
        reduce_factor: float = 0.5,
        increase_factor: float = 1.1,
        min_rpm: int = 1,
    ):
        self.reduce_factor = reduce_factor
        self.increase_factor = increase_factor
        self.min_rpm = min_rpm
    
    def on_rate_limit_response(self, rule: RateLimitRule) -> int:
        """Handle 429 response"""
        new_rpm = max(
            int(rule.current_rpm * self.reduce_factor),
            self.min_rpm
        )
        return new_rpm
    
    def on_success_response(self, rule: RateLimitRule) -> int:
        """Handle 200 response"""
        new_rpm = int(rule.current_rpm * self.increase_factor)
        # Cap at original configured limit
        new_rpm = min(new_rpm, rule.original_rpm or new_rpm)
        return new_rpm


class RateLimiter:
    """
    Service: Main rate limiting service.
    
    Manages rate limits for multiple domains.
    """
    
    def __init__(
        self,
        default_rpm: int = 10,
        default_window_seconds: int = 60,
        config: Optional[DomainConfig] = None,
    ):
        self._rules: Dict[str, RateLimitRule] = {}
        self._default_rpm = default_rpm
        self._default_window = default_window_seconds
        self._config = config
        self._lock = threading.Lock()
        self._adaptive_controller = AdaptiveRateController()
    
    def add_rule(self, rule: RateLimitRule) -> None:
        """Add rate limit rule for a domain"""
        with self._lock:
            self._rules[rule.domain] = rule
    
    def get_rule(self, domain: str) -> Optional[RateLimitRule]:
        """Get rule for domain"""
        return self._rules.get(domain)
    
    def get_all_domains(self) -> List[str]:
        """Get all configured domains"""
        return list(self._rules.keys())
    
    def acquire(self, domain: str, tokens: float = 1.0) -> bool:
        """
        Try to acquire permission to make a request.
        
        Returns:
            True if allowed, False if rate limited
        """
        rule = self._get_or_create_rule(domain)
        return rule.acquire(tokens)
    
    def wait_and_acquire(self, domain: str, tokens: float = 1.0, timeout: Optional[float] = None) -> bool:
        """Block until request is allowed"""
        rule = self._get_or_create_rule(domain)
        return rule.wait_and_acquire(tokens, timeout)
    
    def record_response(self, domain: str, status_code: int) -> None:
        """Record server response for adaptive limiting"""
        rule = self._get_or_create_rule(domain)
        
        if rule.adaptive:
            if status_code == 429:
                new_rpm = self._adaptive_controller.on_rate_limit_response(rule)
                rule._current_rpm = new_rpm
                rule._init_bucket()
            elif 200 <= status_code < 300:
                new_rpm = self._adaptive_controller.on_success_response(rule)
                rule._current_rpm = new_rpm
                rule._init_bucket()
    
    def _get_or_create_rule(self, domain: str) -> RateLimitRule:
        """Get existing rule or create default"""
        with self._lock:
            if domain not in self._rules:
                # Create default rule for unknown domain
                self._rules[domain] = RateLimitRule(
                    domain=domain,
                    requests_per_minute=RequestsPerMinute(self._default_rpm),
                    window_seconds=self._default_window,
                )
            return self._rules[domain]
    
    @classmethod
    def from_config(cls, config_path: Path) -> "RateLimiter":
        """Create rate limiter from YAML config file"""
        config = DomainConfig.from_yaml(config_path)
        limiter = cls(
            default_rpm=config.default.requests_per_minute.value if config.default else 10,
            default_window_seconds=config.default.window_seconds if config.default else 60,
            config=config,
        )
        
        for rule in config.rules.values():
            limiter.add_rule(rule)
        
        return limiter
```

---

## Integration with Scraper

```python
# crawler/scraper/scraper.py (modification)
from .rate_limiter import RateLimiter, RateLimitRule

class Scraper:
    def __init__(
        self,
        platform: str,
        rate_limiter: Optional[RateLimiter] = None,
        # ... other params
    ):
        self.rate_limiter = rate_limiter or RateLimiter()
    
    def scrape_url(self, url: str) -> ScrapedContent:
        # Extract domain from URL
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        # Wait for rate limit
        self.rate_limiter.wait_and_acquire(domain)
        
        try:
            # Perform scraping
            result = self._do_scrape(url)
            
            # Record success
            self.rate_limiter.record_response(domain, 200)
            
            return result
            
        except Exception as e:
            # Record failure
            status_code = getattr(e, 'status_code', 500)
            self.rate_limiter.record_response(domain, status_code)
            raise
```

---

## Configuration Example

```yaml
# config/rate_limits.yaml
domains:
  beacon.com:
    requests_per_minute: 10
    window_seconds: 60
    adaptive: true
  
  qpublic.net:
    requests_per_minute: 20
    window_seconds: 60
    adaptive: true
  
  tax-sale.org:
    requests_per_minute: 5
    window_seconds: 60
    adaptive: true

default:
  requests_per_minute: 10
  window_seconds: 60
```

---

## Acceptance Criteria Checklist

- [ ] Tests written and passing (RED → GREEN → REFACTOR)
- [ ] Token Bucket algorithm implemented
- [ ] Per-domain rate limiting working
- [ ] Adaptive rate limiting working
- [ ] Default rate limits configured
- [ ] Integration with Scraper complete
- [ ] YAML configuration supported
- [ ] Thread-safe implementation
- [ ] No linting errors
- [ ] Coverage > 90%
