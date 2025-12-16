"""
Language detection and translation utility for multilingual CV support
Uses googletrans library for language detection and translation
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import googletrans
try:
    from googletrans import Translator, LANGUAGES
    HAS_GOOGLETRANS = True
except (ImportError, AttributeError, Exception) as e:
    HAS_GOOGLETRANS = False
    logger.warning(f"googletrans not available (error: {str(e)}). Multilingual support will be limited.")

# Fallback: Try langdetect for language detection only
try:
    from langdetect import detect, DetectorFactory
    # Set seed for consistent results
    DetectorFactory.seed = 0
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False
    logger.warning("langdetect not installed. Language detection will be unavailable.")


def detect_language(text: str) -> Optional[str]:
    """
    Detect the language of the input text.
    
    Args:
        text: Text to detect language for
        
    Returns:
        Language code (e.g., 'en', 'vi', 'zh', 'fr') or None if detection fails
    """
    if not text or not isinstance(text, str) or len(text.strip()) < 10:
        logger.warning("Text too short for language detection")
        return None
    
    # Try googletrans first (better accuracy)
    if HAS_GOOGLETRANS:
        try:
            translator = Translator()
            detected = translator.detect(text)
            lang_code = detected.lang
            confidence = detected.confidence if hasattr(detected, 'confidence') else None
            
            logger.info(f"Detected language: {lang_code} (confidence: {confidence})")
            return lang_code
        except Exception as e:
            logger.warning(f"googletrans detection failed: {str(e)}, trying langdetect")
    
    # Fallback to langdetect (detection only, no translation)
    if HAS_LANGDETECT:
        try:
            lang_code = detect(text)
            logger.info(f"Detected language (langdetect): {lang_code}")
            return lang_code
        except Exception as e:
            logger.warning(f"langdetect detection failed: {str(e)}")
            return None
    
    # If no library available, assume English (fallback)
    logger.warning("No language detection library available, assuming English")
    return 'en'


def translate_to_english(text: str, source_lang: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Translate text to English for classification.
    
    Args:
        text: Text to translate
        source_lang: Source language code (optional, will be detected if not provided)
        
    Returns:
        Tuple of (translated_text, detected_lang) or (None, None) if translation fails
    """
    if not text or not isinstance(text, str):
        logger.warning("Invalid text for translation")
        return None, None
    
    # If no translation library available, return original text
    if not HAS_GOOGLETRANS:
        logger.warning("googletrans not available, skipping translation")
        # Try to detect language anyway
        detected_lang = detect_language(text) if HAS_LANGDETECT else None
        return text, detected_lang
    
    try:
        translator = Translator()
        
        # Detect language if not provided
        if not source_lang:
            detected = translator.detect(text)
            source_lang = detected.lang
        
        # If already English, no need to translate
        if source_lang == 'en':
            logger.info("Text is already in English, skipping translation")
            return text, 'en'
        
        # Translate to English
        logger.info(f"Translating from {source_lang} to English...")
        translated = translator.translate(text, src=source_lang, dest='en')
        
        if translated and translated.text:
            logger.info(f"Successfully translated text ({len(text)} -> {len(translated.text)} chars)")
            return translated.text, source_lang
        else:
            logger.warning("Translation returned empty result")
            return None, source_lang
            
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        # Return original text if translation fails
        return text, source_lang


def prepare_text_for_classification(text: str, auto_translate: bool = True) -> Tuple[str, Optional[str], bool]:
    """
    Prepare text for classification by detecting language and translating if needed.
    
    Args:
        text: CV text content
        auto_translate: Whether to automatically translate non-English text
        
    Returns:
        Tuple of (prepared_text, detected_lang, was_translated)
        - prepared_text: Text ready for classification (English)
        - detected_lang: Detected source language code
        - was_translated: True if translation was performed
    """
    if not text or not isinstance(text, str):
        return text, None, False
    
    # Detect language
    detected_lang = detect_language(text)
    
    # If English or detection failed, return as-is
    if detected_lang == 'en' or not detected_lang:
        return text, detected_lang or 'en', False
    
    # If auto_translate is enabled and text is not English, translate
    if auto_translate:
        translated_text, source_lang = translate_to_english(text, detected_lang)
        if translated_text and translated_text != text:
            logger.info(f"Text translated from {detected_lang} to English")
            return translated_text, detected_lang, True
        else:
            logger.warning(f"Translation failed or not needed, using original text")
            return text, detected_lang, False
    else:
        # Return original text without translation
        return text, detected_lang, False


def get_language_name(lang_code: str) -> str:
    """
    Get human-readable language name from language code.
    
    Args:
        lang_code: Language code (e.g., 'en', 'vi', 'zh')
        
    Returns:
        Language name (e.g., 'English', 'Vietnamese', 'Chinese')
    """
    if HAS_GOOGLETRANS and lang_code in LANGUAGES:
        return LANGUAGES[lang_code].capitalize()
    
    # Fallback mapping for common languages
    lang_names = {
        'en': 'English',
        'vi': 'Vietnamese',
        'zh': 'Chinese',
        'zh-cn': 'Chinese (Simplified)',
        'zh-tw': 'Chinese (Traditional)',
        'fr': 'French',
        'de': 'German',
        'es': 'Spanish',
        'ja': 'Japanese',
        'ko': 'Korean',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'ar': 'Arabic',
        'it': 'Italian',
        'th': 'Thai',
        'id': 'Indonesian',
    }
    
    return lang_names.get(lang_code, lang_code.upper())

