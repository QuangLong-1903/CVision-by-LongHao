"""
AI Content Enhancer - Sử dụng AI để cải thiện nội dung CV
Hỗ trợ: OpenAI API (có phí), Google Gemini (FREE), Cohere (FREE tier), Hugging Face (FREE)
"""

import os
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

# Import free APIs
try:
    from app.utils.ai_enhancer_free import enhance_summary_free, enhance_experience_free, enhance_skills_free, enhance_text_free
    HAS_FREE_APIS = True
except ImportError:
    HAS_FREE_APIS = False
    logger.warning("Free AI APIs không khả dụng")

# Import OpenAI
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logger.warning("OpenAI module chưa được cài đặt")

def get_openai_client():
    """Khởi tạo OpenAI client"""
    if not HAS_OPENAI:
        return None
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        logger.error(f"Lỗi khởi tạo OpenAI client: {e}")
        return None

def get_ai_provider():
    """
    Xác định provider AI nào sẽ sử dụng
    Ưu tiên: OpenAI > Gemini > Cohere > Hugging Face
    """
    # Kiểm tra OpenAI
    if get_openai_client():
        return "openai"
    
    # Kiểm tra Gemini
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    
    # Kiểm tra Cohere
    if os.environ.get("COHERE_API_KEY"):
        return "cohere"
    
    # Kiểm tra Hugging Face
    if os.environ.get("HUGGINGFACE_API_KEY"):
        return "huggingface"
    
    return None

def enhance_summary_simple(summary: str) -> str:
    """
    Fallback method: Cải thiện văn bản đơn giản không cần AI
    Chỉ format và làm cho văn bản gọn gàng hơn
    """
    if not summary or not summary.strip():
        return summary
    
    # Loại bỏ khoảng trắng thừa
    text = " ".join(summary.split())
    
    # Đảm bảo câu đầu viết hoa
    if text and not text[0].isupper():
        text = text[0].upper() + text[1:]
    
    # Đảm bảo có dấu chấm cuối
    if text and text[-1] not in '.!?':
        text += '.'
    
    return text

def enhance_summary_with_ai(summary: str, job_title: Optional[str] = None) -> Optional[str]:
    """Cải thiện phần tóm tắt/mục tiêu nghề nghiệp bằng AI - biến văn bản nhàm chán thành thu hút và chuyên nghiệp"""
    if not summary or not summary.strip():
        logger.warning("Summary is empty, cannot enhance")
        return None

    # Prompt cải thiện để văn bản thu hút và chuyên nghiệp hơn
    system_prompt = """Bạn là chuyên gia viết CV. Nhiệm vụ của bạn là viết lại văn bản để trở nên thu hút và chuyên nghiệp hơn.
QUAN TRỌNG: Chỉ trả về văn bản đã được cải thiện, KHÔNG có hướng dẫn, KHÔNG có nhiều lựa chọn, KHÔNG có giải thích hay lưu ý.
Chỉ trả về văn bản cuối cùng đã được cải thiện."""

    user_prompt = f"""Viết lại phần tóm tắt sau để trở nên thu hút và chuyên nghiệp hơn. 
Giữ nguyên ý nghĩa và thông tin quan trọng. Sử dụng từ ngữ mạnh mẽ, tích cực. Tối đa 150 từ.

Nội dung gốc:
{summary}
"""

    if job_title:
        user_prompt += f"\nVị trí ứng tuyển: {job_title}\n"

    user_prompt += "\nChỉ trả về văn bản đã được cải thiện, không có hướng dẫn hay giải thích:"

    # Thử OpenAI trước
    client = get_openai_client()
    if client:
        try:
            logger.info(f"Đang cải thiện summary với OpenAI... (length: {len(summary)} chars)")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=250,
                temperature=0.8
            )
            enhanced = response.choices[0].message.content.strip()
            logger.info(f"✓ OpenAI đã cải thiện summary thành công (length: {len(enhanced)} chars)")
            return enhanced
        except Exception as e:
            logger.warning(f"OpenAI failed: {str(e)}, thử API miễn phí...")
    
    # Thử các API miễn phí
    if HAS_FREE_APIS:
        enhanced = enhance_summary_free(summary, job_title)
        if enhanced:
            logger.info(f"✓ Free API đã cải thiện summary thành công")
            return enhanced
    
    # Fallback: format đơn giản
    logger.warning("Không có AI API nào khả dụng. Sử dụng fallback method đơn giản.")
    return enhance_summary_simple(summary)


