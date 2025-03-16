import logging
import os
import base64
import asyncio
from typing import Dict, Any, Optional, List, Union, BinaryIO
import replicate

from app.core.config import settings

logger = logging.getLogger(__name__)


class ReplicateService:
    """Service for interacting with Replicate API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Replicate client with API key"""
        self.api_key = api_key or settings.REPLICATE_API_TOKEN
        
        if not self.api_key:
            logger.warning("Replicate API token not provided. API calls will fail.")

    async def generate_image(
        self,
        prompt: str,
        model: Optional[str] = None,
        num_outputs: int = 1,
        size: Optional[str] = None,
        guidance_scale: Optional[float] = None,
        num_inference_steps: Optional[int] = None,
        seed: Optional[int] = None,
        **kwargs
    ) -> List[str]:
        """
        Generate images from text using Replicate API
        
        Args:
            prompt: Text prompt for image generation
            model: Replicate model to use (format: username/model_name:version)
            num_outputs: Number of images to generate
            size: Image size (width x height)
            guidance_scale: How strictly to follow the prompt
            num_inference_steps: Number of steps for diffusion
            seed: Random seed for reproducibility
            **kwargs: Additional model-specific parameters
            
        Returns:
            List of URLs to generated images
        """
        try:
            model = model or settings.DEFAULT_REPLICATE_IMAGE_MODEL
            
            # Create client
            client = replicate.Client(api_token=self.api_key)
            
            # Build model input parameters
            input_params = {
                "prompt": prompt,
                "num_outputs": num_outputs
            }
            
            # Add optional parameters if provided
            if size:
                # Parse size string (e.g., "1024x1024")
                try:
                    width, height = map(int, size.split("x"))
                    input_params["width"] = width
                    input_params["height"] = height
                except ValueError:
                    # If size isn't in expected format, ignore it
                    logger.warning(f"Invalid size format: {size}. Expected format: widthxheight")
            
            if guidance_scale is not None:
                input_params["guidance_scale"] = guidance_scale
                
            if num_inference_steps is not None:
                input_params["num_inference_steps"] = num_inference_steps
                
            if seed is not None:
                input_params["seed"] = seed
                
            # Add any additional parameters
            input_params.update(kwargs)
            
            # Run the model asynchronously
            outputs = await asyncio.to_thread(
                client.run,
                model,
                input=input_params
            )
            
            # Convert output to list of image URLs
            if isinstance(outputs, list):
                # Some models return a list of image URLs
                return [str(url) for url in outputs]
            else:
                # Some models might return a single output or a dictionary
                logger.warning(f"Unexpected output format from Replicate: {type(outputs)}")
                if isinstance(outputs, dict) and "output" in outputs:
                    return outputs["output"] if isinstance(outputs["output"], list) else [outputs["output"]]
                return [str(outputs)]
            
        except Exception as e:
            logger.error(f"Error generating images with Replicate: {e}")
            raise 