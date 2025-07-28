from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import os
import logging
import asyncio
import uuid
import json
import aiohttp
import time
from contextlib import asynccontextmanager
from collections import defaultdict, deque
import traceback
from desktop_integration import desktop_integration

# Environment setup
ROOT_DIR = Path(__file__).parent
from dotenv import load_dotenv
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
security = HTTPBearer(auto_error=False)

# Global variables for app state
active_connections: List[WebSocket] = []
job_queue = asyncio.Queue()
rate_limiters = defaultdict(lambda: deque())
batch_processes = {}

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Models
class AIProvider(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    enabled: bool = True
    api_key: Optional[str] = None
    rate_limit_per_minute: int = 10
    selectors: Dict[str, str] = {}
    timeout_seconds: int = 30
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PromptTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    template: str
    category: str
    variables: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ImageGenerationJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str
    provider: str
    status: str = "queued"  # queued, processing, completed, failed, cancelled
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    priority: int = 1  # 1=low, 5=high
    metadata: Dict[str, Any] = {}

class BatchJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    prompts: List[str]
    providers: List[str]
    status: str = "queued"
    progress: Dict[str, int] = {"completed": 0, "total": 0, "failed": 0}
    jobs: List[str] = []  # Job IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    settings: Dict[str, Any] = {}

class AppConfig(BaseModel):
    gemini_api_key: str
    openai_api_key: str
    gemini_or_api_key: str
    auto_retry_enabled: bool = True
    max_retry_attempts: int = 3
    default_timeout: int = 30
    concurrent_jobs: int = 3
    enable_logging: bool = True
    dark_mode: bool = True
    notifications_enabled: bool = True

class SelectorUpdate(BaseModel):
    provider: str
    selectors: Dict[str, str]

class SystemHealth(BaseModel):
    status: str
    uptime_seconds: int
    active_jobs: int
    queued_jobs: int
    completed_jobs_today: int
    error_rate: float
    memory_usage_mb: float
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# Rate Limiting Function
async def check_rate_limit(provider: str, limit_per_minute: int = 10) -> bool:
    now = time.time()
    minute_ago = now - 60
    
    # Clean old entries
    while rate_limiters[provider] and rate_limiters[provider][0] < minute_ago:
        rate_limiters[provider].popleft()
    
    # Check if under limit
    if len(rate_limiters[provider]) < limit_per_minute:
        rate_limiters[provider].append(now)
        return True
    return False

# WebSocket connection manager
async def broadcast_to_clients(message: Dict[str, Any]):
    if active_connections:
        dead_connections = []
        for connection in active_connections:
            try:
                await connection.send_text(json.dumps(message, default=str))
            except:
                dead_connections.append(connection)
        
        # Remove dead connections
        for dead_conn in dead_connections:
            if dead_conn in active_connections:
                active_connections.remove(dead_conn)

# AI Integration Functions
async def generate_prompts_openai(theme: str, count: int = 5, api_key: str = None) -> List[str]:
    """Generate creative prompts using OpenAI"""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        system_prompt = f"""Generate {count} creative and detailed image generation prompts based on the theme: '{theme}'. 
        Each prompt should be specific, vivid, and optimized for AI image generation. Include artistic style, mood, lighting, and composition details.
        Return only the prompts, one per line, without numbering."""
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate {count} prompts for: {theme}"}
            ],
            "max_tokens": 1000,
            "temperature": 0.8
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.openai.com/v1/chat/completions", 
                                  json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    prompts = [line.strip() for line in content.split('\n') if line.strip()]
                    return prompts[:count]
                else:
                    error_text = await response.text()
                    logger.error(f"OpenAI API Error: {response.status} - {error_text}")
                    return []
    except Exception as e:
        logger.error(f"Error generating prompts with OpenAI: {str(e)}")
        return []

