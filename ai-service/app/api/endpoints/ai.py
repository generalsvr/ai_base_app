import logging
import json
import time
from typing import List, Optional, Callable, Any, Union, Dict
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Body, Query, Request as FastAPIRequest
from fastapi.responses import StreamingResponse, Response
import base64
import functools
from pydantic import BaseModel
from urllib.parse import urlparse

from app.schemas.ai import (
    CompletionRequest, CompletionResponse,
    EmbeddingRequest, EmbeddingResponse, EmbeddingData, EmbeddingDB,
    SimilarityRequest, SimilarityResponse, SimilarityResult,
    ImageResponse, ImageProcessingRequest,
    AudioTranscriptionRequest, AudioTranscriptionResponse,
    TTSRequest, TTSCloneVoiceRequest, TTSEmotionControl, TTSSupportedFormat, TTSSupportedLanguage,
    Provider
)
from app.services.openai_service import OpenAIService
from app.services.groq_service import GroqService
from app.services.zyphra_service import ZyphraService
from app.services.qdrant_service import QdrantService
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter()
qdrant_service = QdrantService()
analytics_service = AnalyticsService()


def get_ai_service(provider: Provider, api_key: Optional[str] = None, base_url: Optional[str] = None):
    """Get the appropriate AI service based on the provider"""
    if provider == Provider.GROQ:
        return GroqService(api_key=api_key)
    elif provider == Provider.ZYPHRA:
        return ZyphraService(api_key=api_key)
    else:  # Default to OpenAI
        return OpenAIService(api_key=api_key, base_url=base_url)


