"""
Image OCR utilities for CV files
Supports JPG, PNG, JPEG image formats using EasyOCR
"""

import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False
    logger.warning("easyocr not installed. Image OCR support will be unavailable.")

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logger.warning("Pillow not installed. Image preprocessing will be limited.")


_reader = None


def get_ocr_reader(languages: List[str] = ['en', 'vi']) -> Optional[object]:
    """
    Get or initialize EasyOCR reader.
    Initialize once for better performance.
    
    Args:
        languages: List of language codes to support (default: ['en', 'vi'])
        
    Returns:
        EasyOCR reader object or None if not available
    """
    global _reader
    
    if not HAS_EASYOCR:
        return None
    
    if _reader is None:
        try:
            logger.info(f"Initializing EasyOCR reader with languages: {languages}")
            _reader = easyocr.Reader(languages, gpu=False)  # Set gpu=True if GPU available
            logger.info("EasyOCR reader initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR reader: {str(e)}")
            return None
    
    return _reader


def preprocess_image(image_path: str) -> Optional[Image.Image]:
    """
    Preprocess image for better OCR accuracy.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Preprocessed PIL Image or None if error
    """
    if not HAS_PIL:
        return None
    
    try:
        image = Image.open(image_path)
        
            # Convert to RGB if needed (for PNG with transparency)
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        max_size = 3000
        width, height = image.size
        if width > max_size or height > max_size:
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
        
        return image
        
    except Exception as e:
        logger.error(f"Image preprocessing failed: {str(e)}")
        return None


def extract_text_from_image(image_path: str, languages: List[str] = ['en', 'vi'], timeout: int = 30) -> Optional[str]:
    """
    Extract text from image file using EasyOCR.
    Added timeout to prevent hanging.
    
    Args:
        image_path: Path to image file (jpg, jpeg, png)
        languages: List of language codes to support (default: ['en', 'vi'])
        timeout: Maximum time in seconds to wait for OCR (default: 30)
        
    Returns:
        Extracted text as string, or None if error, timeout, or OCR unavailable
    """
    if not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return None
    
    if not HAS_EASYOCR:
        logger.warning("EasyOCR not available. Image uploaded but text extraction skipped.")
        return None
    
    try:
        # Check file size - skip OCR for very large images to prevent hanging
        file_size = os.path.getsize(image_path)
        max_size_for_ocr = 5 * 1024 * 1024  # 5MB
        if file_size > max_size_for_ocr:
            logger.warning(f"Image too large for OCR ({file_size / 1024 / 1024:.1f}MB > 5MB). Skipping text extraction.")
            return None
        
        reader = get_ocr_reader(languages)
        if not reader:
            logger.warning("Failed to initialize EasyOCR reader. Image uploaded but text extraction skipped.")
            return None
        
        # Use timeout to prevent hanging
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("OCR processing timeout")
        
        # Set timeout (Unix only, Windows will use try-except)
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
        except (AttributeError, ValueError):
            # Windows doesn't support SIGALRM, will rely on try-except
            pass
        
        try:
            if HAS_PIL:
                processed_image = preprocess_image(image_path)
                if processed_image:
                    import tempfile
                    temp_path = None
                    try:
                        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                            temp_path = temp_file.name
                            processed_image.save(temp_path, 'JPEG', quality=95)
                        
                        logger.info(f"Processing image with OCR: {image_path}")
                        results = reader.readtext(temp_path)
                    finally:
                        if temp_path and os.path.exists(temp_path):
                            try:
                                os.unlink(temp_path)
                            except:
                                pass
                else:
                    logger.warning("Image preprocessing failed, using original image")
                    results = reader.readtext(image_path)
            else:
                logger.info(f"Processing image with OCR (no preprocessing): {image_path}")
                results = reader.readtext(image_path)
            
            # Cancel timeout
            try:
                signal.alarm(0)
            except (AttributeError, ValueError):
                pass
            
            text_lines = []
            for (bbox, text, confidence) in results:
                if confidence >= 0.5:
                    text_lines.append(text)
            
            if text_lines:
                text = "\n".join(text_lines)
                logger.info(f"Successfully extracted text from image ({len(text)} characters, {len(text_lines)} lines)")
                return text.strip()
            else:
                logger.warning(f"No text extracted from image (all results had low confidence)")
                return None
                
        except TimeoutError:
            logger.warning(f"OCR processing timeout after {timeout}s. Image uploaded but text extraction skipped.")
            try:
                signal.alarm(0)
            except (AttributeError, ValueError):
                pass
            return None
        except Exception as e:
            logger.error(f"OCR extraction failed for {image_path}: {str(e)}")
            try:
                signal.alarm(0)
            except (AttributeError, ValueError):
                pass
            return None
            
    except Exception as e:
        logger.error(f"OCR extraction failed for {image_path}: {str(e)}")
        return None


def extract_text_from_image_file(image_path: str, file_type: str = None) -> Optional[str]:
    """
    Extract text from image file based on file type.
    Wrapper function for consistency with other extractors.
    
    Args:
        image_path: Path to image file
        file_type: File extension (jpg, jpeg, png). If None, auto-detect from file_path
        
    Returns:
        Extracted text as string, or None if error or unsupported format
    """
    if not file_type:
        _, ext = os.path.splitext(image_path)
        file_type = ext.lstrip('.').lower()
    
    file_type = file_type.lower()
    
    if file_type in ['jpg', 'jpeg', 'png']:
        return extract_text_from_image(image_path)
    else:
        logger.error(f"Unsupported image file type: {file_type}")
        return None

