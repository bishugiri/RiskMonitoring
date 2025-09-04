"""
Performance monitoring script for the Risk Monitor application.
Tracks processing times and identifies bottlenecks.
"""

import time
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass
from contextlib import contextmanager

@dataclass
class PerformanceMetric:
    """Performance metric data class"""
    operation: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    error: str = None
    metadata: Dict[str, Any] = None

class PerformanceMonitor:
    """Monitors and tracks performance metrics"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.current_operations: Dict[str, float] = {}
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, "performance.log")),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def track_operation(self, operation_name: str, metadata: Dict[str, Any] = None):
        """Context manager to track operation performance"""
        start_time = time.time()
        self.current_operations[operation_name] = start_time
        
        try:
            yield
            success = True
            error = None
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            metric = PerformanceMetric(
                operation=operation_name,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=success,
                error=error,
                metadata=metadata or {}
            )
            
            self.metrics.append(metric)
            del self.current_operations[operation_name]
            
            # Log performance
            if success:
                self.logger.info(f"✅ {operation_name} completed in {duration:.2f}s")
            else:
                self.logger.error(f"❌ {operation_name} failed after {duration:.2f}s: {error}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.metrics:
            return {"message": "No metrics recorded"}
        
        successful_metrics = [m for m in self.metrics if m.success]
        failed_metrics = [m for m in self.metrics if not m.success]
        
        # Group by operation
        operation_stats = {}
        for metric in self.metrics:
            op_name = metric.operation
            if op_name not in operation_stats:
                operation_stats[op_name] = {
                    'count': 0,
                    'total_duration': 0,
                    'success_count': 0,
                    'error_count': 0,
                    'min_duration': float('inf'),
                    'max_duration': 0,
                    'avg_duration': 0
                }
            
            stats = operation_stats[op_name]
            stats['count'] += 1
            stats['total_duration'] += metric.duration
            stats['min_duration'] = min(stats['min_duration'], metric.duration)
            stats['max_duration'] = max(stats['max_duration'], metric.duration)
            
            if metric.success:
                stats['success_count'] += 1
            else:
                stats['error_count'] += 1
        
        # Calculate averages
        for op_name, stats in operation_stats.items():
            stats['avg_duration'] = stats['total_duration'] / stats['count']
        
        # Overall statistics
        total_duration = sum(m.duration for m in self.metrics)
        total_operations = len(self.metrics)
        success_rate = len(successful_metrics) / total_operations if total_operations > 0 else 0
        
        return {
            'summary': {
                'total_operations': total_operations,
                'successful_operations': len(successful_metrics),
                'failed_operations': len(failed_metrics),
                'success_rate': f"{success_rate:.2%}",
                'total_duration': f"{total_duration:.2f}s",
                'average_duration': f"{total_duration/total_operations:.2f}s" if total_operations > 0 else "0s"
            },
            'operation_stats': operation_stats,
            'bottlenecks': self._identify_bottlenecks(),
            'recommendations': self._generate_recommendations()
        }
    
    def _identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        # Find operations taking more than 10 seconds
        slow_operations = [m for m in self.metrics if m.duration > 10]
        if slow_operations:
            bottlenecks.append({
                'type': 'slow_operations',
                'description': f"{len(slow_operations)} operations took more than 10 seconds",
                'operations': [{'name': m.operation, 'duration': f"{m.duration:.2f}s"} for m in slow_operations]
            })
        
        # Find operations with high failure rates
        operation_failure_rates = {}
        for metric in self.metrics:
            op_name = metric.operation
            if op_name not in operation_failure_rates:
                operation_failure_rates[op_name] = {'total': 0, 'failures': 0}
            
            operation_failure_rates[op_name]['total'] += 1
            if not metric.success:
                operation_failure_rates[op_name]['failures'] += 1
        
        high_failure_ops = [
            {'name': op, 'failure_rate': f"{stats['failures']/stats['total']:.2%}"}
            for op, stats in operation_failure_rates.items()
            if stats['failures']/stats['total'] > 0.2  # More than 20% failure rate
        ]
        
        if high_failure_ops:
            bottlenecks.append({
                'type': 'high_failure_rate',
                'description': f"{len(high_failure_ops)} operations have high failure rates",
                'operations': high_failure_ops
            })
        
        return bottlenecks
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        # Check for slow operations
        slow_ops = [m for m in self.metrics if m.duration > 30]
        if slow_ops:
            recommendations.append(f"Consider optimizing {len(slow_ops)} slow operations (>30s)")
        
        # Check for high failure rates
        failed_ops = [m for m in self.metrics if not m.success]
        if len(failed_ops) > len(self.metrics) * 0.1:  # More than 10% failures
            recommendations.append("High failure rate detected - review error handling and retry logic")
        
        # Check for sequential operations that could be parallelized
        sequential_ops = [m for m in self.metrics if 'article' in m.operation.lower() and m.duration > 5]
        if len(sequential_ops) > 3:
            recommendations.append("Multiple sequential article operations detected - consider batch processing")
        
        return recommendations
    
    def save_report(self, filename: str = None):
        """Save performance report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_report_{timestamp}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': self.get_summary(),
            'detailed_metrics': [
                {
                    'operation': m.operation,
                    'start_time': datetime.fromtimestamp(m.start_time).isoformat(),
                    'end_time': datetime.fromtimestamp(m.end_time).isoformat(),
                    'duration': m.duration,
                    'success': m.success,
                    'error': m.error,
                    'metadata': m.metadata
                }
                for m in self.metrics
            ]
        }
        
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output")
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"Performance report saved to {filepath}")
        return filepath

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def track_performance(operation_name: str, metadata: Dict[str, Any] = None):
    """Decorator to track function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with performance_monitor.track_operation(operation_name, metadata):
                return func(*args, **kwargs)
        return wrapper
    return decorator
