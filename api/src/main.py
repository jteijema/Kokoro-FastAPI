"""
FastAPI OpenAI Compatible API
"""

from contextlib import asynccontextmanager

import uvicorn
from loguru import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .services.tts_model import TTSModel
from .services.tts_service import TTSService
from .services.warmup import WarmupService
from .routers.openai_compatible import router as openai_router
from .routers.text_processing import router as text_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for model initialization"""
    logger.info("Loading TTS model and voice packs...")

    # Initialize the main model with warm-up
    voicepack_count = await TTSModel.setup()
    
    # Initialize TTSService singleton and store in app state
    tts_service = TTSService()
    app.state.tts_service = tts_service
    
    # Initialize warmup service with the singleton instance
    warmup = WarmupService(tts_service=tts_service)
    loaded_voices = warmup.load_voices()
    await warmup.warmup_voices("Hello world", loaded_voices)
    
    boundary = "░" * 24
    startup_msg =f"""

{boundary}

    ╔═╗┌─┐┌─┐┌┬┐
    ╠╣ ├─┤└─┐ │ 
    ╚  ┴ ┴└─┘ ┴ 
    ╦╔═┌─┐┬┌─┌─┐
    ╠╩╗│ │├┴┐│ │
    ╩ ╩└─┘┴ ┴└─┘

{boundary}
                """
    startup_msg += f"\nModel warmed up on {TTSModel.get_device()}"
    startup_msg += f"\n{voicepack_count} voice packs loaded\n"
    startup_msg += f"\n{boundary}\n"
    logger.info(startup_msg)

    yield


# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
    openapi_url="/openapi.json",  # Explicitly enable OpenAPI schema
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(openai_router, prefix="/v1")
app.include_router(text_router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/v1/test")
async def test_endpoint():
    """Test endpoint to verify routing"""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("api.src.main:app", host=settings.host, port=settings.port, reload=True)
