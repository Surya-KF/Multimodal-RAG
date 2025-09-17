from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        """Log request and response details"""
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        # Log request details
        request_info = {
            "timestamp": timestamp,
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        
        # Get request body size if available
        if hasattr(request, 'body'):
            try:
                body = await request.body()
                request_info["body_size"] = len(body)
            except:
                request_info["body_size"] = 0
        
        logger.info(f"Request: {json.dumps(request_info)}")
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response details
            response_info = {
                "timestamp": datetime.now().isoformat(),
                "status_code": response.status_code,
                "process_time_seconds": round(process_time, 4),
                "response_headers": dict(response.headers)
            }
            
            logger.info(f"Response: {json.dumps(response_info)}")
            
            # Add processing time to response headers
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log errors
            process_time = time.time() - start_time
            error_info = {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "process_time_seconds": round(process_time, 4)
            }
            
            logger.error(f"Request error: {json.dumps(error_info)}")
            raise
