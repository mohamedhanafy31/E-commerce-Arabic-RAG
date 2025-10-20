"""
Comprehensive error handling middleware for RAG System
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

from core.logging import get_logger, log_error, log_performance

logger = get_logger("middleware")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware for RAG System"""
    
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
        
        except FileNotFoundError as e:
            log_error(logger, e, "file_not_found", 
                     request_id=request_id,
                     method=request.method,
                     path=request.url.path)
            return JSONResponse(
                status_code=404,
                content={
                    "error": "File Not Found",
                    "detail": "The requested file or resource was not found",
                    "type": "file_not_found",
                    "request_id": request_id,
                    "solutions": [
                        "Check if the file exists",
                        "Verify the file path",
                        "Ensure proper file permissions"
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
        
        except MemoryError as e:
            log_error(logger, e, "memory_error", 
                     request_id=request_id,
                     method=request.method,
                     path=request.url.path)
            return JSONResponse(
                status_code=507,
                content={
                    "error": "Insufficient Storage",
                    "detail": "Not enough memory to process the request",
                    "type": "memory_error",
                    "request_id": request_id,
                    "solutions": [
                        "Try with a smaller file",
                        "Reduce chunk size",
                        "Restart the service"
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
                    "detail": "An unexpected error occurred in the RAG system",
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
