"""
AI Content Enhancer - Sử dụng các API miễn phí
Hỗ trợ: Google Gemini (free), Hugging Face (free), Cohere (free tier)
"""

import os
import logging
from typing import Optional, Dict, List
import requests

logger = logging.getLogger(__name__)

# ============= Google Gemini API (FREE) =============
def get_gemini_client():
    """Khởi tạo Google Gemini client"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    return api_key

def enhance_with_gemini(prompt: str, system_prompt: str = None) -> Optional[str]:
    """Sử dụng Google Gemini API (FREE) - Sử dụng Google Generative AI SDK"""
    api_key = get_gemini_client()
    if not api_key:
        return None
    
    try:
        # Thử dùng Google Generative AI SDK (khuyến nghị)
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Sử dụng model mới nhất: gemini-2.5-flash (free, nhanh, tốt)
            # Fallback: gemini-flash-latest hoặc gemini-pro-latest
            models_to_try = ['gemini-2.5-flash', 'gemini-flash-latest', 'gemini-pro-latest', 'gemini-2.0-flash']
            
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(full_prompt)
                    if response and response.text:
                        logger.info(f"✓ Gemini API hoạt động (SDK) với model: {model_name}")
                        return response.text.strip()
                except Exception as e:
                    logger.debug(f"Model {model_name} failed: {str(e)}, thử model tiếp theo...")
                    continue
                    
        except ImportError:
            # Nếu không có SDK, dùng REST API
            logger.info("Google Generative AI SDK chưa được cài, dùng REST API...")
        except Exception as e:
            logger.warning(f"Gemini SDK failed: {str(e)}, thử REST API...")
        
        # Fallback: Dùng REST API (nếu SDK không hoạt động)
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        # Thử với các model mới qua REST API
        models_rest = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-flash-latest']
        for model_name in models_rest:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": full_prompt
                        }]
                    }]
                }
                response = requests.post(url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'candidates' in data and len(data['candidates']) > 0:
                        content = data['candidates'][0]['content']['parts'][0]['text']
                        logger.info(f"✓ Gemini API hoạt động (REST) với model: {model_name}")
                        return content.strip()
            except:
                continue
        
        logger.error("Tất cả các phương thức Gemini API đều không hoạt động")
        return None
        
    except Exception as e:
        logger.error(f"Lỗi khi gọi Gemini API: {str(e)}")
        return None

# ============= Hugging Face Inference API (FREE) =============
def enhance_with_huggingface(prompt: str, model: str = "microsoft/DialoGPT-large") -> Optional[str]:
    """Sử dụng Hugging Face Inference API (FREE với giới hạn)"""
    api_key = os.environ.get("HUGGINGFACE_API_KEY")
    
    try:
        # Sử dụng model text generation
        url = f"https://api-inference.huggingface.co/models/{model}"
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 200,
                "temperature": 0.8
            }
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            return data[0].get('generated_text', '').strip()
        elif isinstance(data, dict) and 'generated_text' in data:
            return data['generated_text'].strip()
        return None
    except Exception as e:
        logger.error(f"Lỗi khi gọi Hugging Face API: {str(e)}")
        return None

# ============= Cohere API (FREE TIER) =============
def get_cohere_client():
    """Khởi tạo Cohere client"""
    api_key = os.environ.get("COHERE_API_KEY")
    if not api_key:
        return None
    return api_key

def enhance_with_cohere(prompt: str) -> Optional[str]:
    """Sử dụng Cohere API (FREE tier: 100 requests/month)"""
    api_key = get_cohere_client()
    if not api_key:
        return None
    
    try:
        url = "https://api.cohere.ai/v1/generate"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "command",
            "prompt": prompt,
            "max_tokens": 200,
            "temperature": 0.8
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if 'generations' in data and len(data['generations']) > 0:
            return data['generations'][0]['text'].strip()
        return None
    except Exception as e:
        logger.error(f"Lỗi khi gọi Cohere API: {str(e)}")
        return None

# ============= Main Enhancement Functions =============
def enhance_text_free(prompt: str, system_prompt: str = None) -> Optional[str]:
    """
    Thử các API miễn phí theo thứ tự ưu tiên:
    1. Google Gemini (free, tốt nhất)
    2. Cohere (free tier)
    3. Hugging Face (free với giới hạn)
    """
    # Thử Gemini trước (free và tốt nhất)
    result = enhance_with_gemini(prompt, system_prompt)
    if result:
        logger.info("✓ Sử dụng Google Gemini API")
        return result
    
    # Thử Cohere
    result = enhance_with_cohere(prompt)
    if result:
        logger.info("✓ Sử dụng Cohere API")
        return result
    
    # Thử Hugging Face (có thể chậm hơn)
    result = enhance_with_huggingface(prompt)
    if result:
        logger.info("✓ Sử dụng Hugging Face API")
        return result
    
    logger.warning("Không có API miễn phí nào khả dụng")
    return None

def enhance_summary_free(summary: str, job_title: Optional[str] = None) -> Optional[str]:
    """Cải thiện tóm tắt bằng API miễn phí"""
    if not summary or not summary.strip():
        return None
    
    system_prompt = """Bạn là chuyên gia viết CV. Nhiệm vụ của bạn là viết lại văn bản để trở nên thu hút và chuyên nghiệp hơn.
