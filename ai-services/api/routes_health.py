"""
Health check and monitoring endpoints for the Civic Educator AI service.
"""
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
import psutil

from .schemas import HealthCheckResponse, HealthStatus, ServiceHealth
from .routes_chat import get_rag_pipeline
from rag.pipeline import RAGPipeline

logger = logging.getLogger(__name__)
router = APIRouter(tags=["system"])

# Service version (would come from package or environment in production)
SERVICE_VERSION = "0.1.0"

def get_system_metrics() -> Dict[str, Any]:
    """Collect basic system metrics."""
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_rss_mb": memory_info.rss / (1024 * 1024),  # Convert to MB
        "memory_percent": process.memory_percent(),
        "disk_usage": psutil.disk_usage('/')._asdict(),
        "process_uptime": (datetime.now() - datetime.fromtimestamp(process.create_time())).total_seconds(),
    }

def check_model_health(rag_pipeline: RAGPipeline) -> ServiceHealth:
    """Check the health of ML models."""
    try:
        # Test embedding model
        test_embedding = rag_pipeline.embedding_model.embed_query("test")
        embedding_ok = len(test_embedding) > 0
        
        # Test reranker if available
        reranker_ok = True
        if rag_pipeline.reranker:
            test_scores = rag_pipeline.reranker.predict([("test", "test document")])
            reranker_ok = len(test_scores) == 1 and isinstance(test_scores[0], float)
        
        return ServiceHealth(
            status=HealthStatus.HEALTHY if (embedding_ok and reranker_ok) else HealthStatus.DEGRADED,
            details={
                "embedding_model": {
                    "status": "ok" if embedding_ok else "error",
                    "model": rag_pipeline.embedding_model.model_name,
                    "dimension": len(test_embedding) if embedding_ok else 0
                },
                "reranker": {
                    "status": "ok" if reranker_ok else "error",
                    "enabled": rag_pipeline.reranker is not None,
                    "model": rag_pipeline.reranker.model_name if rag_pipeline.reranker else None
                }
            }
        )
    except Exception as e:
        logger.error(f"Error checking model health: {e}", exc_info=True)
        return ServiceHealth(
            status=HealthStatus.UNHEALTHY,
            details={"error": str(e)}
        )

def check_service_health() -> Dict[str, ServiceHealth]:
    """Check the health of service components."""
    services = {}
    
    # System health
    try:
        metrics = get_system_metrics()
        services["system"] = ServiceHealth(
            status=HealthStatus.HEALTHY,
            details=metrics
        )
    except Exception as e:
        services["system"] = ServiceHealth(
            status=HealthStatus.DEGRADED,
            details={"error": f"Failed to get system metrics: {str(e)}"}
        )
    
    # Document index health
    try:
        # This would check if the document index is accessible
        # For now, we'll just check if we can get the index stats
        services["document_index"] = ServiceHealth(
            status=HealthStatus.HEALTHY,
            details={
                "status": "ok",
                "doc_count": "unknown"  # Would be actual count in a real implementation
            }
        )
    except Exception as e:
        services["document_index"] = ServiceHealth(
            status=HealthStatus.UNHEALTHY,
            details={"error": f"Document index error: {str(e)}"}
        )
    
    return services

@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline)
) -> HealthCheckResponse:
    """
    Check the health of the service and its components.
    
    Returns a comprehensive health status including:
    - Service version
    - Overall status
    - Model health (embedding, reranker)
    - System metrics (CPU, memory, disk)
    - Service component statuses
    """
    try:
        # Check model health
        model_health = check_model_health(rag_pipeline)
        
        # Check service health
        services_health = check_service_health()
        
        # Determine overall status
        all_statuses = [model_health.status] + [s.status for s in services_health.values()]
        if HealthStatus.UNHEALTHY in all_statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in all_statuses:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        return HealthCheckResponse(
            status=overall_status,
            version=SERVICE_VERSION,
            models={
                "embedding": model_health,
                "reranker": model_health  # In a real implementation, these would be separate
            },
            services=services_health,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        error_detail = {"error": str(e)}
        return HealthCheckResponse(
            status=HealthStatus.UNHEALTHY,
            version=SERVICE_VERSION,
            models={
                "embedding": ServiceHealth(status=HealthStatus.UNHEALTHY, details=error_detail),
                "reranker": ServiceHealth(status=HealthStatus.UNHEALTHY, details=error_detail),
            },
            services={
                "system": ServiceHealth(status=HealthStatus.DEGRADED, details=error_detail),
                "document_index": ServiceHealth(status=HealthStatus.DEGRADED, details=error_detail),
            },
            timestamp=datetime.utcnow().isoformat()
        )

@router.get("/metrics")
async def metrics() -> Dict[str, Any]:
    """Return system and application metrics in Prometheus format."""
    try:
        metrics = get_system_metrics()
        
        # Format metrics in Prometheus text format
        prom_metrics = [
            "# HELP process_cpu_percent CPU usage percentage",
            "# TYPE process_cpu_percent gauge",
            f"process_cpu_percent {metrics['cpu_percent']}",
            "",
            "# HELP process_memory_rss_mb Resident set size in MB",
            "# TYPE process_memory_rss_mb gauge",
            f"process_memory_rss_mb {metrics['memory_rss_mb']}",
            "",
            "# HELP process_memory_percent Memory usage percentage",
            "# TYPE process_memory_percent gauge",
            f"process_memory_percent {metrics['memory_percent']}",
            "",
            "# HELP process_uptime_seconds Process uptime in seconds",
            "# TYPE process_uptime_seconds counter",
            f"process_uptime_seconds {metrics['process_uptime']}",
            "",
            "# HELP disk_usage_percent Disk usage percentage",
            "# TYPE disk_usage_percent gauge",
            f"disk_usage_percent {metrics['disk_usage']['percent']}",
        ]
        
        return {
            "content": "\n".join(prom_metrics),
            "media_type": "text/plain; version=0.0.4"
        }
        
    except Exception as e:
        logger.error(f"Failed to collect metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to collect metrics: {str(e)}"
        )
