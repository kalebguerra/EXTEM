# Advanced Features Module for AI Image Generator Manager
# This module implements the improved features from the Chrome extension analysis

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
from motor.motor_asyncio import AsyncIOMotorDatabase
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class DynamicSelectorManager:
    """
    Advanced selector management system that allows dynamic updates
    without code changes - addressing the maintenance issue from the analysis
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.selector_cache = {}
        self.last_updated = {}
        
    async def get_selectors(self, provider: str) -> Dict[str, str]:
        """Get current selectors for a provider with caching"""
        now = time.time()
        
        # Check cache validity (5 minute cache)
        if (provider in self.selector_cache and 
            provider in self.last_updated and 
            now - self.last_updated[provider] < 300):
            return self.selector_cache[provider]
        
        # Fetch from database
        provider_doc = await self.db.providers.find_one({"name": provider})
        if not provider_doc:
            return {}
            
        selectors = provider_doc.get("selectors", {})
        
        # Update cache
        self.selector_cache[provider] = selectors
        self.last_updated[provider] = now
        
        logger.info(f"Updated selectors for {provider}: {list(selectors.keys())}")
        return selectors
    
    async def update_selectors(self, provider: str, new_selectors: Dict[str, str], 
                             reason: str = "Manual update") -> bool:
        """Update selectors dynamically"""
        try:
            result = await self.db.providers.update_one(
                {"name": provider},
                {
                    "$set": {
                        "selectors": new_selectors,
                        "updated_at": datetime.utcnow(),
                        "selector_update_reason": reason
                    }
                }
            )
            
            if result.modified_count > 0:
                # Clear cache to force refresh
                if provider in self.selector_cache:
                    del self.selector_cache[provider]
                if provider in self.last_updated:
                    del self.last_updated[provider]
                
                # Log update
                await self.db.selector_updates.insert_one({
                    "provider": provider,
                    "selectors": new_selectors,
                    "reason": reason,
                    "timestamp": datetime.utcnow()
                })
                
                logger.info(f"Successfully updated selectors for {provider}: {reason}")
                return True
            else:
                logger.warning(f"Failed to update selectors for {provider}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating selectors for {provider}: {str(e)}")
            return False
    
    async def auto_detect_selectors(self, provider: str, page_source: str) -> Dict[str, str]:
        """
        AI-powered selector detection (placeholder for future ML implementation)
        This would use machine learning to automatically detect UI changes
        """
        # For now, return common patterns
        common_patterns = {
            "prompt_input": [
                "textarea[placeholder*='prompt']",
                "input[placeholder*='prompt']",
                "div[contenteditable='true']",
                "div[data-slate-editor='true']"
            ],
            "generate_button": [
                "button:contains('Generate')",
                "button:contains('Create')",
                "button:contains('Submit')",
                "button[type='submit']"
            ],
            "result_images": [
                "img[src*='generated']",
                "img[src*='result']",
                ".result img",
                ".generated-image img"
            ]
        }
        
        # This would be enhanced with actual AI detection logic
        return {
            "prompt_input": common_patterns["prompt_input"][0],
            "generate_button": common_patterns["generate_button"][0], 
            "result_images": common_patterns["result_images"][0]
        }

class AdvancedRateLimiter:
    """
    Intelligent rate limiting system that adapts based on provider response patterns
    """
    
    def __init__(self):
        self.request_history = defaultdict(deque)  # provider -> [(timestamp, success)]
        self.adaptive_limits = defaultdict(lambda: {"requests_per_minute": 10, "burst_allowed": 3})
        self.cooldown_periods = defaultdict(float)  # provider -> cooldown_end_time
        
    async def can_make_request(self, provider: str) -> tuple[bool, float]:
        """
        Check if request can be made, return (allowed, wait_seconds)
        """
        now = time.time()
        
        # Check if in cooldown period
        if provider in self.cooldown_periods and now < self.cooldown_periods[provider]:
            wait_time = self.cooldown_periods[provider] - now
            return False, wait_time
        
        # Clean old entries (older than 1 minute)
        minute_ago = now - 60
        history = self.request_history[provider]
        while history and history[0][0] < minute_ago:
            history.popleft()
        
        # Get current limits
        limits = self.adaptive_limits[provider]
        current_requests = len(history)
        
        # Check if under limit
        if current_requests < limits["requests_per_minute"]:
            return True, 0
        
        # Calculate wait time until oldest request expires
        if history:
            wait_time = 60 - (now - history[0][0])
            return False, max(0, wait_time)
        
        return True, 0
    
    async def record_request(self, provider: str, success: bool, 
                           response_time: float = 0, error_type: str = None):
        """Record request result and adapt limits"""
        now = time.time()
        self.request_history[provider].append((now, success, response_time, error_type))
        
        # Analyze recent performance and adapt
        await self._adapt_limits(provider)
        
        # Handle specific error types
        if not success and error_type:
            await self._handle_error(provider, error_type)
    
    async def _adapt_limits(self, provider: str):
        """Intelligently adapt rate limits based on performance"""
        history = self.request_history[provider]
        if len(history) < 5:  # Need minimum data
            return
        
        recent_requests = list(history)[-10:]  # Last 10 requests
        success_rate = sum(1 for _, success, _, _ in recent_requests if success) / len(recent_requests)
        avg_response_time = sum(rt for _, _, rt, _ in recent_requests if rt > 0) / len([rt for _, _, rt, _ in recent_requests if rt > 0]) if any(rt for _, _, rt, _ in recent_requests) else 0
        
        current_limit = self.adaptive_limits[provider]["requests_per_minute"]
        
        # Increase limit if performing well
        if success_rate > 0.95 and avg_response_time < 2.0 and current_limit < 60:
            new_limit = min(current_limit + 2, 60)
            self.adaptive_limits[provider]["requests_per_minute"] = new_limit
            logger.info(f"Increased rate limit for {provider} to {new_limit} req/min (success: {success_rate:.2%})")
        
        # Decrease limit if having issues
        elif success_rate < 0.8 or avg_response_time > 10.0:
            new_limit = max(current_limit - 2, 3)
            self.adaptive_limits[provider]["requests_per_minute"] = new_limit
            logger.warning(f"Decreased rate limit for {provider} to {new_limit} req/min (success: {success_rate:.2%}, avg_time: {avg_response_time:.1f}s)")
    
    async def _handle_error(self, provider: str, error_type: str):
        """Handle specific error types with appropriate responses"""
        now = time.time()
        
        error_responses = {
            "rate_limit": 300,      # 5 minute cooldown
            "server_error": 60,     # 1 minute cooldown  
            "timeout": 30,          # 30 second cooldown
            "maintenance": 900,     # 15 minute cooldown
            "quota_exceeded": 3600  # 1 hour cooldown
        }
        
        cooldown_seconds = error_responses.get(error_type, 60)
        self.cooldown_periods[provider] = now + cooldown_seconds
        
        logger.warning(f"Applied {cooldown_seconds}s cooldown to {provider} due to {error_type}")

class EnhancedErrorRecovery:
    """
    Advanced error recovery system with multiple fallback strategies
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, selector_manager: DynamicSelectorManager):
        self.db = db
        self.selector_manager = selector_manager
        self.failure_patterns = defaultdict(list)  # provider -> [failure_info]
        
    async def handle_automation_failure(self, provider: str, job_id: str, 
                                      error_type: str, error_details: Dict[str, Any]) -> bool:
        """
        Handle automation failures with intelligent recovery strategies
        """
        logger.info(f"Handling automation failure for {provider} job {job_id}: {error_type}")
        
        # Record failure pattern
        failure_info = {
            "timestamp": datetime.utcnow(),
            "job_id": job_id,
            "error_type": error_type,
            "details": error_details
        }
        self.failure_patterns[provider].append(failure_info)
        
        # Try recovery strategies in order
        recovery_strategies = [
            self._try_selector_update,
            self._try_alternative_selectors,
            self._try_different_approach,
            self._try_manual_fallback
        ]
        
        for strategy in recovery_strategies:
            try:
                success = await strategy(provider, job_id, error_type, error_details)
                if success:
                    logger.info(f"Recovery successful using {strategy.__name__} for {provider}")
                    return True
            except Exception as e:
                logger.error(f"Recovery strategy {strategy.__name__} failed: {str(e)}")
                continue
        
        logger.error(f"All recovery strategies failed for {provider} job {job_id}")
        return False
    
    async def _try_selector_update(self, provider: str, job_id: str, 
                                 error_type: str, error_details: Dict[str, Any]) -> bool:
        """Try updating selectors based on error analysis"""
        if error_type != "element_not_found":
            return False
        
        missing_element = error_details.get("missing_element")
        if not missing_element:
            return False
        
        # Try to find alternative selectors
        current_selectors = await self.selector_manager.get_selectors(provider)
        alternative_selectors = await self._find_alternative_selectors(
            provider, missing_element, error_details.get("page_source", "")
        )
        
        if alternative_selectors:
            success = await self.selector_manager.update_selectors(
                provider, 
                {**current_selectors, **alternative_selectors},
                f"Auto-recovery for missing element: {missing_element}"
            )
            return success
        
        return False
    
    async def _try_alternative_selectors(self, provider: str, job_id: str,
                                       error_type: str, error_details: Dict[str, Any]) -> bool:
        """Try using backup selector strategies"""
        if error_type != "element_not_found":
            return False
        
        # Implement alternative selector logic
        # This would include XPath, CSS fallbacks, etc.
        return False
    
    async def _try_different_approach(self, provider: str, job_id: str,
                                    error_type: str, error_details: Dict[str, Any]) -> bool:
        """Try a completely different automation approach"""
        # Could switch from DOM manipulation to keyboard shortcuts,
        # API calls if available, etc.
        return False
    
    async def _try_manual_fallback(self, provider: str, job_id: str,
                                 error_type: str, error_details: Dict[str, Any]) -> bool:
        """Fallback to manual processing queue"""
        # Queue job for manual processing
        await self.db.manual_queue.insert_one({
            "job_id": job_id,
            "provider": provider,
            "error_type": error_type,
            "error_details": error_details,
            "queued_at": datetime.utcnow(),
            "status": "pending_manual"
        })
        
        logger.info(f"Job {job_id} queued for manual processing")
        return True
    
    async def _find_alternative_selectors(self, provider: str, missing_element: str,
                                        page_source: str) -> Dict[str, str]:
        """Find alternative selectors for missing elements"""
        # This would include intelligent selector discovery
        # For now, return common alternatives
        
        alternatives = {
            "prompt_input": [
                "textarea[name*='prompt']",
                "input[name*='prompt']", 
                "#prompt",
                ".prompt-input",
                "[data-testid*='prompt']"
            ],
            "generate_button": [
                "button[data-testid*='generate']",
                "button[aria-label*='generate']",
                ".generate-btn",
                "#generate",
                "input[type='submit'][value*='generate']"
            ]
        }
        
        if missing_element in alternatives:
            return {missing_element: alternatives[missing_element][0]}
        
        return {}