QUAN TRỌNG: Chỉ trả về văn bản đã được cải thiện, KHÔNG có hướng dẫn, KHÔNG có nhiều lựa chọn, KHÔNG có giải thích hay lưu ý.
Chỉ trả về văn bản cuối cùng đã được cải thiện."""
    
    user_prompt = f"""Viết lại phần tóm tắt sau để trở nên thu hút và chuyên nghiệp hơn.
Giữ nguyên ý nghĩa và thông tin quan trọng. Ngắn gọn, súc tích, tối đa 150 từ.

Nội dung gốc:
{summary}
"""
    if job_title:
        user_prompt += f"\nVị trí ứng tuyển: {job_title}"
    
    user_prompt += "\n\nChỉ trả về văn bản đã được cải thiện, không có hướng dẫn hay giải thích:"
    
    result = enhance_text_free(user_prompt, system_prompt)
    
    # Làm sạch kết quả: loại bỏ các phần hướng dẫn, lựa chọn, giải thích nếu có
    if result:
        # Loại bỏ các dòng bắt đầu bằng "Lựa chọn", "---", "**", "Lưu ý", "Yêu cầu", v.v.
        lines = result.split('\n')
        cleaned_lines = []
        skip_section = False
        
        for line in lines:
            line_stripped = line.strip()
            # Bỏ qua các dòng là tiêu đề, hướng dẫn, hoặc phân cách
            if any(keyword in line_stripped.lower() for keyword in [
                'lựa chọn', '---', 'lưu ý', 'yêu cầu', 'tuyệt vời', 
                'dưới đây', 'hướng dẫn', 'chọn', 'lựa chọn phù hợp'
            ]):
                if 'lựa chọn' in line_stripped.lower():
                    skip_section = True
                continue
            
            # Bỏ qua các dòng trong section bị skip
            if skip_section and (line_stripped.startswith('**') or line_stripped.startswith('>') or line_stripped == ''):
                continue
            
            if line_stripped and not line_stripped.startswith('**') and not line_stripped.startswith('>'):
                skip_section = False
                cleaned_lines.append(line)
            elif not skip_section:
                cleaned_lines.append(line)
        
        cleaned_result = '\n'.join(cleaned_lines).strip()
        # Nếu kết quả vẫn còn quá dài hoặc có nhiều phần, chỉ lấy phần đầu tiên
        if len(cleaned_result) > 500:  # Nếu quá dài, có thể có nhiều lựa chọn
            # Lấy đoạn đầu tiên (trước khi có dấu hiệu của lựa chọn tiếp theo)
            first_paragraph = cleaned_result.split('\n\n')[0]
            if len(first_paragraph) > 50:  # Đảm bảo có nội dung
                return first_paragraph.strip()
        
        return cleaned_result if cleaned_result else result
    
    return result

def enhance_experience_free(experience: Dict) -> Optional[Dict]:
    """Cải thiện kinh nghiệm bằng API miễn phí"""
    if not experience or not experience.get("description"):
        return experience
    
    system_prompt = """Bạn là chuyên gia viết CV. Nhiệm vụ của bạn là viết lại mô tả công việc thành bullet points chuyên nghiệp.
QUAN TRỌNG: Chỉ trả về văn bản đã được cải thiện, KHÔNG có hướng dẫn, KHÔNG có nhiều lựa chọn, KHÔNG có giải thích hay lưu ý.
Chỉ trả về văn bản cuối cùng đã được cải thiện."""
    
    user_prompt = f"""Viết lại mô tả công việc sau thành 3-5 bullet points chuyên nghiệp.
Sử dụng động từ hành động mạnh mẽ. Thêm số liệu cụ thể nếu có thể.