def handle_exceptions(operation_name: str):
    """
    Decorator for handling exceptions in endpoint functions
    
    Args:
        operation_name: Name of the operation (for error logging)
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_msg = f"Error {operation_name}: {e}"
                logger.error(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)
        return wrapper
    return decorator


@router.post("/completions", response_model=CompletionResponse)
@handle_exceptions("creating completion")
async def create_completion(request: CompletionRequest):
    """Create a text completion"""
    ai_service = get_ai_service(
        provider=request.provider,
        api_key=request.api_key,
        base_url=request.base_url
    )
    
    # Track start time for response time measurement
    start_time = time.time()
    success = True
    error_message = None
    completion = None
    
    try:
        completion = await ai_service.create_completion(
            prompt=request.prompt,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            stop=request.stop
        )
    except Exception as e:
        success = False
        error_message = str(e)
        raise
    finally:
        # Calculate response time
        response_time = time.time() - start_time
        
        # Estimate token count (this is simplified, implement proper token counting based on your model)
        tokens = len(request.prompt.split()) + (len(completion.text.split()) if completion else 0)
        
        # Log to analytics
        await analytics_service.log_ai_call(
            user_id=request.user_id or "anonymous",
            model_used=request.model,
            call_type="completion",
            tokens=tokens,
            response_time=response_time,
            success=success,
            error_message=error_message
        )
    
    return completion


@router.post("/completions/stream")
@handle_exceptions("creating streaming completion")
async def create_completion_stream(request: CompletionRequest):
    """Create a streaming text completion"""
    ai_service = get_ai_service(
        provider=request.provider,
        api_key=request.api_key,
        base_url=request.base_url
    )
    
    async def stream_generator():
        async for chunk in ai_service.create_completion_stream(
            prompt=request.prompt,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            stop=request.stop
        ):
            # Format each chunk as a Server-Sent Event with proper JSON serialization
            yield f"data: {json.dumps(chunk)}\n\n"
        
        # Send a final message to indicate the stream is done
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream"
    )


@router.post("/embeddings", response_model=EmbeddingDB, status_code=status.HTTP_201_CREATED)
@handle_exceptions("creating embedding")
async def create_embedding(request: EmbeddingRequest):
    """Create and store an embedding"""
    # Track start time for response time measurement
    start_time = time.time()
    success = True
    error_message = None
    embedding_vector = None
    
    try:
        # Create the embedding using the selected provider
        ai_service = get_ai_service(
            provider=request.provider,
            api_key=request.api_key,
            base_url=request.base_url
        )
        
        try:
            embedding_vector = await ai_service.create_embedding(
                input_text=request.input,
                model=request.model
            )
        except NotImplementedError:
            # If the provider doesn't support embeddings, try OpenAI as fallback
            logger.warning(f"Provider {request.provider} doesn't support embeddings. Falling back to OpenAI")
            openai_service = OpenAIService(api_key=request.api_key, base_url=request.base_url)
            embedding_vector = await openai_service.create_embedding(
                input_text=request.input,
                model=request.model
            )
        
        # Store the embedding in Qdrant
        embedding_data = qdrant_service.create_embedding(
            text=request.input,
            embedding=embedding_vector
        )
        
        return embedding_data
    except Exception as e:
        success = False
        error_message = str(e)
        raise
    finally:
        # Calculate response time
        response_time = time.time() - start_time
        
        # Estimate token count (simplified)
        tokens = len(request.input.split()) + (len(embedding_vector) if embedding_vector else 0)
        
        # Log to analytics
        await analytics_service.log_ai_call(
            user_id=request.user_id or "anonymous",
            model_used=request.model or "default_embedding_model",
            call_type="embedding",
            tokens=tokens,
            response_time=response_time,
            success=success,
            error_message=error_message
        )


@router.get("/embeddings/{embedding_id}", response_model=EmbeddingDB)
@handle_exceptions("getting embedding")
async def get_embedding(embedding_id: int):
    """Get an embedding by ID"""
    embedding = qdrant_service.get_embedding_by_id(embedding_id)
    if not embedding:
        raise HTTPException(status_code=404, detail="Embedding not found")
    return embedding


@router.delete("/embeddings/{embedding_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_exceptions("deleting embedding")
async def delete_embedding(embedding_id: int):
    """Delete an embedding by ID"""
    result = qdrant_service.delete_embedding(embedding_id)
    if not result:
        raise HTTPException(status_code=404, detail="Embedding not found")
    return None


@router.post("/similarity", response_model=SimilarityResponse)
@handle_exceptions("finding similar texts")
async def find_similar(request: SimilarityRequest):
    """Find similar texts based on vector similarity"""
    # Track start time for response time measurement
    start_time = time.time()
    success = True
    error_message = None
    query_embedding = None
    
    try:
        # Create the embedding for the query
        ai_service = get_ai_service(
            provider=request.provider,
            api_key=request.api_key,
            base_url=request.base_url
        )
        
        try:
            query_embedding = await ai_service.create_embedding(
                input_text=request.query,
                model=request.model
            )
        except NotImplementedError:
            # If the provider doesn't support embeddings, try OpenAI as fallback
            logger.warning(f"Provider {request.provider} doesn't support embeddings. Falling back to OpenAI")
            openai_service = OpenAIService(api_key=request.api_key, base_url=request.base_url)
            query_embedding = await openai_service.create_embedding(
                input_text=request.query,
                model=request.model
            )
        
        # Find similar embeddings in Qdrant
        similar_results = qdrant_service.find_similar(
            embedding=query_embedding,
            limit=request.limit,
            threshold=request.threshold
        )
        
        return {"results": similar_results}
    except Exception as e:
        success = False
        error_message = str(e)
        raise
    finally:
        # Calculate response time
        response_time = time.time() - start_time
        
        # Estimate token count (simplified)
        tokens = len(request.query.split()) + (len(query_embedding) if query_embedding else 0)
        
        # Log to analytics
        await analytics_service.log_ai_call(
            user_id=request.user_id or "anonymous",
            model_used=request.model or "default_embedding_model",
            call_type="similarity_search",
            tokens=tokens,
            response_time=response_time,
            success=success,
            error_message=error_message
        )


@router.post("/images", response_model=ImageResponse)
@handle_exceptions("processing image")
async def process_image(
    request: FastAPIRequest,
    prompt: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    model: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    base_url: Optional[str] = Form(None),
    provider: Optional[str] = Form(Provider.OPENAI),
    user_id: Optional[str] = Form(None)
):
    """
    Process an image from various sources (URL, base64, or file upload).
    This consolidated endpoint supports both JSON body and form data.
    """
    # Track start time for response time measurement
    start_time = time.time()
    success = True
    error_message = None
    actual_prompt = None
    result = None
    
    try:
        # Debug info - log headers
        logger.info(f"Request Content-Type: {request.headers.get('content-type', 'Not provided')}")
        logger.info(f"Request method: {request.method}")
        
        body_bytes = await request.body()
        logger.info(f"Request body length: {len(body_bytes) if body_bytes else 0} bytes")
        
        # Extract user_id from JSON body if present and not provided in form
        if body_bytes and request.headers.get('content-type') == 'application/json':
            try:
                import json
                body_json = json.loads(body_bytes)
                logger.info(f"Request body JSON keys: {list(body_json.keys())}")
                
                if 'user_id' in body_json and user_id is None:
                    user_id = body_json.get('user_id')
            except Exception as e:
                logger.error(f"Error parsing request body as JSON: {e}")
        
        # Process form data or JSON based on what's received
        if file is not None or prompt is not None or image_url is not None:
            # Form data
            if not prompt:
                raise HTTPException(status_code=400, detail="Prompt is required for form data")
            
            actual_prompt = prompt
            
            if not file and not image_url:
                raise HTTPException(status_code=400, detail="Either file or image_url must be provided")
                
            # OpenAI is currently the only supported provider
            if provider != Provider.OPENAI:
                logger.warning(f"Provider {provider} doesn't support image processing. Using OpenAI")
                
            openai_service = OpenAIService(api_key=api_key, base_url=base_url)
            
            if file:
                # Process file upload
                image_bytes = await file.read()
                result = await openai_service.process_image_from_bytes(
                    prompt=prompt,
                    image_bytes=image_bytes,
                    model=model
                )
            else:
                # Process URL
                result = await openai_service.process_image_from_url(
                    prompt=prompt,
                    image_url=image_url,
                    model=model
                )
        else:
            # JSON data - read the raw request body
            if not body_bytes:
                raise HTTPException(status_code=400, detail="Request body cannot be empty")
                
            # Parse JSON
            import json
            try:
                request_json = json.loads(body_bytes)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                logger.error(f"Body content: {body_bytes}")
                raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
                
            # Convert to ImageProcessingRequest for validation
            try:
                req_obj = ImageProcessingRequest(**request_json)
            except Exception as e:
                logger.error(f"Validation error: {e}")
                logger.error(f"Request JSON: {request_json}")
                raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
            
            if not req_obj.prompt:
                raise HTTPException(status_code=400, detail="Prompt is required")
            
            # Get values from request
            prompt = req_obj.prompt
            actual_prompt = prompt
            model = req_obj.model
            api_key = req_obj.api_key
            base_url = req_obj.base_url
            provider = req_obj.provider
            
            # Get user_id if present
            if hasattr(req_obj, 'user_id') and req_obj.user_id and not user_id:
                user_id = req_obj.user_id
            
            # OpenAI is the only supported provider
            if provider != Provider.OPENAI:
                logger.warning(f"Provider {provider} doesn't support image processing. Using OpenAI")
                
            openai_service = OpenAIService(api_key=api_key, base_url=base_url)
            
            if req_obj.image_url:
                # Process URL
                result = await openai_service.process_image_from_url(
                    prompt=prompt,
                    image_url=req_obj.image_url,
                    model=model
                )
            elif req_obj.image_base64:
                # Process base64 data
                try:
                    image_bytes = base64.b64decode(req_obj.image_base64)
                    result = await openai_service.process_image_from_bytes(
                        prompt=prompt,
                        image_bytes=image_bytes,
                        model=model
                    )
                except Exception as e:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Invalid base64 encoding: {str(e)}"
                    )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="No image source provided. Please provide either image_url or image_base64"
                )

        return result
    except Exception as e:
        success = False
        error_message = str(e)
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Unexpected error processing image request: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
    finally:
        # Calculate response time
        response_time = time.time() - start_time
        
        # Only log if we have a prompt (needed for token counting)
        if actual_prompt:
            await log_image_processing(
                prompt=actual_prompt,
                user_id=user_id,
                model=model,
                success=success,
                response_time=response_time,
                error_message=error_message
            )


@router.post("/audio/transcribe", response_model=AudioTranscriptionResponse)
@handle_exceptions("transcribing audio")
async def transcribe_audio(file: UploadFile = File(...),
                          model: Optional[str] = Form(None),
                          prompt: Optional[str] = Form(None),
                          language: Optional[str] = Form(None),
                          temperature: float = Form(0.0),
                          api_key: Optional[str] = Form(None),
                          provider: str = Form(Provider.GROQ),
                          user_id: Optional[str] = Form(None)):
    """Transcribe audio file using Groq or OpenAI"""
    # Track start time for response time measurement
    start_time = time.time()
    success = True
    error_message = None
    
    try:
        # Read the uploaded file
        audio_bytes = await file.read()
        
        ai_service = get_ai_service(
            provider=provider,
            api_key=api_key
        )
        
        # The transcribe_audio method is only implemented in GroqService now
        if provider == Provider.GROQ:
            result = await ai_service.transcribe_audio(
                audio_file=audio_bytes,
                model=model,
                prompt=prompt,
                language=language,
                temperature=temperature
            )
        else:
            # You can implement OpenAI audio transcription as needed
            raise HTTPException(
                status_code=400,
                detail="OpenAI transcription not implemented yet. Please use provider=groq"
            )
        
        return result
    except Exception as e:
        success = False
        error_message = str(e)
        raise
    finally:
        # Calculate response time
        response_time = time.time() - start_time
        
        # For audio transcription, estimate tokens based on audio length
        # This is a very rough estimation - you might want to calculate this better
        # based on the actual audio duration
        tokens = 1000  # Placeholder estimation
        
        # Log to analytics
        await analytics_service.log_ai_call(
            user_id=user_id or "anonymous",
            model_used=model or "default_audio_model",
            call_type="audio_transcription",
            tokens=tokens,
            response_time=response_time,
            success=success,
            error_message=error_message
        )


@router.post("/tts/synthesize")
@handle_exceptions("synthesizing speech")
async def synthesize_speech(request: TTSRequest):
    """Convert text to speech using TTS provider"""
    # Track start time for response time measurement
    start_time = time.time()
    success = True
    error_message = None
    
    try:
        # Currently only Zyphra is supported for TTS
        if request.provider != Provider.ZYPHRA:
            logger.warning(f"Provider {request.provider} doesn't support TTS. Using Zyphra")
            provider = Provider.ZYPHRA
        else:
            provider = request.provider
            
        # Get the TTS service
        tts_service = get_ai_service(
            provider=provider,
            api_key=request.api_key
        )
        
        # Generate speech
        audio_data = await tts_service.generate_speech(
            text=request.text,
            model=request.model,
            speaking_rate=request.speaking_rate,
            language_iso_code=request.language_iso_code,
            mime_type=request.mime_type,
            emotion=request.emotion,
            vqscore=request.vqscore,
            speaker_noised=request.speaker_noised,
            speaker_audio=None  # Not cloning voice here
        )
        
        # Determine content type for the response
        content_type = request.mime_type or "audio/webm"
        
        # Return the audio data
        return Response(
            content=audio_data,
            media_type=content_type
        )
    except Exception as e:
        success = False
        error_message = str(e)
        raise
    finally:
        # Calculate response time
        response_time = time.time() - start_time
        
        # Estimate tokens based on text length
        tokens = len(request.text.split())
        
        # Log to analytics
        await analytics_service.log_ai_call(
            user_id=request.user_id or "anonymous",
            model_used=request.model or "default_tts_model",
            call_type="text_to_speech",
            tokens=tokens,
            response_time=response_time,
            success=success,
            error_message=error_message
        )


@router.post("/tts/clone-voice")
@handle_exceptions("synthesizing speech with voice cloning")
async def synthesize_speech_with_cloned_voice(request: TTSCloneVoiceRequest):
    """Convert text to speech using a cloned voice"""
    # Track start time for response time measurement
    start_time = time.time()
    success = True
    error_message = None
    
    try:
        # Currently only Zyphra is supported for TTS with voice cloning
        if request.provider != Provider.ZYPHRA:
            logger.warning(f"Provider {request.provider} doesn't support TTS with voice cloning. Using Zyphra")
            provider = Provider.ZYPHRA
        else:
            provider = request.provider
            
        # Get the TTS service
        tts_service = get_ai_service(
            provider=provider,
            api_key=request.api_key
        )
        
        # Generate speech with cloned voice
        audio_data = await tts_service.generate_speech(
            text=request.text,
            model=request.model,
            speaking_rate=request.speaking_rate,
            language_iso_code=request.language_iso_code,
            mime_type=request.mime_type,
            emotion=request.emotion,
            vqscore=request.vqscore,
            speaker_noised=request.speaker_noised,
            speaker_audio=request.speaker_audio_base64
        )
        
        # Determine content type for the response
        content_type = request.mime_type or "audio/webm"
        
        # Return the audio data
        return Response(
            content=audio_data,
            media_type=content_type
        )
    except Exception as e:
        success = False
        error_message = str(e)
        raise
    finally:
        # Calculate response time
        response_time = time.time() - start_time
        
        # Estimate tokens based on text length and include a factor for voice cloning
        tokens = len(request.text.split()) * 2  # Double the tokens for voice cloning processing
        
        # Log to analytics
        await analytics_service.log_ai_call(
            user_id=request.user_id or "anonymous",
            model_used=request.model or "default_tts_model",
            call_type="tts_voice_cloning",
            tokens=tokens,
            response_time=response_time,
            success=success,
            error_message=error_message
        )


@router.post("/tts/emotion")
@handle_exceptions("synthesizing speech with emotion")
async def synthesize_speech_with_emotion(
    text: str = Form(...),
    happiness: float = Form(0.6),
    neutral: float = Form(0.6),
    sadness: float = Form(0.05),
    disgust: float = Form(0.05),
    fear: float = Form(0.05),
    surprise: float = Form(0.05),
    anger: float = Form(0.05),
    other: float = Form(0.5),
    model: Optional[str] = Form(None),
    speaking_rate: float = Form(15.0),
    language_iso_code: Optional[str] = Form(None),
    mime_type: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    provider: str = Form(Provider.ZYPHRA),
    user_id: Optional[str] = Form(None)
):
    """Convert text to speech with emotion control"""
    # Track start time for response time measurement
    start_time = time.time()
    success = True
    error_message = None
    
    try:
        # Currently only Zyphra is supported for TTS with emotion control
        if provider != Provider.ZYPHRA:
            logger.warning(f"Provider {provider} doesn't support TTS with emotion control. Using Zyphra")
            provider = Provider.ZYPHRA
            
        # Get the TTS service
        tts_service = get_ai_service(
            provider=provider,
            api_key=api_key
        )
        
        # Create emotion weights
        emotion = {
            "happiness": happiness,
            "neutral": neutral,
            "sadness": sadness,
            "disgust": disgust,
            "fear": fear,
            "surprise": surprise,
            "anger": anger,
            "other": other
        }
        
        # Generate speech with emotion
        audio_data = await tts_service.generate_speech(
            text=text,
            model=model,
            speaking_rate=speaking_rate,
            language_iso_code=language_iso_code,
            mime_type=mime_type,
            emotion=emotion
        )
        
        # Determine content type for the response
        content_type = mime_type or "audio/webm"
        
        # Return the audio data
        return Response(
            content=audio_data,
            media_type=content_type
        )
    except Exception as e:
        success = False
        error_message = str(e)
        raise
    finally:
        # Calculate response time
        response_time = time.time() - start_time
        
        # Estimate tokens based on text length
        tokens = len(text.split())
        
        # Log to analytics
        await analytics_service.log_ai_call(
            user_id=user_id or "anonymous",
            model_used=model or "default_tts_model",
            call_type="tts_emotion",
            tokens=tokens,
            response_time=response_time,
            success=success,
            error_message=error_message
        )


async def log_image_processing(
    prompt: str,
    user_id: Optional[str],
    model: Optional[str],
    success: bool,
    response_time: float,
    error_message: Optional[str] = None
):
    """Helper function to log image processing calls to analytics"""
    # Estimate token count based on prompt length
    tokens = len(prompt.split())
    
    # Log to analytics
    await analytics_service.log_ai_call(
        user_id=user_id or "anonymous",
        model_used=model or "default_image_model",
        call_type="image_processing",
        tokens=tokens,
        response_time=response_time,
        success=success,
        error_message=error_message
    ) 