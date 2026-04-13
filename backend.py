"""
FastAPI backend for the multi-modal agent.

Provides REST endpoints for text and image processing through the unified
LangGraph workflow. Supports text, image generation, stance detection,
and image analysis tasks.
"""

import io
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, ConfigDict
import uvicorn

from config import Config, get_config
from graph.workflow import build_workflow, run_workflow
from graph.state import AgentStatePydantic, TaskType


# ============================================================================
# Logging Configuration
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================

def normalize_task_type(task_type: Any) -> str:
    """Safely normalize task_type to string, handling both Enum and string cases.
    
    Args:
        task_type: TaskType enum, string, or None
        
    Returns:
        String representation of task type, or "unknown" if None
        
    Examples:
        normalize_task_type(TaskType.SUMMARIZATION)  # "summary"
        normalize_task_type("summary")                 # "summary"
        normalize_task_type(None)                      # "unknown"
    """
    # Log the type for debugging
    logger.debug("normalize_task_type: input type=%s, value=%s", 
                type(task_type).__name__, task_type)
    
    # Handle None
    if task_type is None:
        logger.warning("normalize_task_type: task_type is None, using default 'unknown'")
        return "unknown"
    
    # Handle TaskType Enum (has .value attribute)
    if hasattr(task_type, 'value'):
        normalized = task_type.value
        logger.debug("normalize_task_type: Extracted enum value: %s", normalized)
        return normalized
    
    # Handle plain string
    if isinstance(task_type, str):
        logger.debug("normalize_task_type: Already string: %s", task_type)
        return task_type
    
    # Fallback: convert to string
    logger.warning("normalize_task_type: Unexpected type, converting to string: %s", task_type)
    return str(task_type)


# ============================================================================
# Pydantic Models
# ============================================================================

class ProcessRequest(BaseModel):
    """Request model for /process endpoint."""
    
    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Input text for processing"
    )
    image: Optional[bytes] = Field(
        None,
        description="Optional image bytes for image analysis"
    )
    verbose: bool = Field(
        False,
        description="Enable verbose logging of execution steps"
    )
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        """Validate text input."""
        if not v or not v.strip():
            raise ValueError("Text cannot be empty or whitespace-only")
        return v.strip()
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Summarize this article about AI...",
                "image": None,
                "verbose": False
            }
        }
    )


class ProcessResponse(BaseModel):
    """Response model for /process endpoint."""
    
    success: bool = Field(description="Whether processing was successful")
    task_type: str = Field(description="Detected task type")
    result: Optional[Dict[str, Any]] = Field(
        None,
        description="Task-specific result"
    )
    error: Optional[str] = Field(None, description="Error message if failed")
    messages: list = Field(
        default_factory=list,
        description="Execution trace messages"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "task_type": "summary",
                "result": {
                    "type": "summary",
                    "content": "This article discusses...",
                    "status": "success"
                },
                "error": None,
                "messages": ["🚀 Workflow: Starting execution", "📍 Router: Routing to summary"],
                "metadata": {}
            }
        }
    )


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str = Field(description="Health status")
    version: str = Field(description="API version")
    message: str = Field(description="Status message")


# ============================================================================
# FastAPI Application Setup
# ============================================================================