Vị trí: {experience.get('position', 'N/A')}
Công ty: {experience.get('company', 'N/A')}
Mô tả: {experience.get('description', '')}
"""
    
    enhanced_desc = enhance_text_free(user_prompt, system_prompt)
    
    # Làm sạch kết quả tương tự như enhance_summary_free
    if enhanced_desc:
        lines = enhanced_desc.split('\n')
        cleaned_lines = []
        skip_section = False
        
        for line in lines:
            line_stripped = line.strip()
            if any(keyword in line_stripped.lower() for keyword in [
                'lựa chọn', '---', 'lưu ý', 'yêu cầu', 'tuyệt vời', 
                'dưới đây', 'hướng dẫn', 'chọn', 'lựa chọn phù hợp'
            ]):
                if 'lựa chọn' in line_stripped.lower():
                    skip_section = True
                continue
            
            if skip_section and (line_stripped.startswith('**') or line_stripped.startswith('>') or line_stripped == ''):
                continue
            
            if line_stripped and not line_stripped.startswith('**') and not line_stripped.startswith('>'):
                skip_section = False
                cleaned_lines.append(line)
            elif not skip_section:
                cleaned_lines.append(line)
        
        cleaned_result = '\n'.join(cleaned_lines).strip()
        if len(cleaned_result) > 1000:
            first_paragraph = cleaned_result.split('\n\n')[0]
            if len(first_paragraph) > 50:
                enhanced_desc = first_paragraph.strip()
            else:
                enhanced_desc = cleaned_result
        else:
            enhanced_desc = cleaned_result if cleaned_result else enhanced_desc
        
        enhanced_experience = experience.copy()
        enhanced_experience["description"] = enhanced_desc
        return enhanced_experience
    
    return experience

def enhance_skills_free(skills: List[str], experiences: Optional[List[Dict]] = None) -> Optional[List[str]]:
    """Cải thiện danh sách kỹ năng bằng API miễn phí"""
    if not skills:
        return skills
    
    skills_text = "\n".join(f"- {s}" for s in skills)
    
    system_prompt = """Bạn là chuyên gia CV. Nhiệm vụ của bạn là tối ưu hóa danh sách kỹ năng để trở nên chuyên nghiệp và ấn tượng hơn.
QUAN TRỌNG: Chỉ trả về danh sách kỹ năng đã được tối ưu hóa, KHÔNG có hướng dẫn, KHÔNG có giải thích."""
    
    user_prompt = f"""Cải thiện danh sách kỹ năng sau:
1. Loại bỏ kỹ năng trùng lặp hoặc tương tự
2. Sắp xếp theo mức độ quan trọng và liên quan
3. Nhóm các kỹ năng liên quan lại với nhau
4. Format chuyên nghiệp, dễ đọc

Danh sách kỹ năng gốc:
{skills_text}
"""
    
    if experiences:
        exp_text = "\n".join([f"- {exp.get('position', '')} tại {exp.get('company', '')}" for exp in experiences[:3]])
        user_prompt += f"\nKinh nghiệm tham khảo:\n{exp_text}"
    
    user_prompt += "\n\nChỉ trả về danh sách kỹ năng đã được tối ưu hóa (mỗi kỹ năng một dòng, không đánh số, không có ký tự đặc biệt ở đầu):"
    
    result = enhance_text_free(user_prompt, system_prompt)
    
    # Làm sạch kết quả
    if result:
        lines = result.split('\n')
        cleaned_skills = []
        
        for line in lines:
            line_stripped = line.strip()
            # Bỏ qua các dòng là hướng dẫn, giải thích
            if any(keyword in line_stripped.lower() for keyword in [
                'lựa chọn', '---', 'lưu ý', 'yêu cầu', 'tuyệt vời', 
                'dưới đây', 'hướng dẫn', 'chọn', 'lựa chọn phù hợp',
                'lưu ý khi chọn', 'đừng ngại', 'bạn có thể'
            ]):
                continue
            
            # Bỏ qua dòng trống, số, hoặc đánh số
            if not line_stripped or line_stripped.isdigit() or line_stripped.startswith('Lựa chọn'):
                continue
            
            # Lấy kỹ năng (loại bỏ bullet points, số thứ tự)
            skill = line_stripped.strip("-• 1234567890. ")
            if skill and len(skill) > 1:
                cleaned_skills.append(skill)
        
        return cleaned_skills if cleaned_skills else skills
    
    return skills

