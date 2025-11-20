"""Lightweight monitoring and health checks for indie hackers."""

import logging
import time
import psutil
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Lightweight performance monitoring.

    Tracks key metrics without heavy dependencies or external services.
    """

    def __init__(self):
        """Initialize performance monitor."""
        self.start_time = time.time()
        self.metrics = {
            "api_calls": {},
            "errors": {},
            "cache_hits": 0,
            "cache_misses": 0,
        }

    def record_api_call(self, service: str, duration: float, success: bool = True):
        """Record an API call."""
        if service not in self.metrics["api_calls"]:
            self.metrics["api_calls"][service] = {
                "total": 0,
                "success": 0,
                "failed": 0,
                "total_duration": 0,
            }

        stats = self.metrics["api_calls"][service]
        stats["total"] += 1
        stats["total_duration"] += duration

        if success:
            stats["success"] += 1
        else:
            stats["failed"] += 1

    def record_error(self, error_type: str):
        """Record an error."""
        if error_type not in self.metrics["errors"]:
            self.metrics["errors"][error_type] = 0

        self.metrics["errors"][error_type"] += 1

    def record_cache_hit(self):
        """Record a cache hit."""
        self.metrics["cache_hits"] += 1

    def record_cache_miss(self):
        """Record a cache miss."""
        self.metrics["cache_misses"] += 1

    def get_system_stats(self) -> Dict:
        """Get current system stats."""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
            }
        except:
            return {}

    def get_stats(self) -> Dict:
        """Get all performance stats."""
        uptime = time.time() - self.start_time

        stats = {
            "uptime_seconds": uptime,
            "uptime_formatted": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m",
            "metrics": self.metrics.copy(),
            "system": self.get_system_stats(),
        }

        # Calculate averages
        for service, data in self.metrics["api_calls"].items():
            if data["total"] > 0:
                data["avg_duration"] = data["total_duration"] / data["total"]
                data["success_rate"] = (data["success"] / data["total"]) * 100

        # Calculate cache hit rate
        total_cache_ops = stats["metrics"]["cache_hits"] + stats["metrics"]["cache_misses"]
        if total_cache_ops > 0:
            stats["metrics"]["cache_hit_rate"] = (stats["metrics"]["cache_hits"] / total_cache_ops) * 100
        else:
            stats["metrics"]["cache_hit_rate"] = 0

        return stats

    def log_stats(self):
        """Log current stats."""
        stats = self.get_stats()

        logger.info("=" * 60)
        logger.info("PERFORMANCE STATS")
        logger.info("=" * 60)
        logger.info(f"Uptime: {stats['uptime_formatted']}")

        for service, data in stats["metrics"]["api_calls"].items():
            logger.info(
                f"{service}: {data['total']} calls, "
                f"{data.get('avg_duration', 0):.3f}s avg, "
                f"{data.get('success_rate', 0):.1f}% success"
            )

        logger.info(
            f"Cache: {stats['metrics']['cache_hit_rate']:.1f}% hit rate "
            f"({stats['metrics']['cache_hits']} hits, {stats['metrics']['cache_misses']} misses)"
        )

        if stats["system"]:
            logger.info(
                f"System: CPU {stats['system'].get('cpu_percent', 0):.1f}%, "
                f"Memory {stats['system'].get('memory_percent', 0):.1f}%, "
                f"Disk {stats['system'].get('disk_usage', 0):.1f}%"
            )

        logger.info("=" * 60)

    def export_stats(self, filepath: Optional[Path] = None):
        """Export stats to JSON file."""
        import json

        stats = self.get_stats()
        stats["exported_at"] = datetime.now().isoformat()

        filepath = filepath or Path("metrics") / f"stats_{int(time.time())}.json"
        filepath.parent.mkdir(exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(stats, f, indent=2)

        logger.info(f"Stats exported to {filepath}")


# Global monitor instance
_monitor: Optional[PerformanceMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """Get singleton performance monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


class HealthCheck:
    """Simple health check system."""

    @staticmethod
    def check_apis() -> Dict[str, bool]:
        """Check if APIs are accessible."""
        from ..config.settings import get_settings

        settings = get_settings()
        health = {}

        # Check if API keys are configured
        health["apollo_configured"] = bool(settings.apollo_api_key)
        health["elevenlabs_configured"] = bool(settings.elevenlabs_api_key)
        health["llm_configured"] = bool(
            settings.anthropic_api_key or settings.openai_api_key
        )

        return health

    @staticmethod
    def check_system() -> Dict[str, bool]:
        """Check system resources."""
        try:
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                "memory_available": mem.percent < 90,  # Less than 90% used
                "disk_available": disk.percent < 90,   # Less than 90% used
            }
        except:
            return {}

    @staticmethod
    def check_cache() -> Dict[str, bool]:
        """Check cache system."""
        from .cache import get_cache_manager

        try:
            cache = get_cache_manager()
            stats = cache.get_stats()

            return {
                "cache_initialized": True,
                "cache_entries": stats.get("total_entries", 0),
            }
        except:
            return {"cache_initialized": False}

    @staticmethod
    def run_health_check() -> Dict:
        """Run full health check."""
        return {
            "timestamp": datetime.now().isoformat(),
            "apis": HealthCheck.check_apis(),
            "system": HealthCheck.check_system(),
            "cache": HealthCheck.check_cache(),
        }