def enhance_experience_with_ai(experience: Dict) -> Optional[Dict]:
    """Cải thiện mô tả kinh nghiệm làm việc bằng AI - biến văn bản nhàm chán thành thu hút và chuyên nghiệp"""
    if not experience or not experience.get("description"):
        logger.warning("Experience description is empty, cannot enhance")
        return experience

    system_prompt = """Bạn là chuyên gia viết CV. Nhiệm vụ của bạn là viết lại mô tả công việc thành bullet points chuyên nghiệp.
QUAN TRỌNG: Chỉ trả về văn bản đã được cải thiện, KHÔNG có hướng dẫn, KHÔNG có nhiều lựa chọn, KHÔNG có giải thích hay lưu ý.
Chỉ trả về văn bản cuối cùng đã được cải thiện."""

    user_prompt = f"""Viết lại mô tả công việc sau thành 3-5 bullet points chuyên nghiệp.
Sử dụng động từ hành động mạnh mẽ. Thêm số liệu cụ thể nếu có thể.

Vị trí: {experience.get('position', 'N/A')}
Công ty: {experience.get('company', 'N/A')}
Mô tả gốc:
{experience.get('description', '')}
"""

    achievements = experience.get("achievements", [])
    if achievements:
        user_prompt += "\nThành tựu đạt được:\n" + "\n".join(f"- {a}" for a in achievements)

    user_prompt += "\nChỉ trả về văn bản đã được cải thiện, không có hướng dẫn hay giải thích:"

    # Thử OpenAI trước
    client = get_openai_client()
    if client:
        try:
            logger.info(f"Đang cải thiện experience với OpenAI... (position: {experience.get('position', 'N/A')})")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=400,
                temperature=0.8
            )
            enhanced_desc = response.choices[0].message.content.strip()
            
            # Làm sạch kết quả: loại bỏ hướng dẫn, lựa chọn, giải thích
            enhanced_desc = _clean_ai_response(enhanced_desc)
            
            enhanced_points = [line.strip("-• ").strip() for line in enhanced_desc.split("\n") if line.strip()]

            enhanced_experience = experience.copy()
            enhanced_experience["description"] = enhanced_desc
            enhanced_experience["enhanced_points"] = enhanced_points

            logger.info(f"✓ OpenAI đã cải thiện experience thành công cho vị trí: {experience.get('position', 'N/A')}")
            return enhanced_experience
        except Exception as e:
            logger.warning(f"OpenAI failed: {str(e)}, thử API miễn phí...")
    
    # Thử các API miễn phí
    if HAS_FREE_APIS:
        enhanced = enhance_experience_free(experience)
        if enhanced and enhanced != experience:
            logger.info(f"✓ Free API đã cải thiện experience thành công")
            return enhanced
    
    # Trả về bản gốc nếu không có AI
    logger.warning("Không có AI API nào khả dụng")
    return experience


