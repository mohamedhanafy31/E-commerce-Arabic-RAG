"""
Comprehensive error handling middleware for Orchestrator
Handles all types of errors with detailed logging and structured responses
"""

import logging
import traceback
import time
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.responses import Response

from app.core.logging import get_logger, log_error, log_performance

logger = get_logger("middleware")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware for Orchestrator"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = getattr(request.state, "request_id", None)
        
        try:
            response = await call_next(request)
            
            # Log successful requests
            duration_ms = (time.time() - start_time) * 1000
            log_performance(logger, "request_completed", duration_ms,
                          request_id=request_id,
                          method=request.method,
                          path=request.url.path,
                          status_code=response.status_code)
            
            return response
        
        except HTTPException as e:
            # Re-raise HTTP exceptions as they are already properly formatted
            duration_ms = (time.time() - start_time) * 1000
            log_error(logger, e, "http_exception", 
                     request_id=request_id,
                     method=request.method,
                     path=request.url.path,
                     status_code=e.status_code)
            raise e
        
        except ConnectionError as e:
            log_error(logger, e, "connection_error", 
                     request_id=request_id,
                     method=request.method,
                     path=request.url.path)
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Service Unavailable",
                    "detail": "Unable to connect to external services",
                    "type": "connection_error",
                    "request_id": request_id,
                    "solutions": [
                        "Check if ASR, RAG, and TTS services are running",
                        "Verify service URLs in configuration",
                        "Check network connectivity"
                    ]
                }
            )
        
        except TimeoutError as e:
            log_error(logger, e, "timeout_error", 
                     request_id=request_id,
                     method=request.method,
                     path=request.url.path)
            return JSONResponse(
                status_code=504,
                content={
                    "error": "Gateway Timeout",
                    "detail": "Request timed out while waiting for external services",
                    "type": "timeout_error",
                    "request_id": request_id,
                    "solutions": [
                        "Retry the request",
                        "Check external service performance",
                        "Increase timeout settings if needed"
                    ]
                }
            )
        
        except ValueError as e:
            log_error(logger, e, "validation_error", 
                     request_id=request_id,
                     method=request.method,
                     path=request.url.path)
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Validation Error",
                    "detail": str(e),
                    "type": "validation_error",
                    "request_id": request_id,
                    "solutions": [
                        "Check request parameters",
                        "Verify data format and types",
                        "Ensure required fields are provided"
                    ]
                }
            )
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_error(logger, e, "unexpected_error", 
                     request_id=request_id,
                     method=request.method,
                     path=request.url.path,
                     duration_ms=duration_ms)
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "detail": "An unexpected error occurred in the orchestrator",
                    "type": "internal_error",
                    "request_id": request_id,
                    "solutions": [
                        "Check server logs for detailed error information",
                        "Retry the request",
                        "Contact support if the issue persists"
                    ]
                }
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all requests"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Generate request ID
        import uuid
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request start
        logger.info(f"Request started: {request.method} {request.url.path}", extra={
            'operation': 'request_started',
            'request_id': request_id,
            'method': request.method,
            'path': request.url.path,
            'client_ip': request.client.host if request.client else "unknown",
            'user_agent': request.headers.get("user-agent", "unknown")
        })
        
        response = await call_next(request)
        
        # Log request completion
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Request completed: {request.method} {request.url.path} - {response.status_code}", extra={
            'operation': 'request_completed',
            'request_id': request_id,
            'method': request.method,
            'path': request.url.path,
            'status_code': response.status_code,
            'duration_ms': duration_ms
        })
        
        return response