class SmartJobScheduler:
    """
    Intelligent job scheduling system that optimizes based on provider performance,
    time of day, and historical success rates
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.provider_performance = defaultdict(dict)
        self.optimal_times = defaultdict(list)
        
    async def schedule_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a job with optimal timing and provider selection"""
        provider = job_data.get("provider")
        priority = job_data.get("priority", 1)
        
        # Analyze best time to run
        optimal_delay = await self._calculate_optimal_delay(provider)
        
        # Adjust priority based on historical performance
        adjusted_priority = await self._adjust_priority(provider, priority)
        
        # Schedule the job
        scheduled_time = datetime.utcnow() + timedelta(seconds=optimal_delay)
        
        job_data.update({
            "scheduled_time": scheduled_time,
            "adjusted_priority": adjusted_priority,
            "scheduling_reason": f"Optimal delay: {optimal_delay}s, Priority: {priority}->{adjusted_priority}"
        })
        
        return job_data
    
    async def _calculate_optimal_delay(self, provider: str) -> float:
        """Calculate optimal delay based on provider performance patterns"""
        # Analyze recent job completion times for the provider
        recent_jobs = await self.db.jobs.find({
            "provider": provider,
            "status": "completed",
            "completed_at": {"$gte": datetime.utcnow() - timedelta(hours=24)}
        }).sort("completed_at", -1).limit(50).to_list(50)
        
        if not recent_jobs:
            return 0  # No delay if no historical data
        
        # Calculate average processing time
        processing_times = []
        for job in recent_jobs:
            if job.get("completed_at") and job.get("created_at"):
                processing_time = (job["completed_at"] - job["created_at"]).total_seconds()
                processing_times.append(processing_time)
        
        if processing_times:
            avg_processing_time = sum(processing_times) / len(processing_times)
            # Add some buffer time
            return min(avg_processing_time * 0.1, 30)  # Max 30 second delay
        
        return 0
    
    async def _adjust_priority(self, provider: str, base_priority: int) -> int:
        """Adjust job priority based on provider reliability"""
        # Get recent success rate for provider
        recent_jobs = await self.db.jobs.count_documents({
            "provider": provider,
            "created_at": {"$gte": datetime.utcnow() - timedelta(hours=6)}
        })
        
        successful_jobs = await self.db.jobs.count_documents({
            "provider": provider,
            "status": "completed",
            "created_at": {"$gte": datetime.utcnow() - timedelta(hours=6)}
        })
        
        if recent_jobs > 0:
            success_rate = successful_jobs / recent_jobs
            
            # Boost priority for reliable providers
            if success_rate > 0.9:
                return min(base_priority + 1, 5)
            elif success_rate < 0.5:
                return max(base_priority - 1, 1)
        
        return base_priority