def enhance_skills_with_ai(skills: List[str], experiences: Optional[List[Dict]] = None) -> Optional[List[str]]:
    """Cải thiện danh sách kỹ năng bằng AI - sắp xếp và tối ưu hóa"""
    if not skills:
        logger.warning("Skills list is empty, cannot enhance")
        return []

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

    user_prompt += "\nChỉ trả về danh sách kỹ năng đã được tối ưu hóa (mỗi kỹ năng một dòng, không đánh số, không có ký tự đặc biệt ở đầu):"

    # Thử OpenAI trước
    client = get_openai_client()
    if client:
        try:
            logger.info(f"Đang cải thiện skills với OpenAI... (count: {len(skills)})")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.6
            )
            enhanced_text = response.choices[0].message.content.strip()
            
            # Làm sạch kết quả: loại bỏ hướng dẫn, lựa chọn, giải thích
            enhanced_text = _clean_ai_response(enhanced_text)
            
            enhanced_skills = [line.strip("-• ").strip() for line in enhanced_text.split("\n") 
                             if line.strip() and not line.strip().isdigit() 
                             and not any(keyword in line.lower() for keyword in [
                                 'lựa chọn', 'tuyệt vời', 'dưới đây', 'lưu ý', 
                                 'yêu cầu', 'hướng dẫn', 'chọn', '---'
                             ])]
            logger.info(f"✓ OpenAI đã cải thiện skills thành công (count: {len(enhanced_skills)})")
            return enhanced_skills if enhanced_skills else skills
        except Exception as e:
            logger.warning(f"OpenAI failed: {str(e)}, thử API miễn phí...")
    
    if HAS_FREE_APIS:
        enhanced = enhance_skills_free(skills, experiences)
        if enhanced and enhanced != skills:
            logger.info(f"✓ Free API đã cải thiện skills thành công")
            return enhanced
    
    logger.warning("Không có AI API nào khả dụng cho skills")
    return skills

def _clean_ai_response(text: str) -> str:
    """
    Làm sạch kết quả từ AI: loại bỏ hướng dẫn, lựa chọn, giải thích
    """
    if not text:
        return text
    
    lines = text.split('\n')
    cleaned_lines = []
    skip_section = False
    
    for line in lines:
        line_stripped = line.strip()
        
        if any(keyword in line_stripped.lower() for keyword in [
            'lựa chọn', '---', 'lưu ý', 'yêu cầu', 'tuyệt vời', 
            'dưới đây', 'hướng dẫn', 'chọn', 'lựa chọn phù hợp',
            'lưu ý khi chọn', 'đừng ngại', 'bạn có thể'
        ]):
            if 'lựa chọn' in line_stripped.lower():
                skip_section = True
            continue
        
        if skip_section and (line_stripped.startswith('**') or line_stripped.startswith('>') or line_stripped == ''):
            continue
        
        if line_stripped and (line_stripped.isdigit() or line_stripped.startswith('Lựa chọn')):
            continue
        
        if line_stripped and not line_stripped.startswith('**') and not line_stripped.startswith('>'):
            skip_section = False
            cleaned_lines.append(line)
        elif not skip_section:
            cleaned_lines.append(line)
    
    cleaned_result = '\n'.join(cleaned_lines).strip()
    
    if len(cleaned_result) > 500:
        first_paragraph = cleaned_result.split('\n\n')[0]
        if len(first_paragraph) > 50:
            return first_paragraph.strip()
    
    return cleaned_result if cleaned_result else text

def enhance_full_cv_with_ai(cv_data: Dict) -> Dict:
    """Cải thiện toàn bộ CV với AI"""
    enhanced_cv = cv_data.copy()

    if cv_data.get("summary"):
        enhanced_summary = enhance_summary_with_ai(
            cv_data["summary"],
            cv_data.get("experiences", [{}])[0].get("position") if cv_data.get("experiences") else None
        )
        if enhanced_summary:
            enhanced_cv["ai_enhanced_summary"] = enhanced_summary

    if cv_data.get("experiences"):
        enhanced_experiences = []
        for exp in cv_data["experiences"]:
            enhanced_experiences.append(enhance_experience_with_ai(exp))
        enhanced_cv["ai_enhanced_experiences"] = enhanced_experiences

    if cv_data.get("skills"):
        enhanced_skills = enhance_skills_with_ai(cv_data["skills"], cv_data.get("experiences"))
        if enhanced_skills:
            enhanced_cv["ai_enhanced_skills"] = enhanced_skills

    return enhanced_cv

