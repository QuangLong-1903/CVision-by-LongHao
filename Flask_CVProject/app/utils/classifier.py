"""
Basic CV Classification utility using keyword matching
Supports multilingual CVs by translating non-English text to English
"""

import logging
from typing import Optional, Tuple, Dict, List

logger = logging.getLogger(__name__)

# Import translator for multilingual support
try:
    from app.utils.translator import prepare_text_for_classification
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False
    logger.warning("Translator not available, multilingual support disabled")

CATEGORY_KEYWORDS = {
    'Software Engineer': [
        'software engineer', 'software development', 'programming', 'coding',
        'python', 'java', 'javascript', 'react', 'vue', 'angular', 'node.js',
        'backend', 'frontend', 'full stack', 'web development', 'app development',
        'database', 'sql', 'api', 'rest', 'git', 'agile', 'scrum'
    ],
    'Data Scientist': [
        'data scientist', 'data science', 'machine learning', 'ml', 'ai',
        'data analysis', 'analytics', 'python', 'r', 'sql', 'pandas', 'numpy',
        'tensorflow', 'pytorch', 'scikit-learn', 'jupyter', 'statistics',
        'data visualization', 'big data', 'data mining', 'deep learning'
    ],
    'Project Manager': [
        'project manager', 'pm', 'project management', 'agile', 'scrum',
        'kanban', 'sprint', 'stakeholder', 'team lead', 'team leader',
        'delivery manager', 'product owner', 'jira', 'confluence', 'budget',
        'timeline', 'risk management', 'resource management'
    ],
    'Marketing': [
        'marketing', 'digital marketing', 'seo', 'sem', 'social media',
        'content marketing', 'email marketing', 'campaign', 'branding',
        'advertising', 'google ads', 'facebook ads', 'analytics', 'crm',
        'sales', 'lead generation', 'conversion', 'strategy'
    ],
    'Designer': [
        'designer', 'ui/ux', 'user interface', 'user experience', 'graphic design',
        'adobe', 'photoshop', 'illustrator', 'figma', 'sketch', 'wireframe',
        'prototype', 'interaction design', 'visual design', 'brand identity',
        'web design', 'mobile design'
    ],
    'Business Analyst': [
        'business analyst', 'ba', 'requirements', 'stakeholder', 'analysis',
        'documentation', 'process improvement', 'user stories', 'use cases',
        'sql', 'data analysis', 'reporting', 'dashboard', 'excel', 'power bi',
        'requirements gathering', 'functional specification'
    ],
    'DevOps Engineer': [
        'devops', 'ci/cd', 'docker', 'kubernetes', 'aws', 'azure', 'gcp',
        'terraform', 'ansible', 'jenkins', 'gitlab', 'github actions',
        'cloud', 'infrastructure', 'monitoring', 'logging', 'linux',
        'shell scripting', 'automation', 'deployment'
    ],
    'HR/Recruitment': [
        'hr', 'human resources', 'recruitment', 'recruiter', 'talent acquisition',
        'hiring', 'interview', 'onboarding', 'employee relations', 'payroll',
        'training', 'performance management', 'compensation', 'benefits'
    ],
    'Finance/Accounting': [
        'finance', 'accounting', 'accountant', 'cpa', 'financial analysis',
        'audit', 'tax', 'bookkeeping', 'excel', 'quickbooks', 'sap', 'erp',
        'budget', 'forecasting', 'financial reporting', 'gaap', 'ifrs'
    ],
    'Sales': [
        'sales', 'sales representative', 'account executive', 'business development',
        'customer acquisition', 'client relationship', 'negotiation', 'crm',
        'salesforce', 'quota', 'revenue', 'lead generation', 'cold calling',
        'pipeline management'
    ]
}


def classify_cv_by_keywords(text: str, categories: Optional[Dict[str, List[str]]] = None, auto_translate: bool = True) -> Tuple[Optional[str], float]:
    """
    Classify CV text using keyword matching
    Supports multilingual CVs by automatically translating non-English text to English
    
    Args:
        text: CV text content (extracted text)
        categories: Optional custom category keywords dict
        auto_translate: Whether to automatically translate non-English text (default: True)
        
    Returns:
        Tuple of (category_name, confidence_score)
        Returns (None, 0.0) if no match found
    """
    if not text or not isinstance(text, str):
        logger.warning("Empty or invalid text provided for classification")
        return None, 0.0
    
    # Prepare text for classification (detect language and translate if needed)
    original_text = text
    if HAS_TRANSLATOR and auto_translate:
        try:
            prepared_text, detected_lang, was_translated = prepare_text_for_classification(text, auto_translate=True)
            if was_translated:
                logger.info(f"CV text was translated from {detected_lang} to English for classification")
                text = prepared_text
            elif detected_lang and detected_lang != 'en':
                logger.info(f"CV text is in {detected_lang}, but translation not performed")
        except Exception as e:
            logger.warning(f"Translation preparation failed: {str(e)}, using original text")
            text = original_text
    
    text_lower = text.lower()
    
    # Use provided categories or default
    keywords_map = categories if categories else CATEGORY_KEYWORDS
    
    # Count matches for each category
    category_scores = {}
    
    for category, keywords in keywords_map.items():
        matches = 0
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matches += 1
        
        # Score = percentage of keywords matched (capped at reasonable level)
        total_keywords = len(keywords)
        if total_keywords > 0:
            score = min(matches / total_keywords, 1.0)  # Cap at 1.0
            if matches > 0:  # Only include categories with at least one match
                category_scores[category] = score
    
    if not category_scores:
        logger.info("No category matches found in CV text")
        return None, 0.0
    
    # Find category with highest score
    best_category = max(category_scores.items(), key=lambda x: x[1])
    category_name, confidence = best_category
    
    logger.info(f"Classified CV as '{category_name}' with confidence {confidence:.2%}")
    
    # Only return if confidence is above threshold (at least 10% match)
    if confidence >= 0.1:
        return category_name, confidence
    else:
        logger.info(f"Confidence too low ({confidence:.2%}), returning None")
        return None, 0.0



def get_category_id_by_name(category_name: str, job_categories_model) -> Optional[int]:
    """
    Get category ID from database by category name
    
    Args:
        category_name: Category name string
        job_categories_model: JobCategory model class
        
    Returns:
        Category ID or None if not found
    """
    try:
        category = job_categories_model.query.filter_by(name=category_name).first()
        if category:
            return category.id
        return None
    except Exception as e:
        logger.error(f"Error getting category ID: {str(e)}")
        return None