async def generate_prompts_gemini(theme: str, count: int = 5, api_key: str = None) -> List[str]:
    """Generate creative prompts using Gemini"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        
        prompt = f"""Generate {count} creative and detailed image generation prompts based on the theme: '{theme}'. 
        Each prompt should be specific, vivid, and optimized for AI image generation. Include artistic style, mood, lighting, and composition details.
        Return only the prompts, one per line, without numbering or extra text."""
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.8,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024
            }
        }
        
        headers = {"Content-Type": "application/json"}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data['candidates'][0]['content']['parts'][0]['text']
                    prompts = [line.strip() for line in content.split('\n') if line.strip()]
                    return prompts[:count]
                else:
                    error_text = await response.text()
                    logger.error(f"Gemini API Error: {response.status} - {error_text}")
                    return []
    except Exception as e:
        logger.error(f"Error generating prompts with Gemini: {str(e)}")
        return []

# Job Processing Functions
async def process_job_queue():
    """Background task to process job queue"""
    logger.info("Job queue processor started")
    
    while True:
        try:
            # Get job from queue with timeout
            try:
                job = await asyncio.wait_for(job_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
                
            logger.info(f"Processing job: {job.id}")
            
            # Update job status
            await db.jobs.update_one(
                {"id": job.id}, 
                {"$set": {"status": "processing", "updated_at": datetime.utcnow()}}
            )
            
            # Broadcast status update
            await broadcast_to_clients({
                "type": "job_status_update",
                "job_id": job.id,
                "status": "processing"
            })
            
            # Process the job
            success = await process_single_job(job)
            
            if success:
                await db.jobs.update_one(
                    {"id": job.id}, 
                    {"$set": {
                        "status": "completed",
                        "completed_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }}
                )
                status = "completed"
            else:
                # Handle retry logic
                if job.retry_count < 3:  # Max 3 retries
                    job.retry_count += 1
                    await db.jobs.update_one(
                        {"id": job.id}, 
                        {"$set": {
                            "status": "queued",
                            "retry_count": job.retry_count,
                            "updated_at": datetime.utcnow()
                        }}
                    )
                    await job_queue.put(job)  # Re-queue for retry
                    status = "queued_retry"
                    logger.info(f"Job {job.id} queued for retry ({job.retry_count}/3)")
                else:
                    await db.jobs.update_one(
                        {"id": job.id}, 
                        {"$set": {
                            "status": "failed",
                            "completed_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }}
                    )
                    status = "failed"
                    logger.error(f"Job {job.id} failed after max retries")
            
            # Broadcast final status
            await broadcast_to_clients({
                "type": "job_status_update",
                "job_id": job.id,
                "status": status
            })
            
        except Exception as e:
            logger.error(f"Error in job queue processor: {str(e)}\n{traceback.format_exc()}")
            await asyncio.sleep(1)

async def process_single_job(job: ImageGenerationJob) -> bool:
    """Process a single image generation job"""
    try:
        # Get provider config
        provider_doc = await db.providers.find_one({"name": job.provider})
        if not provider_doc:
            logger.error(f"Provider {job.provider} not found")
            return False
            
        # Check rate limit
        rate_limit = provider_doc.get("rate_limit_per_minute", 10)
        if not await check_rate_limit(job.provider, rate_limit):
            logger.warning(f"Rate limit exceeded for {job.provider}")
            await asyncio.sleep(60)  # Wait before retry
            return False
            
        # Simulate job processing (replace with actual automation logic)
        await asyncio.sleep(2)  # Simulate processing time
        
        # Store result
        result = {
            "images": [f"https://example.com/generated_image_{job.id}.jpg"],
            "processing_time": 2.0,
            "provider_response": "Success"
        }
        
        await db.jobs.update_one(
            {"id": job.id}, 
            {"$set": {"result": result, "updated_at": datetime.utcnow()}}
        )
        
        return True
        
    except Exception as e:
        error_msg = f"Error processing job {job.id}: {str(e)}"
        logger.error(error_msg)
        
        await db.jobs.update_one(
            {"id": job.id}, 
            {"$set": {"error": error_msg, "updated_at": datetime.utcnow()}}
        )
        
        return False

# Application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AI Image Generator Manager")
    
    # Initialize default providers
    await init_default_providers()
    await init_default_config()
    
    # Start background tasks
    queue_task = asyncio.create_task(process_job_queue())
    
    yield
    
    # Shutdown
    queue_task.cancel()
    client.close()
    logger.info("Application shutdown complete")

async def init_default_providers():
    """Initialize default AI providers"""
    default_providers = [
        {
            "name": "OpenAI DALL-E",
            "enabled": True,
            "rate_limit_per_minute": 50,
            "selectors": {
                "prompt_input": "textarea[placeholder*='prompt']",
                "generate_button": "button[data-testid='generate']",
                "result_images": "img[alt*='generated']"
            },
            "timeout_seconds": 60
        },
        {
            "name": "Midjourney",
            "enabled": False,
            "rate_limit_per_minute": 20,
            "selectors": {
                "prompt_input": "div[data-slate-editor='true']",
                "generate_button": "button[aria-label='Send Message']",
                "result_images": "img[class*='imageWrapper']"
            },
            "timeout_seconds": 120
        },
        {
            "name": "ImageFX",
            "enabled": True,
            "rate_limit_per_minute": 30,
            "selectors": {
                "prompt_input": "div[data-slate-editor='true'][contenteditable='true']",
                "generate_button": "button:has-text('criar')",
                "result_images": "img[src*='lh3.googleusercontent.com']"
            },
            "timeout_seconds": 90
        }
    ]
    
    for provider_data in default_providers:
        existing = await db.providers.find_one({"name": provider_data["name"]})
        if not existing:
            provider_data["id"] = str(uuid.uuid4())
            provider_data["created_at"] = datetime.utcnow()
            provider_data["updated_at"] = datetime.utcnow()
            await db.providers.insert_one(provider_data)
            logger.info(f"Initialized provider: {provider_data['name']}")

async def init_default_config():
    """Initialize default app configuration"""
    existing_config = await db.config.find_one({})
    if not existing_config:
        default_config = {
            "id": str(uuid.uuid4()),
            "gemini_api_key": "AIzaSyDgmnAwq1zuyFOY0sNQl4z7MgbavgHdo2M",
            "openai_api_key": "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",
            "gemini_or_api_key": "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",
            "auto_retry_enabled": True,
            "max_retry_attempts": 3,
            "default_timeout": 30,
            "concurrent_jobs": 3,
            "enable_logging": True,
            "dark_mode": True,
            "notifications_enabled": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await db.config.insert_one(default_config)
        logger.info("Initialized default configuration")

# Create FastAPI app
app = FastAPI(
    title="AI Image Generator Manager",
    description="Advanced desktop application for managing AI image generation across multiple platforms",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
@app.get("/api/")
async def root():
    return {"message": "AI Image Generator Manager - Desktop App v2.0", "status": "running"}

@app.get("/api/desktop/system-info")
async def get_desktop_system_info():
    """Get comprehensive system information for desktop app"""
    system_info = await desktop_integration.get_system_info()
    return system_info

@app.get("/api/desktop/config")
async def get_desktop_config():
    """Get desktop-specific configuration"""
    config = await desktop_integration.load_desktop_config()
    return config

@app.put("/api/desktop/config")
async def update_desktop_config(config: dict):
    """Update desktop-specific configuration"""
    success = await desktop_integration.save_desktop_config(config)
    if success:
        return {"message": "Desktop configuration updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update desktop configuration")

@app.post("/api/desktop/auto-start")
async def setup_auto_start(enable: bool = True):
    """Setup application auto-start"""
    success = await desktop_integration.setup_auto_start(enable)
    if success:
        return {"message": f"Auto-start {'enabled' if enable else 'disabled'} successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to setup auto-start")

@app.post("/api/desktop/shortcut")
async def create_desktop_shortcut():
    """Create desktop shortcut"""
    success = await desktop_integration.create_desktop_shortcut()
    if success:
        return {"message": "Desktop shortcut created successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to create desktop shortcut")

@app.get("/api/desktop/logs")
async def get_app_logs(lines: int = 100):
    """Get recent application logs"""
    logs = await desktop_integration.get_app_logs(lines)
    return {"logs": logs}

@app.delete("/api/desktop/cache")
async def clear_app_cache():
    """Clear application cache"""
    success = await desktop_integration.clear_cache()
    if success:
        return {"message": "Cache cleared successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@app.post("/api/desktop/export")
async def export_app_data(export_path: str, include_logs: bool = False):
    """Export application data"""
    success = await desktop_integration.export_data(export_path, include_logs)
    if success:
        return {"message": f"Data exported to {export_path}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to export data")

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)

@app.get("/api/health", response_model=SystemHealth)
async def get_system_health():
    active_jobs = await db.jobs.count_documents({"status": "processing"})
    queued_jobs = await db.jobs.count_documents({"status": "queued"})
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    completed_today = await db.jobs.count_documents({
        "status": "completed",
        "completed_at": {"$gte": today}
    })
    
    total_jobs = await db.jobs.count_documents({})
    failed_jobs = await db.jobs.count_documents({"status": "failed"})
    error_rate = (failed_jobs / total_jobs * 100) if total_jobs > 0 else 0
    
    return SystemHealth(
        status="healthy",
        uptime_seconds=3600,  # Placeholder
        active_jobs=active_jobs,
        queued_jobs=queued_jobs,
        completed_jobs_today=completed_today,
        error_rate=error_rate,
        memory_usage_mb=128.5  # Placeholder
    )

@app.get("/api/config", response_model=AppConfig)
async def get_config():
    config = await db.config.find_one({})
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return AppConfig(**config)

@app.put("/api/config", response_model=AppConfig)
async def update_config(config: AppConfig):
    config_dict = config.dict()
    config_dict["updated_at"] = datetime.utcnow()
    
    result = await db.config.update_one(
        {}, 
        {"$set": config_dict},
        upsert=True
    )
    
    if result:
        await broadcast_to_clients({
            "type": "config_updated",
            "message": "Configuration updated successfully"
        })
        return config
    else:
        raise HTTPException(status_code=400, detail="Failed to update configuration")

@app.get("/api/providers", response_model=List[AIProvider])
async def get_providers():
    providers = []
    async for provider in db.providers.find({}):
        providers.append(AIProvider(**provider))
    return providers

@app.post("/api/providers", response_model=AIProvider)
async def create_provider(provider: AIProvider):
    provider_dict = provider.dict()
    provider_dict["created_at"] = datetime.utcnow()
    provider_dict["updated_at"] = datetime.utcnow()
    
    result = await db.providers.insert_one(provider_dict)
    if result.inserted_id:
        return provider
    else:
        raise HTTPException(status_code=400, detail="Failed to create provider")

@app.put("/api/providers/{provider_id}", response_model=AIProvider)
async def update_provider(provider_id: str, provider: AIProvider):
    provider_dict = provider.dict()
    provider_dict["updated_at"] = datetime.utcnow()
    
    result = await db.providers.update_one(
        {"id": provider_id}, 
        {"$set": provider_dict}
    )
    
    if result.modified_count:
        await broadcast_to_clients({
            "type": "provider_updated",
            "provider_id": provider_id,
            "message": f"Provider {provider.name} updated"
        })
        return provider
    else:
        raise HTTPException(status_code=404, detail="Provider not found")

@app.patch("/api/providers/{provider_id}/selectors")
async def update_selectors(provider_id: str, selector_update: SelectorUpdate):
    result = await db.providers.update_one(
        {"id": provider_id},
        {"$set": {"selectors": selector_update.selectors, "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count:
        await broadcast_to_clients({
            "type": "selectors_updated",
            "provider_id": provider_id,
            "selectors": selector_update.selectors,
            "message": "Selectors updated dynamically"
        })
        return {"message": "Selectors updated successfully"}
    else:
        raise HTTPException(status_code=404, detail="Provider not found")

@app.post("/api/generate-prompts")
async def generate_prompts(theme: str, count: int = 5, provider: str = "openai"):
    config = await db.config.find_one({})
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not found")
    
    try:
        if provider.lower() == "openai":
            prompts = await generate_prompts_openai(theme, count, config.get("openai_api_key"))
        elif provider.lower() == "gemini":
            prompts = await generate_prompts_gemini(theme, count, config.get("gemini_api_key"))
        else:
            raise HTTPException(status_code=400, detail="Invalid provider")
        
        if not prompts:
            raise HTTPException(status_code=500, detail="Failed to generate prompts")
            
        await broadcast_to_clients({
            "type": "prompts_generated",
            "theme": theme,
            "count": len(prompts),
            "provider": provider
        })
        
        return {"prompts": prompts, "theme": theme, "provider": provider}
        
    except Exception as e:
        logger.error(f"Error generating prompts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs", response_model=ImageGenerationJob)
async def create_job(prompt: str, provider: str, priority: int = 1):
    job = ImageGenerationJob(
        prompt=prompt,
        provider=provider,
        priority=priority,
        metadata={"source": "api", "user_agent": "desktop_app"}
    )
    
    job_dict = job.dict()
    result = await db.jobs.insert_one(job_dict)
    
    if result.inserted_id:
        await job_queue.put(job)
        
        await broadcast_to_clients({
            "type": "job_created",
            "job_id": job.id,
            "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
            "provider": provider
        })
        
        return job
    else:
        raise HTTPException(status_code=400, detail="Failed to create job")

@app.get("/api/jobs", response_model=List[ImageGenerationJob])
async def get_jobs(limit: int = 50, status: Optional[str] = None):
    query = {}
    if status:
        query["status"] = status
    
    jobs = []
    async for job in db.jobs.find(query).sort("created_at", -1).limit(limit):
        jobs.append(ImageGenerationJob(**job))
    
    return jobs

@app.get("/api/jobs/{job_id}", response_model=ImageGenerationJob)
async def get_job(job_id: str):
    job = await db.jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return ImageGenerationJob(**job)

@app.delete("/api/jobs/{job_id}")
async def cancel_job(job_id: str):
    result = await db.jobs.update_one(
        {"id": job_id, "status": {"$in": ["queued", "processing"]}},
        {"$set": {"status": "cancelled", "updated_at": datetime.utcnow()}}
    )
    
    if result.modified_count:
        await broadcast_to_clients({
            "type": "job_cancelled",
            "job_id": job_id
        })
        return {"message": "Job cancelled successfully"}
    else:
        raise HTTPException(status_code=404, detail="Job not found or cannot be cancelled")

@app.post("/api/batch", response_model=BatchJob)
async def create_batch_job(batch: BatchJob):
    batch_dict = batch.dict()
    batch_dict["progress"]["total"] = len(batch.prompts) * len(batch.providers)
    
    result = await db.batches.insert_one(batch_dict)
    
    if result.inserted_id:
        # Create individual jobs for the batch
        jobs = []
        for prompt in batch.prompts:
            for provider in batch.providers:
                job = ImageGenerationJob(
                    prompt=prompt,
                    provider=provider,
                    priority=2,  # Higher priority for batch jobs
                    metadata={"batch_id": batch.id, "source": "batch"}
                )
                
                job_dict = job.dict()
                await db.jobs.insert_one(job_dict)
                jobs.append(job.id)
                await job_queue.put(job)
        
        # Update batch with job IDs
        await db.batches.update_one(
            {"id": batch.id},
            {"$set": {"jobs": jobs, "status": "processing"}}
        )
        
        await broadcast_to_clients({
            "type": "batch_started",
            "batch_id": batch.id,
            "total_jobs": len(jobs)
        })
        
        batch.jobs = jobs
        return batch
    else:
        raise HTTPException(status_code=400, detail="Failed to create batch job")

@app.get("/api/batches", response_model=List[BatchJob])
async def get_batches():
    batches = []
    async for batch in db.batches.find({}).sort("created_at", -1):
        batches.append(BatchJob(**batch))
    return batches

@app.get("/api/templates", response_model=List[PromptTemplate])
async def get_templates():
    templates = []
    async for template in db.templates.find({}):
        templates.append(PromptTemplate(**template))
    return templates

@app.post("/api/templates", response_model=PromptTemplate)
async def create_template(template: PromptTemplate):
    template_dict = template.dict()
    result = await db.templates.insert_one(template_dict)
    
    if result.inserted_id:
        return template
    else:
        raise HTTPException(status_code=400, detail="Failed to create template")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)