def evaluate_cv_match_with_job(cv_text: str, job_title: str, job_description: str, job_requirements: Optional[str] = None) -> Optional[float]:
    """
    Đánh giá độ phù hợp giữa CV và job posting bằng AI
    Trả về match score từ 0.0 đến 1.0
    """
    if not cv_text or not job_title:
        logger.warning("CV text or job title is empty, cannot evaluate")
        return None
    
    system_prompt = """Bạn là chuyên gia tuyển dụng. Nhiệm vụ của bạn là đánh giá độ phù hợp giữa CV và vị trí tuyển dụng.
QUAN TRỌNG: Chỉ trả về một số từ 0.0 đến 1.0 (ví dụ: 0.85), KHÔNG có giải thích, KHÔNG có văn bản khác.
0.0 = hoàn toàn không phù hợp
1.0 = hoàn toàn phù hợp"""
    
    job_info = f"Vị trí: {job_title}\n"
    if job_description:
        job_info += f"Mô tả công việc: {job_description[:500]}\n"  # Giới hạn độ dài
    if job_requirements:
        job_info += f"Yêu cầu: {job_requirements[:500]}\n"
    
    user_prompt = f"""Đánh giá độ phù hợp giữa CV và vị trí tuyển dụng sau dựa trên các tiêu chí:

1. **Kỹ năng (Skills)**: CV có các kỹ năng cần thiết cho vị trí không? (30%)
2. **Kinh nghiệm (Experience)**: Kinh nghiệm làm việc có phù hợp với yêu cầu không? (30%)
3. **Trình độ học vấn (Education)**: Trình độ học vấn có đáp ứng yêu cầu không? (15%)
4. **Mô tả công việc (Job Description Match)**: CV có thể hiện hiểu biết về công việc không? (15%)
5. **Yêu cầu đặc biệt (Special Requirements)**: Có đáp ứng các yêu cầu đặc biệt (ngoại ngữ, chứng chỉ, v.v.) không? (10%)

Đánh giá tổng thể từ 0.0 (hoàn toàn không phù hợp) đến 1.0 (hoàn toàn phù hợp).

Thông tin vị trí tuyển dụng:
{job_info}

Nội dung CV (rút gọn):
{cv_text[:2000]}

Chỉ trả về một số từ 0.0 đến 1.0 (ví dụ: 0.85), không có giải thích:"""
    
    # Thử OpenAI trước
    client = get_openai_client()
    if client:
        try:
            logger.info(f"Đang đánh giá CV với job '{job_title}' bằng OpenAI...")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=50,
                temperature=0.3
            )
            result_text = response.choices[0].message.content.strip()
            
            # Parse số từ kết quả
            try:
                import re
                # Tìm số đầu tiên trong kết quả (có thể là 0.85 hoặc 85%)
                numbers = re.findall(r'\d+\.?\d*', result_text)
                if numbers:
                    score = float(numbers[0])
                    # Nếu số > 1, có thể là phần trăm (ví dụ: 85), chia cho 100
                    if score > 1.0:
                        score = score / 100.0
                    # Đảm bảo score trong khoảng 0.0-1.0
                    score = max(0.0, min(1.0, score))
                    logger.info(f"✓ OpenAI đánh giá CV: {score:.2f}")
                    return score
                else:
                    logger.warning(f"Không tìm thấy số trong OpenAI response: {result_text}")
            except (ValueError, IndexError) as e:
                logger.warning(f"Không thể parse score từ OpenAI response: {result_text}, error: {str(e)}")
        except Exception as e:
            logger.warning(f"OpenAI failed: {str(e)}")
    
    # Fallback: tính toán đơn giản dựa trên keyword matching
    logger.warning("Không có AI API khả dụng, sử dụng fallback method")
    return None
    