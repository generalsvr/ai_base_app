import logging
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse, Response
import base64

from app.schemas.ai import (
    CompletionRequest, CompletionResponse,
    EmbeddingRequest, EmbeddingResponse, EmbeddingData, EmbeddingDB,
    SimilarityRequest, SimilarityResponse, SimilarityResult,
    ImageUrlRequest, ImageFileRequest, ImageResponse,
    AudioTranscriptionRequest, AudioTranscriptionResponse,
    TTSRequest, TTSCloneVoiceRequest, TTSEmotionControl, TTSSupportedFormat, TTSSupportedLanguage,
    Provider
)
from app.services.openai_service import OpenAIService
from app.services.groq_service import GroqService
from app.services.zyphra_service import ZyphraService
from app.services.qdrant_service import QdrantService

logger = logging.getLogger(__name__)

router = APIRouter()
qdrant_service = QdrantService()


def get_ai_service(provider: Provider, api_key: Optional[str] = None, base_url: Optional[str] = None):
    """Get the appropriate AI service based on the provider"""
    if provider == Provider.GROQ:
        return GroqService(api_key=api_key)
    elif provider == Provider.ZYPHRA:
        return ZyphraService(api_key=api_key)
    else:  # Default to OpenAI
        return OpenAIService(api_key=api_key, base_url=base_url)


@router.post("/completions", response_model=CompletionResponse)
async def create_completion(request: CompletionRequest):
    """Create a text completion"""
    try:
        ai_service = get_ai_service(
            provider=request.provider,
            api_key=request.api_key,
            base_url=request.base_url
        )
        
        completion = await ai_service.create_completion(
            prompt=request.prompt,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            stop=request.stop
        )
        return completion
    except Exception as e:
        logger.error(f"Error creating completion: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating completion: {str(e)}")


@router.post("/completions/stream")
async def create_completion_stream(request: CompletionRequest):
    """Create a streaming text completion"""
    try:
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
    except Exception as e:
        logger.error(f"Error creating streaming completion: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating streaming completion: {str(e)}")


@router.post("/embeddings", response_model=EmbeddingDB, status_code=status.HTTP_201_CREATED)
async def create_embedding(request: EmbeddingRequest):
    """Create and store an embedding"""
    try:
        # Create the embedding using the selected provider
        ai_service = get_ai_service(
            provider=request.provider,
            api_key=request.api_key,
            base_url=request.base_url
        )
        
        embedding_vector = await ai_service.create_embedding(
            input_text=request.input,
            model=request.model
        )
        
        # Store the embedding in Qdrant
        embedding_data = qdrant_service.create_embedding(
            text=request.input,
            embedding=embedding_vector
        )
        
        return embedding_data
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
        logger.error(f"Error creating embedding: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating embedding: {str(e)}")


@router.get("/embeddings/{embedding_id}", response_model=EmbeddingDB)
async def get_embedding(embedding_id: int):
    """Get an embedding by ID"""
    embedding = qdrant_service.get_embedding_by_id(embedding_id)
    if not embedding:
        raise HTTPException(status_code=404, detail="Embedding not found")
    return embedding


@router.delete("/embeddings/{embedding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_embedding(embedding_id: int):
    """Delete an embedding by ID"""
    result = qdrant_service.delete_embedding(embedding_id)
    if not result:
        raise HTTPException(status_code=404, detail="Embedding not found")
    return None


@router.post("/similarity", response_model=SimilarityResponse)
async def find_similar(request: SimilarityRequest):
    """Find similar texts based on vector similarity"""
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
        logger.error(f"Error finding similar texts: {e}")
        raise HTTPException(status_code=500, detail=f"Error finding similar texts: {str(e)}")


@router.post("/images/url", response_model=ImageResponse)
async def process_image_from_url(request: ImageUrlRequest):
    """Process an image from a URL"""
    try:
        # OpenAI is currently the only supported provider for image processing
        if request.provider != Provider.OPENAI:
            logger.warning(f"Provider {request.provider} doesn't support image processing. Using OpenAI")
        
        openai_service = OpenAIService(api_key=request.api_key, base_url=request.base_url)
        
        result = await openai_service.process_image_from_url(
            prompt=request.prompt,
            image_url=str(request.image_url),
            model=request.model
        )
        
        return result
    except Exception as e:
        logger.error(f"Error processing image from URL: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing image from URL: {str(e)}")


@router.post("/images/base64", response_model=ImageResponse)
async def process_image_from_base64(request: ImageFileRequest):
    """Process an image from base64 data"""
    try:
        # OpenAI is currently the only supported provider for image processing
        if request.provider != Provider.OPENAI:
            logger.warning(f"Provider {request.provider} doesn't support image processing. Using OpenAI")
        
        openai_service = OpenAIService(api_key=request.api_key, base_url=request.base_url)
        
        # Decode the base64 string to bytes
        try:
            image_bytes = base64.b64decode(request.image_base64)
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid base64 encoding: {str(e)}"
            )
        
        result = await openai_service.process_image_from_bytes(
            prompt=request.prompt,
            image_bytes=image_bytes,
            model=request.model
        )
        
        return result
    except Exception as e:
        logger.error(f"Error processing image from base64: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing image from base64: {str(e)}")


