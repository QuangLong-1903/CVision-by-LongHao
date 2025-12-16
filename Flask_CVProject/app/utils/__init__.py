"""
Utility functions for CVision
"""

from app.utils.text_extractor import (
    extract_text_from_file,
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt
)

from app.utils.classifier import (
    classify_cv_by_keywords,
    get_category_id_by_name,
    CATEGORY_KEYWORDS
)

from app.utils.translator import (
    detect_language,
    translate_to_english,
    prepare_text_for_classification,
    get_language_name
)

__all__ = [
    'extract_text_from_file',
    'extract_text_from_pdf',
    'extract_text_from_docx',
    'extract_text_from_txt',
    'classify_cv_by_keywords',
    'get_category_id_by_name',
    'CATEGORY_KEYWORDS',
    'detect_language',
    'translate_to_english',
    'prepare_text_for_classification',
    'get_language_name'
]