def create_app(config: Optional[Config] = None) -> FastAPI:
    """Create and configure the FastAPI application.
    
    Args:
        config: Optional config object (uses default Config if None)
        
    Returns:
        Configured FastAPI application
    """
    if config is None:
        config = get_config()
    
    # ========================================================================
    # Lifespan Management
    # ========================================================================
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manage application lifespan (startup/shutdown)."""
        logger.info("Starting Multi-Modal Agent API")
        
        try:
            workflow_config = {
                "hf_api_key": config.hf_api_key,
                "timeout": getattr(config, 'timeout', 30),
                "max_retries": getattr(config, 'max_retries', 3),
                "model_loading_timeout": getattr(config, 'model_loading_timeout', 120)
            }
            
            logger.info("Building LangGraph workflow...")
            workflow_cache["compiled_graph"] = build_workflow(workflow_config)
            workflow_cache["initialized"] = True
            
            logger.info("✓ Workflow initialized successfully")
            
            yield
            
        except Exception as e:
            logger.error("Failed to initialize workflow: %s", e)
            raise
        finally:
            logger.info("Shutting down Multi-Modal Agent API")
            workflow_cache["compiled_graph"] = None
    
    app = FastAPI(
        title="Multi-Modal Agent API",
        description="REST API for text and image processing using unified LangGraph workflow",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Consider restricting in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Global workflow state
    workflow_cache = {
        "compiled_graph": None,
        "config": config,
        "initialized": False
    }
    
    # ========================================================================
    # Health Check Endpoint
    # ========================================================================
    
    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["Health"],
        summary="Health Check"
    )
    async def health_check():
        """Check API health and workflow status."""
        logger.debug("Health check requested")
        
        return {
            "status": "healthy" if workflow_cache["initialized"] else "uninitialized",
            "version": "1.0.0",
            "message": "Ready to process requests" if workflow_cache["initialized"] else "Workflow not yet initialized"
        }
    
    # ========================================================================
    # Main Processing Endpoint
    # ========================================================================
    
    @app.post(
        "/process",
        response_model=ProcessResponse,
        tags=["Processing"],
        summary="Process text/image through multi-modal agent",
        responses={
            200: {"description": "Processing successful"},
            400: {"description": "Invalid input"},
            500: {"description": "Server error"},
            503: {"description": "Service unavailable"}
        }
    )
    async def process(
        text: str = Form(..., min_length=1, max_length=10000),
        image: Optional[UploadFile] = File(None),
        verbose: bool = Form(False)
    ):
        """Process text and optional image through the multi-modal workflow.
        
        **Parameters:**
        - **text**: Input text for processing (required)
        - **image**: Optional image file for image analysis
        - **verbose**: Enable verbose logging (default: false)
        
        **Returns:**
        - **ProcessResponse**: Contains task type, result, error status, and execution messages
        """
        logger.info("Processing request: text=%s, image=%s, verbose=%s",
                   text[:50] + "..." if len(text) > 50 else text,
                   "yes" if image else "no",
                   verbose)
        
        try:
            # Check initialization
            if not workflow_cache["initialized"]:
                logger.error("Workflow not initialized")
                raise HTTPException(
                    status_code=503,
                    detail="Workflow not initialized. Please try again."
                )
            
            # Validate and read image if provided
            image_bytes = None
            if image:
                logger.debug("Reading image file: %s", image.filename)
                image_bytes = await image.read()
                
                if not image_bytes:
                    raise HTTPException(
                        status_code=400,
                        detail="Image file is empty"
                    )
                
                if len(image_bytes) > 50 * 1024 * 1024:  # 50MB limit
                    raise HTTPException(
                        status_code=400,
                        detail="Image file too large (max 50MB)"
                    )
                
                logger.info("Image loaded: %d bytes", len(image_bytes))
            
            # Execute workflow
            logger.debug("Invoking workflow...")
            final_state = run_workflow(
                workflow_cache["compiled_graph"],
                user_input=text,
                image=image_bytes,
                verbose=verbose
            )
            
            # Check for errors
            if final_state.is_error():
                logger.warning("Workflow completed with error: %s", final_state.error)
                return ProcessResponse(
                    success=False,
                    task_type=normalize_task_type(final_state.task_type),
                    error=final_state.error,
                    messages=final_state.messages,
                    metadata={
                        "execution_failed": True,
                        "error_type": type(final_state.error).__name__ if final_state.error else "unknown"
                    }
                )
            
            # Successful processing
            logger.info("Workflow completed successfully: task=%s", final_state.task_type)
            
            return ProcessResponse(
                success=True,
                task_type=normalize_task_type(final_state.task_type),
                result=final_state.result,
                messages=final_state.messages,
                metadata={
                    "task_type_enum": str(final_state.task_type),
                    "has_image": image_bytes is not None,
                    "result_type": final_state.result.get("type") if final_state.result else None
                }
            )
        
        except HTTPException:
            raise
        
        except Exception as e:
            logger.error("Unexpected error during processing: %s", e, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Processing failed: {str(e)}"
            )
    
    # ========================================================================
    # Image Download Endpoint
    # ========================================================================
    
    @app.post(
        "/process-and-download",
        tags=["Processing"],
        summary="Process and download image (for image generation)",
        responses={
            200: {"description": "Image generated and downloaded"},
            400: {"description": "Invalid input"},
            500: {"description": "Server error"},
            503: {"description": "Service unavailable"}
        }
    )
    async def process_and_download(
        text: str = Form(..., min_length=1, max_length=10000),
        verbose: bool = Form(False)
    ):
        """Process text and download image for image generation tasks.
        
        Returns binary image data if task generates an image, otherwise returns JSON.
        
        **Parameters:**
        - **text**: Image generation prompt (required)
        - **verbose**: Enable verbose logging (default: false)
        """
        logger.info("Processing image generation request: %s", text[:50] + "..." if len(text) > 50 else text)
        
        try:
            if not workflow_cache["initialized"]:
                raise HTTPException(
                    status_code=503,
                    detail="Workflow not initialized"
                )
            
            # Execute workflow
            final_state = run_workflow(
                workflow_cache["compiled_graph"],
                user_input=text,
                image=None,
                verbose=verbose
            )
            
            # Check if image was generated
            # Handle both Enum and string task_type
            task_type_str = normalize_task_type(final_state.task_type)
            logger.debug("Task type after normalization: %s", task_type_str)
            
            if task_type_str == TaskType.IMAGE_GENERATION.value and final_state.result:
                image_url = final_state.result.get("image_url")
                if not image_url:
                    content = final_state.result.get("content")
                    if isinstance(content, str) and content.startswith("http"):
                        image_url = content

                if isinstance(image_url, str) and image_url.startswith("http"):
                    logger.info("Returning generated image URL: %s", image_url)
                    return ProcessResponse(
                        success=True,
                        task_type=task_type_str,
                        result={"image_url": image_url},
                        messages=final_state.messages
                    )
            
            # Not an image, return as JSON
            logger.info("Returning non-image result as JSON")
            return ProcessResponse(
                success=not final_state.is_error(),
                task_type=normalize_task_type(final_state.task_type),
                result=final_state.result,
                error=final_state.error,
                messages=final_state.messages
            )
        
        except HTTPException:
            raise
        
        except Exception as e:
            logger.error("Error in image generation: %s", e, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Processing failed: {str(e)}"
            )
    
    # ========================================================================
    # Batch Processing Endpoint
    # ========================================================================
    
    @app.post(
        "/process-batch",
        tags=["Processing"],
        summary="Process multiple texts in batch",
        responses={
            200: {"description": "Batch processing completed"},
            400: {"description": "Invalid input"},
            500: {"description": "Server error"}
        }
    )
    async def process_batch(texts: list[str] = Form(...)):
        """Process multiple texts in sequence through the workflow.
        
        **Parameters:**
        - **texts**: List of text strings to process
        
        **Returns:**
        - List of ProcessResponse objects
        """
        logger.info("Batch processing %d texts", len(texts))
        
        if not texts:
            raise HTTPException(status_code=400, detail="No texts provided")
        
        if len(texts) > 100:
            raise HTTPException(status_code=400, detail="Batch size limited to 100 items")
        
        try:
            if not workflow_cache["initialized"]:
                raise HTTPException(status_code=503, detail="Workflow not initialized")
            
            results = []
            
            for i, text in enumerate(texts, 1):
                try:
                    logger.debug("Processing batch item %d/%d", i, len(texts))
                    
                    final_state = run_workflow(
                        workflow_cache["compiled_graph"],
                        user_input=text,
                        image=None,
                        verbose=False
                    )
                    
                    results.append({
                        "index": i - 1,
                        "success": not final_state.is_error(),
                        "task_type": normalize_task_type(final_state.task_type),
                        "result": final_state.result,
                        "error": final_state.error
                    })
                
                except Exception as e:
                    logger.error("Error processing batch item %d: %s", i, e)
                    results.append({
                        "index": i - 1,
                        "success": False,
                        "error": str(e)
                    })
            
            logger.info("Batch processing completed: %d/%d successful",
                       sum(1 for r in results if r["success"]),
                       len(texts))
            
            return {
                "total": len(texts),
                "successful": sum(1 for r in results if r["success"]),
                "results": results
            }
        
        except HTTPException:
            raise
        
        except Exception as e:
            logger.error("Batch processing error: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")
    
    # ========================================================================
    # Root Endpoint
    # ========================================================================
    
    @app.get("/", tags=["Info"], summary="API Information")
    async def root():
        """Get API information and available endpoints."""
        return {
            "name": "Multi-Modal Agent API",
            "version": "1.0.0",
            "description": "REST API for text and image processing",
            "endpoints": {
                "health": "/health (GET)",
                "process": "/process (POST) - Main processing endpoint",
                "process_and_download": "/process-and-download (POST) - For image generation downloads",
                "process_batch": "/process-batch (POST) - Batch processing",
                "docs": "/docs (Swagger UI)",
                "redoc": "/redoc (ReDoc documentation)"
            }
        }
    
    # Mount output directory for serving generated images
    _project_root = Path(__file__).resolve().parent
    _output_dir = _project_root / "outputs" / "images"
    _output_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/outputs", StaticFiles(directory=str(_output_dir)), name="outputs")
    logger.info("Mounted generated images directory: %s", _output_dir)
    
    return app


# ============================================================================
# Application Instance
# ============================================================================

# Create application instance with default config
config = get_config()
app = create_app(config)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    """Run the FastAPI application."""
    runtime_config = get_config()
    host = runtime_config.api_host
    port = runtime_config.api_port
    reload = runtime_config.api_reload
    
    logger.info("Starting FastAPI server on %s:%d", host, port)
    
    uvicorn.run(
        "backend:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        timeout_keep_alive=120  # Increased from default 5 to 120 for long-running requests
    )
