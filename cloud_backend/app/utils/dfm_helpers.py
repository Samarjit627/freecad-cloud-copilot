"""
DFM Helper Utilities
Contains utility functions to support the DFM engine and analysis process
"""

import logging
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def calculate_manufacturability_score(issues: List[Dict[str, Any]]) -> int:
    """
    Calculate a manufacturability score based on the number and severity of issues
    
    Args:
        issues: List of manufacturing issues
        
    Returns:
        int: Score from 0-100, where 100 is perfect manufacturability
    """
    if not issues:
        return 100
        
    # Start with perfect score and deduct based on issues
    score = 100
    
    for issue in issues:
        severity = issue.get("severity", "medium").lower()
        
        # Deduct points based on severity
        if severity == "critical":
            score -= 25
        elif severity == "high":
            score -= 15
        elif severity == "medium":
            score -= 10
        elif severity == "low":
            score -= 5
            
    # Ensure score doesn't go below 0
    return max(0, score)

def format_cost_estimate(base_cost: float, complexity_factor: float) -> Dict[str, float]:
    """
    Format cost estimate with min/max range
    
    Args:
        base_cost: Base manufacturing cost
        complexity_factor: Factor to adjust cost based on complexity
        
    Returns:
        Dict with min and max cost estimates
    """
    min_cost = round(base_cost * (1 - 0.1 * complexity_factor), 2)
    max_cost = round(base_cost * (1 + 0.2 * complexity_factor), 2)
    
    return {
        "min": min_cost,
        "max": max_cost
    }

def measure_execution_time(func):
    """
    Decorator to measure execution time of a function
    
    Args:
        func: Function to measure
        
    Returns:
        Wrapped function that logs execution time
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger.info(f"Function {func.__name__} executed in {end_time - start_time:.4f} seconds")
        return result
    
    return wrapper