@router.post("/images/upload", response_model=ImageResponse)
async def process_image_from_file(
    prompt: str = Form(...),
    file: UploadFile = File(...),
    model: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    base_url: Optional[str] = Form(None),
    provider: Optional[str] = Form(Provider.OPENAI)
):
    """Process an image from an uploaded file"""
    try:
        # OpenAI is currently the only supported provider for image processing
        if provider != Provider.OPENAI:
            logger.warning(f"Provider {provider} doesn't support image processing. Using OpenAI")
        
        openai_service = OpenAIService(api_key=api_key, base_url=base_url)
        
        # Read the uploaded file
        image_bytes = await file.read()
        
        result = await openai_service.process_image_from_bytes(
            prompt=prompt,
            image_bytes=image_bytes,
            model=model
        )
        
        return result
    except Exception as e:
        logger.error(f"Error processing uploaded image: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing uploaded image: {str(e)}")


@router.post("/audio/transcribe", response_model=AudioTranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...),
                          model: Optional[str] = Form(None),
                          prompt: Optional[str] = Form(None),
                          language: Optional[str] = Form(None),
                          temperature: float = Form(0.0),
                          api_key: Optional[str] = Form(None),
                          provider: str = Form(Provider.GROQ)):
    """Transcribe audio file using Groq or OpenAI"""
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
        logger.error(f"Error transcribing audio: {e}")
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}")


@router.post("/tts/synthesize")
async def synthesize_speech(request: TTSRequest):
    """Convert text to speech using TTS provider"""
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
        logger.error(f"Error synthesizing speech: {e}")
        raise HTTPException(status_code=500, detail=f"Error synthesizing speech: {str(e)}")


@router.post("/tts/clone-voice")
async def synthesize_speech_with_cloned_voice(request: TTSCloneVoiceRequest):
    """Convert text to speech using a cloned voice"""
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
        logger.error(f"Error synthesizing speech with voice cloning: {e}")
        raise HTTPException(status_code=500, detail=f"Error synthesizing speech with voice cloning: {str(e)}")


@router.post("/tts/upload-voice")
async def synthesize_speech_with_uploaded_voice(
    text: str = Form(...),
    file: UploadFile = File(...),
    model: Optional[str] = Form(None),
    speaking_rate: float = Form(15.0),
    language_iso_code: Optional[str] = Form(None),
    mime_type: Optional[str] = Form(None),
    vqscore: Optional[float] = Form(None),
    speaker_noised: Optional[bool] = Form(None),
    api_key: Optional[str] = Form(None),
    provider: str = Form(Provider.ZYPHRA)
):
    """Convert text to speech using an uploaded voice reference"""
    try:
        # Currently only Zyphra is supported for TTS with voice cloning
        if provider != Provider.ZYPHRA:
            logger.warning(f"Provider {provider} doesn't support TTS with voice cloning. Using Zyphra")
            provider = Provider.ZYPHRA
            
        # Get the TTS service
        tts_service = get_ai_service(
            provider=provider,
            api_key=api_key
        )
        
        # Read the uploaded file
        voice_reference_bytes = await file.read()
        
        # Convert the audio bytes to base64 for the API
        voice_reference_base64 = tts_service.process_audio_bytes(voice_reference_bytes)
        
        # Generate speech with cloned voice
        audio_data = await tts_service.generate_speech(
            text=text,
            model=model,
            speaking_rate=speaking_rate,
            language_iso_code=language_iso_code,
            mime_type=mime_type,
            vqscore=vqscore,
            speaker_noised=speaker_noised,
            speaker_audio=voice_reference_base64
        )
        
        # Determine content type for the response
        content_type = mime_type or "audio/webm"
        
        # Return the audio data
        return Response(
            content=audio_data,
            media_type=content_type
        )
    except Exception as e:
        logger.error(f"Error synthesizing speech with uploaded voice: {e}")
        raise HTTPException(status_code=500, detail=f"Error synthesizing speech with uploaded voice: {str(e)}")


@router.post("/tts/emotion")
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
    provider: str = Form(Provider.ZYPHRA)
):
    """Convert text to speech with emotion control"""
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
        logger.error(f"Error synthesizing speech with emotion: {e}")
        raise HTTPException(status_code=500, detail=f"Error synthesizing speech with emotion: {str(e)}") 