class AdvancedAnalytics:
    """
    Comprehensive analytics system for monitoring and optimization
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        
    async def generate_performance_report(self, time_range: str = "24h") -> Dict[str, Any]:
        """Generate detailed performance analytics"""
        time_delta = {
            "1h": timedelta(hours=1),
            "24h": timedelta(hours=24), 
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }.get(time_range, timedelta(hours=24))
        
        start_time = datetime.utcnow() - time_delta
        
        # Aggregate job statistics
        job_stats = await self._get_job_statistics(start_time)
        provider_stats = await self._get_provider_statistics(start_time)
        error_analysis = await self._get_error_analysis(start_time)
        performance_trends = await self._get_performance_trends(start_time)
        
        return {
            "time_range": time_range,
            "generated_at": datetime.utcnow(),
            "job_statistics": job_stats,
            "provider_performance": provider_stats,
            "error_analysis": error_analysis,
            "performance_trends": performance_trends,
            "recommendations": await self._generate_recommendations(job_stats, provider_stats, error_analysis)
        }
    
    async def _get_job_statistics(self, start_time: datetime) -> Dict[str, Any]:
        """Get comprehensive job statistics"""
        pipeline = [
            {"$match": {"created_at": {"$gte": start_time}}},
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "avg_processing_time": {
                        "$avg": {
                            "$subtract": ["$completed_at", "$created_at"]
                        }
                    }
                }
            }
        ]
        
        results = await self.db.jobs.aggregate(pipeline).to_list(None)
        
        total_jobs = sum(result["count"] for result in results)
        completed_jobs = next((r["count"] for r in results if r["_id"] == "completed"), 0)
        failed_jobs = next((r["count"] for r in results if r["_id"] == "failed"), 0)
        
        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "success_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
            "failure_rate": (failed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
            "status_breakdown": {result["_id"]: result["count"] for result in results}
        }
    
    async def _get_provider_statistics(self, start_time: datetime) -> Dict[str, Any]:
        """Get provider-specific performance statistics"""
        pipeline = [
            {"$match": {"created_at": {"$gte": start_time}}},
            {
                "$group": {
                    "_id": "$provider",
                    "total_jobs": {"$sum": 1},
                    "completed_jobs": {
                        "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                    },
                    "failed_jobs": {
                        "$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}
                    },
                    "avg_processing_time": {
                        "$avg": {
                            "$cond": [
                                {"$eq": ["$status", "completed"]},
                                {"$subtract": ["$completed_at", "$created_at"]},
                                None
                            ]
                        }
                    }
                }
            }
        ]
        
        results = await self.db.jobs.aggregate(pipeline).to_list(None)
        
        provider_stats = {}
        for result in results:
            provider = result["_id"]
            total = result["total_jobs"]
            completed = result["completed_jobs"]
            
            provider_stats[provider] = {
                "total_jobs": total,
                "completed_jobs": completed,
                "failed_jobs": result["failed_jobs"],
                "success_rate": (completed / total * 100) if total > 0 else 0,
                "avg_processing_time_seconds": result["avg_processing_time"] / 1000 if result["avg_processing_time"] else 0
            }
        
        return provider_stats
    
    async def _get_error_analysis(self, start_time: datetime) -> Dict[str, Any]:
        """Analyze error patterns and frequencies"""
        pipeline = [
            {"$match": {
                "created_at": {"$gte": start_time},
                "status": "failed",
                "error": {"$exists": True, "$ne": None}
            }},
            {
                "$group": {
                    "_id": "$error",
                    "count": {"$sum": 1},
                    "providers": {"$addToSet": "$provider"}
                }
            },
            {"$sort": {"count": -1}}
        ]
        
        results = await self.db.jobs.aggregate(pipeline).to_list(None)
        
        return {
            "total_errors": sum(result["count"] for result in results),
            "error_types": [{
                "error_message": result["_id"],
                "count": result["count"],
                "affected_providers": result["providers"]
            } for result in results[:10]]  # Top 10 errors
        }
    
    async def _get_performance_trends(self, start_time: datetime) -> Dict[str, Any]:
        """Get performance trends over time"""
        # This would include hourly/daily trend analysis
        # For now, return basic trending data
        
        return {
            "trend_direction": "stable",
            "performance_change": 0,
            "notes": "Trend analysis requires more historical data"
        }
    
    async def _generate_recommendations(self, job_stats: Dict, provider_stats: Dict, 
                                      error_analysis: Dict) -> List[str]:
        """Generate actionable recommendations based on analytics"""
        recommendations = []
        
        # Success rate recommendations
        if job_stats.get("success_rate", 0) < 80:
            recommendations.append("Overall success rate is below 80%. Consider reviewing error patterns and updating automation scripts.")
        
        # Provider-specific recommendations
        for provider, stats in provider_stats.items():
            if stats["success_rate"] < 70:
                recommendations.append(f"{provider} has low success rate ({stats['success_rate']:.1f}%). Review selectors and automation logic.")
            
            if stats.get("avg_processing_time_seconds", 0) > 120:
                recommendations.append(f"{provider} has high processing time ({stats['avg_processing_time_seconds']:.1f}s). Consider optimizing timeouts.")
        
        # Error pattern recommendations
        if error_analysis.get("total_errors", 0) > job_stats.get("total_jobs", 1) * 0.2:
            recommendations.append("High error rate detected. Review common error patterns and implement fixes.")
        
        if not recommendations:
            recommendations.append("System is performing well! No immediate optimizations needed.")
        
        return recommendations

# Export classes for use in main application
__all__ = [
    'DynamicSelectorManager',
    'AdvancedRateLimiter', 
    'EnhancedErrorRecovery',
    'SmartJobScheduler',
    'AdvancedAnalytics'
]