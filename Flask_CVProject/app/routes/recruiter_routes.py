"""
Routes cho nhà tuyển dụng
- Đăng bài tuyển dụng
- Xem danh sách CV ứng tuyển
- Xem top CV theo category
- Dashboard thống kê
"""

import os
import logging
import re
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import User, JobPosting, JobApplication, CV, JobCategory, ClassificationLog
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone, time, timedelta
from sqlalchemy import func, desc, and_, or_
from app.utils.ai_enhancer import evaluate_cv_match_with_job
from app.utils.text_extractor import extract_text_from_file

logger = logging.getLogger(__name__)

recruiter_bp = Blueprint("recruiter", __name__)

# Đường dẫn base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Flask_CVProject/app

# Thư mục lưu logo công ty
LOGO_UPLOAD_FOLDER = os.path.join('Flask_CVProject', 'app', 'static', 'uploads', 'company_logos')
ALLOWED_LOGO_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'}

def allowed_logo_file(filename):
    """Kiểm tra file có phải là logo hợp lệ không"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_LOGO_EXTENSIONS

def save_company_logo(file, job_id):
    """Lưu logo công ty và trả về đường dẫn"""
    if not file or file.filename == '':
        return None
    
    if not allowed_logo_file(file.filename):
        raise ValueError('Định dạng file không được hỗ trợ. Chỉ chấp nhận: JPG, JPEG, PNG, GIF, WEBP, SVG')
    
    # Tạo tên file an toàn với job_id để tránh trùng lặp
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f'logo_{job_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{file_ext}'
    filename = secure_filename(filename)
    
    # Tạo thư mục nếu chưa có
    os.makedirs(LOGO_UPLOAD_FOLDER, exist_ok=True)
    
    # Lưu file
    file_path = os.path.join(LOGO_UPLOAD_FOLDER, filename)
    file.save(file_path)
    
    # Trả về đường dẫn relative để lưu vào database
    return f'/static/uploads/company_logos/{filename}'

def safe_decode_text(text):
    """
    An toàn decode text từ database, đảm bảo UTF-8
    Xử lý cả trường hợp dữ liệu đã bị lưu sai encoding
    """
    if text is None:
        return None
    
    # Nếu là bytes, decode về string
    if isinstance(text, bytes):
        # Thử các encoding phổ biến
        encodings = ['utf-8', 'cp1252', 'latin-1', 'iso-8859-1', 'windows-1252']
        for encoding in encodings:
            try:
                decoded = text.decode(encoding)
                # Kiểm tra xem có ký tự không hợp lệ không
                if '\ufffd' not in decoded:
                    return decoded
            except (UnicodeDecodeError, UnicodeError):
                continue
        # Cuối cùng, ignore errors
        return text.decode('utf-8', errors='replace').replace('\ufffd', '')
    
    # Nếu đã là string
    if isinstance(text, str):
        # Kiểm tra xem string có phải là UTF-8 hợp lệ không
        try:
            # Thử encode/decode để kiểm tra
            text.encode('utf-8').decode('utf-8')
            # Nếu có ký tự replacement (\ufffd), có thể đã bị decode sai
            if '\ufffd' in text:
                # Có thể cần decode lại từ bytes gốc
                # Nhưng không có bytes gốc, nên chỉ có thể fix một phần
                pass
            return text
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            # String không phải UTF-8 hợp lệ
            # Có thể đã bị double encoding hoặc encoding sai
            try:
                # Thử decode lại: encode với latin-1 rồi decode với utf-8
                # (để fix double encoding)
                fixed = text.encode('latin-1', errors='ignore').decode('utf-8', errors='replace')
                return fixed.replace('\ufffd', '')
            except Exception:
                # Cuối cùng, chỉ loại bỏ ký tự không hợp lệ
                try:
                    return text.encode('utf-8', errors='replace').decode('utf-8').replace('\ufffd', '')
                except Exception:
                    return text
    
    # Nếu không phải string hay bytes, convert sang string
    try:
        return str(text)
    except Exception:
        return ''

def fix_common_vietnamese_errors(text):
    """
    Cố gắng sửa một số lỗi encoding phổ biến trong tiếng Việt
    Dựa trên pattern: ký tự có dấu bị thay bằng ? hoặc bị sai
    """
    if not text or not isinstance(text, str):
        return text
    
    try:
        # Sắp xếp các pattern theo độ dài giảm dần để fix cụm từ dài trước
        # Mapping các từ/cụm từ bị lỗi phổ biến
        word_fixes = [
            # FIX LỖI "TÀI X?" → "TÀI XẾ" (ưu tiên cao nhất)
            (r'TÀI X\? XE', 'TÀI XẾ XE'),
            (r'Tài x\? xe', 'Tài xế xe'),
            (r'tài x\? xe', 'tài xế xe'),
            (r'TÀI X\?', 'TÀI XẾ'),
            (r'Tài x\?', 'Tài xế'),
            (r'tài x\?', 'tài xế'),
            (r'X\? XE', 'XẾ XE'),
            (r'x\? xe', 'xế xe'),
            # Các cụm từ dài trước - FIX LỖI "Mứng Du lựch"
            (r'Mứng Du lựch', 'Mùa Du lịch'),
            (r'Mứng Du lịch', 'Mùa Du lịch'),
            (r'Mùa Du lựch', 'Mùa Du lịch'),
            (r'Mứng', 'Mùa'),
            (r'Du lựch', 'Du lịch'),
            (r'cham sóc', 'chăm sóc'),
            (r'cham', 'chăm'),
            # Các cụm từ khác
            (r'Ti\?p Th\?', 'Tiếp Thị'),
            (r'Giị thi\?u', 'Giới thiệu'),
            (r'sốn phầm mị', 'sản phẩm mới'),
            (r'cếp Quận lý', 'cấp Quản lý'),
            (r'Ch\? d\?ng', 'Chủ động'),
            (r'Thị tru\?ng', 'Thị trường'),
            (r'dậy m\?nh', 'đẩy mạnh'),
            (r'm\? r\?ng', 'mở rộng'),
            (r'H\? Chí Minh', 'Hồ Chí Minh'),
            (r'ph\? cếp', 'phụ cấp'),
            (r'kất qu\?', 'kết quả'),
            (r'Thu\?ng xuyên', 'Thường xuyên'),
            (r'khuyận mị', 'khuyến mãi'),
            (r'chuong trình', 'chương trình'),
            (r'Thịc hiện', 'Thực hiện'),
            (r'ch\? tiêu', 'chỉ tiêu'),
            (r'tìm hi\?u', 'tìm hiểu'),
            (r'phát triận', 'phát triển'),
            (r'ph\?t tri\?n', 'phát triển'),
            (r'đ\?i h\?c', 'đại học'),
            (r'cao đ\?ng', 'cao đẳng'),
            (r'trung c\?p', 'trung cấp'),
            (r's\?n sàng', 'sẵn sàng'),
            (r'ch\?u áp l\?c', 'chịu áp lực'),
            (r'linh ho\?t', 'linh hoạt'),
            (r'đ\?c l\?p', 'độc lập'),
            (r'c\?i ti\?n', 'cải tiến'),
            (r'kinh nghi\?m', 'kinh nghiệm'),
            (r'b\?ng c\?p', 'bằng cấp'),
            (r'k\? n\?ng', 'kỹ năng'),
            (r'\?ng d\?ng', 'ứng dụng'),
            (r'thành th\?o', 'thành thạo'),
            (r'c\?n thi\?t', 'cần thiết'),
            (r'kh\? n\?ng', 'khả năng'),
            (r'giao ti\?p', 'giao tiếp'),
            (r'làm vi\?c', 'làm việc'),
            (r'đ\?i ngũ', 'đội ngũ'),
            (r'chuyên nghi\?p', 'chuyên nghiệp'),
            (r'c\?ng vi\?c', 'công việc'),
            (r'ph\?m ch\?t', 'phẩm chất'),
            (r'đ\?o đ\?c', 'đạo đức'),
            (r't\?t nghi\?p', 'tốt nghiệp'),
            # Các từ đơn
            (r'Ti\?p', 'Tiếp'),
            (r'Th\?', 'Thị'),
            (r'sốn phầm', 'sản phẩm'),
            (r'c\?a', 'của'),
            (r'dận', 'dẫn'),
            (r'Thiất lếp', 'Thiết lập'),
            (r'tất mị', 'tốt mối'),
            (r'v\?', 'với'),
            (r'cham sóc', 'chăm sóc'),
            (r'cếp nhất', 'cập nhật'),
            (r'v\?', 'về'),
            (r'thu\?ng', 'thưởng'),
            (r'duức', 'được'),
            (r'công viức', 'công việc'),
        ]
        
        # Áp dụng các fix
        for pattern, replacement in word_fixes:
            try:
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            except re.error as e:
                logger.warning(f"Regex error with pattern {pattern}: {str(e)}")
                continue
        
        # Sửa các lỗi đặc biệt (không có ?)
        special_fixes = [
            (r'Giị', 'Giới'),
            (r'phầm', 'phẩm'),
            (r'Thiất', 'Thiết'),
            (r'lếp', 'lập'),
            (r'mị', 'mối'),
            (r'khuyận', 'khuyến'),
            (r'chuong', 'chương'),
            (r'Thịc', 'Thực'),
            (r'duức', 'được'),
            (r'kất', 'kết'),
            (r'viức', 'việc'),
            (r'kiận', 'kiến'),
            (r'cếp', 'cấp'),
            (r'Quận', 'Quản'),
            (r'dậy', 'đẩy'),
            (r'triận', 'triển'),
        ]
        
        # Áp dụng các fix đặc biệt
        for pattern, replacement in special_fixes:
            try:
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            except re.error as e:
                logger.warning(f"Regex error with pattern {pattern}: {str(e)}")
                continue
        
    except Exception as e:
        logger.error(f"Error in fix_common_vietnamese_errors: {str(e)}")
        return text
    
    return text

def check_recruiter_role():
    """Kiểm tra user có phải recruiter không"""
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
    user = User.query.get(user_id)
    if not user or user.role != 'recruiter':
        return None
    return user

# ============= HTML Pages =============
@recruiter_bp.route('/recruiter/jobs', methods=['GET'])
def jobs_page():
    """Trang danh sách bài đăng tuyển dụng"""
    return render_template('recruiter/jobs.html')

@recruiter_bp.route('/recruiter/jobs/new', methods=['GET'])
def new_job_page():
    """Trang tạo bài đăng tuyển dụng mới"""
    return render_template('recruiter/new_job.html')

@recruiter_bp.route('/recruiter/jobs/<int:job_id>', methods=['GET'])
def job_detail_page(job_id):
    """Trang chi tiết bài đăng tuyển dụng"""
    return render_template('recruiter/job_detail.html', job_id=job_id)

@recruiter_bp.route('/recruiter/jobs/<int:job_id>/edit', methods=['GET'])
def edit_job_page(job_id):
    """Trang chỉnh sửa bài đăng tuyển dụng"""
    return render_template('recruiter/edit_job.html', job_id=job_id)

@recruiter_bp.route('/recruiter/applications', methods=['GET'])
def applications_page():
    """Trang danh sách CV ứng tuyển"""
    return render_template('recruiter/applications.html')

@recruiter_bp.route('/recruiter/dashboard', methods=['GET'])
def recruiter_dashboard():
    """Trang dashboard thống kê cho nhà tuyển dụng"""
    return render_template('recruiter/dashboard.html')

# ============= API Endpoints =============

@recruiter_bp.route('/api/recruiter/jobs', methods=['GET'])
@jwt_required()
def get_jobs():
    """API lấy danh sách bài đăng tuyển dụng của recruiter"""
    try:
        user = check_recruiter_role()
        if not user:
            return jsonify({'success': False, 'message': 'Chỉ nhà tuyển dụng mới có quyền truy cập'}), 403
        
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        search = request.args.get('search', '').strip()
        category_id = request.args.get('category_id', type=int)
        location = request.args.get('location', '').strip()
        employment_type = request.args.get('employment_type', '').strip()
        
        # Sử dụng raw SQL để tránh lỗi decode tự động của SQLAlchemy
        # Đọc dữ liệu trực tiếp từ database và decode thủ công
        jobs = []
        total_count = 0
        try:
            # Thử dùng ORM trước với pagination và filters
            query = JobPosting.query.filter_by(recruiter_id=user.id)
            
            # Filter by search (title, description)
            if search:
                query = query.filter(
                    or_(
                        JobPosting.title.ilike(f'%{search}%'),
                        JobPosting.description.ilike(f'%{search}%')
                    )
                )
            
            # Filter by category
            if category_id:
                query = query.filter_by(category_id=category_id)
            
            # Filter by location
            if location:
                query = query.filter(JobPosting.location.ilike(f'%{location}%'))
            
            # Filter by employment type
            if employment_type:
                query = query.filter_by(employment_type=employment_type)
            
            # Sort by created_at (newest first)
            query = query.order_by(desc(JobPosting.created_at))
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            jobs = pagination.items
            total_count = pagination.total
        except (UnicodeDecodeError, UnicodeError, Exception) as e:
            logger.warning(f"Lỗi khi đọc jobs với ORM: {str(e)}, thử raw SQL...")
            # Fallback: dùng raw SQL với text() để tránh SQLAlchemy tự động decode
            from sqlalchemy import text
            sql = text("""
                SELECT id, title, description, location, salary_min, salary_max, 
                       category_id, employment_type, is_active, deadline, created_at, company_logo
                FROM job_postings
                WHERE recruiter_id = :recruiter_id
                ORDER BY created_at DESC
            """)
            result = db.session.execute(sql, {'recruiter_id': user.id})
            
            # Tạo class để giả lập JobPosting object
            class JobRow:
                def __init__(self, row_data):
                    self.id = row_data[0]
                    # Decode thủ công với error handling
                    try:
                        self.title = row_data[1] if row_data[1] else None
                        if isinstance(self.title, bytes):
                            self.title = self.title.decode('cp1252', errors='replace')
                    except:
                        self.title = str(row_data[1]) if row_data[1] else None
                    
                    try:
                        self.description = row_data[2] if row_data[2] else None
                        if isinstance(self.description, bytes):
                            self.description = self.description.decode('cp1252', errors='replace')
                    except:
                        self.description = str(row_data[2]) if row_data[2] else None
                    
                    try:
                        self.location = row_data[3] if row_data[3] else None
                        if isinstance(self.location, bytes):
                            self.location = self.location.decode('cp1252', errors='replace')
                    except:
                        self.location = str(row_data[3]) if row_data[3] else None
                    
                    self.salary_min = row_data[4]
                    self.salary_max = row_data[5]
                    self.category_id = row_data[6]
                    
                    try:
                        self.employment_type = row_data[7] if row_data[7] else None
                        if isinstance(self.employment_type, bytes):
                            self.employment_type = self.employment_type.decode('cp1252', errors='replace')
                    except:
                        self.employment_type = str(row_data[7]) if row_data[7] else None
                    
                    self.is_active = row_data[8]
                    self.deadline = row_data[9]
                    self.created_at = row_data[10]
                    self.company_logo = row_data[11] if len(row_data) > 11 else None
                    self.category = None  # Sẽ load sau nếu cần
            
            for row in result:
                jobs.append(JobRow(row))
        
        jobs_list = []
        for job in jobs:
            try:
                # Đếm số lượng ứng viên
                application_count = JobApplication.query.filter_by(job_posting_id=job.id).count()
                
                # Đảm bảo encoding đúng cho các trường text - bọc cả việc truy cập attribute
                # Vì SQLAlchemy có thể tự động decode khi truy cập attribute
                title = None
                description = None
                location = None
                category_name = None
                
                # Truy cập title với error handling
                try:
                    raw_title = getattr(job, 'title', None)
                    if raw_title:
                        title = safe_decode_text(raw_title)
                except (UnicodeDecodeError, UnicodeError, AttributeError, Exception) as e:
                    logger.warning(f"Error accessing/decoding job.title for job {job.id}: {str(e)}")
                    try:
                        # Thử lấy raw value và decode thủ công
                        raw_title = getattr(job, 'title', None)
                        if raw_title:
                            if isinstance(raw_title, bytes):
                                title = raw_title.decode('cp1252', errors='replace')
                            else:
                                title = str(raw_title)
                    except:
                        title = None
                
                # Truy cập description với error handling
                try:
                    raw_description = getattr(job, 'description', None)
                    if raw_description:
                        description = safe_decode_text(raw_description)
                except (UnicodeDecodeError, UnicodeError, AttributeError, Exception) as e:
                    logger.warning(f"Error accessing/decoding job.description for job {job.id}: {str(e)}")
                    try:
                        raw_description = getattr(job, 'description', None)
                        if raw_description:
                            if isinstance(raw_description, bytes):
                                description = raw_description.decode('cp1252', errors='replace')
                            else:
                                description = str(raw_description)
                    except:
                        description = None
                
                # Truy cập location với error handling
                try:
                    raw_location = getattr(job, 'location', None)
                    if raw_location:
                        location = safe_decode_text(raw_location)
                except (UnicodeDecodeError, UnicodeError, AttributeError, Exception) as e:
                    logger.warning(f"Error accessing/decoding job.location for job {job.id}: {str(e)}")
                    try:
                        raw_location = getattr(job, 'location', None)
                        if raw_location:
                            if isinstance(raw_location, bytes):
                                location = raw_location.decode('cp1252', errors='replace')
                            else:
                                location = str(raw_location)
                    except:
                        location = None
                
                # Truy cập category name với error handling
                try:
                    if job.category:
                        raw_category_name = getattr(job.category, 'name', None)
                        if raw_category_name:
                            category_name = safe_decode_text(raw_category_name)
                except (UnicodeDecodeError, UnicodeError, AttributeError, Exception) as e:
                    logger.warning(f"Error accessing/decoding category.name for job {job.id}: {str(e)}")
                    try:
                        if job.category:
                            raw_category_name = getattr(job.category, 'name', None)
                            if raw_category_name:
                                if isinstance(raw_category_name, bytes):
                                    category_name = raw_category_name.decode('cp1252', errors='replace')
                                else:
                                    category_name = str(raw_category_name)
                    except:
                        category_name = None
                
                # Cố gắng fix các lỗi encoding phổ biến
                title = fix_common_vietnamese_errors(title) if title else None
                description = fix_common_vietnamese_errors(description) if description else None
                location = fix_common_vietnamese_errors(location) if location else None
            except Exception as e:
                logger.error(f"Error processing job {job.id}: {str(e)}", exc_info=True)
                # Skip job này nếu có lỗi nghiêm trọng
                continue
            
            # Truncate description nếu cần
            if description and len(description) > 200:
                description = description[:200] + '...'
            
            jobs_list.append({
                'id': job.id,
                'title': title,
                'description': description,
                'location': location,
                'category': category_name,
                'category_id': job.category_id,
                'is_active': job.is_active,
                'application_count': application_count,
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'deadline': job.deadline.isoformat() if job.deadline else None,
                'company_logo': getattr(job, 'company_logo', None) if hasattr(job, 'company_logo') else None
            })
        
        return jsonify({
            'success': True,
            'jobs': jobs_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count if total_count > 0 else len(jobs_list),
                'pages': (total_count + per_page - 1) // per_page if total_count > 0 else 1
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting jobs: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi tải danh sách bài đăng: {str(e)}'
        }), 500

@recruiter_bp.route('/api/recruiter/statistics', methods=['GET'])
@jwt_required()
def get_recruiter_statistics():
    """API lấy thống kê cho nhà tuyển dụng"""
    try:
        user = check_recruiter_role()
        if not user:
            return jsonify({'success': False, 'message': 'Chỉ nhà tuyển dụng mới có quyền truy cập'}), 403
        
        # Thống kê bài đăng
        total_jobs = JobPosting.query.filter_by(recruiter_id=user.id).count()
        active_jobs = JobPosting.query.filter_by(recruiter_id=user.id, is_active=True).count()
        inactive_jobs = JobPosting.query.filter_by(recruiter_id=user.id, is_active=False).count()
        
        # Thống kê ứng viên ứng tuyển
        total_applications = JobApplication.query.join(JobPosting).filter(
            JobPosting.recruiter_id == user.id
        ).count()
        
        # Thống kê theo trạng thái
        status_counts = {
            'pending': 0,
            'reviewed': 0,
            'shortlisted': 0,
            'rejected': 0,
            'hired': 0
        }
        
        applications = JobApplication.query.join(JobPosting).filter(
            JobPosting.recruiter_id == user.id
        ).all()
        
        for app in applications:
            if app.status in status_counts:
                status_counts[app.status] += 1
        
        # Thống kê CV theo category
        cv_by_category = db.session.query(
            JobCategory.name,
            func.count(JobApplication.id).label('count')
        ).join(
            CV, CV.predicted_category_id == JobCategory.id
        ).join(
            JobApplication, JobApplication.cv_id == CV.id
        ).join(
            JobPosting, JobApplication.job_posting_id == JobPosting.id
        ).filter(
            JobPosting.recruiter_id == user.id
        ).group_by(JobCategory.name).all()
        
        category_data = []
        for name, count in cv_by_category:
            try:
                decoded_name = safe_decode_text(name) if name else 'Chưa phân loại'
            except:
                decoded_name = str(name) if name else 'Chưa phân loại'
            category_data.append({'name': decoded_name, 'count': count})
        
        # Top job có nhiều ứng viên nhất
        top_jobs = db.session.query(
            JobPosting.id,
            JobPosting.title,
            func.count(JobApplication.id).label('application_count')
        ).outerjoin(
            JobApplication, JobPosting.id == JobApplication.job_posting_id
        ).filter(
            JobPosting.recruiter_id == user.id
        ).group_by(JobPosting.id, JobPosting.title).order_by(
            desc('application_count')
        ).limit(10).all()
        
        top_jobs_data = []
        for job in top_jobs:
            try:
                title = safe_decode_text(job.title) if job.title else 'Chưa có tiêu đề'
            except:
                title = str(job.title) if job.title else 'Chưa có tiêu đề'
            top_jobs_data.append({
                'id': job.id,
                'title': title,
                'count': job.application_count
            })
        
        # Xu hướng theo thời gian (30 ngày qua)
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)
        
        # Xu hướng bài đăng mới
        jobs_trend = []
        for i in range(30):
            date = now - timedelta(days=29-i)
            date_start = datetime.combine(date.date(), datetime.min.time())
            date_end = datetime.combine(date.date(), datetime.max.time())
            
            jobs_count = JobPosting.query.filter(
                and_(
                    JobPosting.recruiter_id == user.id,
                    JobPosting.created_at >= date_start,
                    JobPosting.created_at <= date_end
                )
            ).count()
            
            jobs_trend.append({
                'date': date.date().isoformat(),
                'count': jobs_count
            })
        
        # Xu hướng CV ứng tuyển mới
        applications_trend = []
        for i in range(30):
            date = now - timedelta(days=29-i)
            date_start = datetime.combine(date.date(), datetime.min.time())
            date_end = datetime.combine(date.date(), datetime.max.time())
            
            apps_count = JobApplication.query.join(JobPosting).filter(
                and_(
                    JobPosting.recruiter_id == user.id,
                    JobApplication.applied_at >= date_start,
                    JobApplication.applied_at <= date_end
                )
            ).count()
            
            applications_trend.append({
                'date': date.date().isoformat(),
                'count': apps_count
            })
        
        # Thống kê 7 ngày và 30 ngày qua
        seven_days_ago = now - timedelta(days=7)
        
        jobs_last_7_days = JobPosting.query.filter(
            and_(
                JobPosting.recruiter_id == user.id,
                JobPosting.created_at >= seven_days_ago
            )
        ).count()
        
        jobs_last_30_days = JobPosting.query.filter(
            and_(
                JobPosting.recruiter_id == user.id,
                JobPosting.created_at >= thirty_days_ago
            )
        ).count()
        
        applications_last_7_days = JobApplication.query.join(JobPosting).filter(
            and_(
                JobPosting.recruiter_id == user.id,
                JobApplication.applied_at >= seven_days_ago
            )
        ).count()
        
        applications_last_30_days = JobApplication.query.join(JobPosting).filter(
            and_(
                JobPosting.recruiter_id == user.id,
                JobApplication.applied_at >= thirty_days_ago
            )
        ).count()
        
        return jsonify({
            'success': True,
            'statistics': {
                'jobs': {
                    'total': total_jobs,
                    'active': active_jobs,
                    'inactive': inactive_jobs,
                    'last_7_days': jobs_last_7_days,
                    'last_30_days': jobs_last_30_days
                },
                'applications': {
                    'total': total_applications,
                    'by_status': status_counts,
                    'last_7_days': applications_last_7_days,
                    'last_30_days': applications_last_30_days
                },
                'cv_by_category': category_data,
                'top_jobs': top_jobs_data,
                'trends': {
                    'jobs': jobs_trend,
                    'applications': applications_trend
                }
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting recruiter statistics: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi tải thống kê: {str(e)}'
        }), 500

@recruiter_bp.route('/api/recruiter/jobs/<int:job_id>', methods=['GET'])
@jwt_required()
def get_job_detail(job_id):
    """API lấy chi tiết bài đăng tuyển dụng của recruiter"""
    try:
        user = check_recruiter_role()
        if not user:
            return jsonify({'success': False, 'message': 'Chỉ nhà tuyển dụng mới có quyền truy cập'}), 403
        
        job = JobPosting.query.get_or_404(job_id)
        
        # Kiểm tra job thuộc về recruiter này
        if job.recruiter_id != user.id:
            return jsonify({'success': False, 'message': 'Bạn không có quyền truy cập bài đăng này'}), 403
        
        # Decode text fields
        title = safe_decode_text(job.title) if job.title else None
        description = safe_decode_text(job.description) if job.description else None
        requirements = safe_decode_text(job.requirements) if job.requirements else None
        location = safe_decode_text(job.location) if job.location else None
        category_name = safe_decode_text(job.category.name) if job.category and job.category.name else None
        employment_type = safe_decode_text(job.employment_type) if job.employment_type else None
        
        return jsonify({
            'success': True,
            'job': {
                'id': job.id,
                'title': title,
                'description': description,
                'requirements': requirements,
                'location': location,
                'salary_min': float(job.salary_min) if job.salary_min else None,
                'salary_max': float(job.salary_max) if job.salary_max else None,
                'category_id': job.category_id,
                'category_name': category_name,
                'employment_type': employment_type,
                'is_active': job.is_active,
                'deadline': job.deadline.isoformat() if job.deadline else None,
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'company_logo': getattr(job, 'company_logo', None) if hasattr(job, 'company_logo') else None
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting job detail: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi tải chi tiết bài đăng: {str(e)}'
        }), 500

@recruiter_bp.route('/api/recruiter/jobs', methods=['POST'])
@jwt_required()
def create_job():
    """API tạo bài đăng tuyển dụng mới"""
    try:
        user = check_recruiter_role()
        if not user:
            return jsonify({'success': False, 'message': 'Chỉ nhà tuyển dụng mới có quyền truy cập'}), 403
        
        # Nhận dữ liệu từ form-data hoặc JSON
        data = {}
        if request.is_json:
            data = request.get_json()
        else:
            data = {
                'title': request.form.get('title'),
                'description': request.form.get('description'),
                'requirements': request.form.get('requirements'),
                'location': request.form.get('location'),
                'category_id': request.form.get('category_id'),
                'salary_min': request.form.get('salary_min'),
                'salary_max': request.form.get('salary_max'),
                'employment_type': request.form.get('employment_type'),
                'deadline': request.form.get('deadline'),
                'is_active': request.form.get('is_active', 'true').lower() == 'true'
            }
            
            # Validate và convert
            if data.get('category_id'):
                try:
                    category_id = int(data['category_id']) if data['category_id'] else None
                    if category_id:
                        category = JobCategory.query.get(category_id)
                        if not category:
                            category_id = None
                    data['category_id'] = category_id
                except (ValueError, TypeError):
                    data['category_id'] = None
            else:
                data['category_id'] = None
            
            if data.get('salary_min'):
                try:
                    data['salary_min'] = float(data['salary_min'])
                except (ValueError, TypeError):
                    data['salary_min'] = None
            else:
                data['salary_min'] = None
            
            if data.get('salary_max'):
                try:
                    data['salary_max'] = float(data['salary_max'])
                except (ValueError, TypeError):
                    data['salary_max'] = None
            else:
                data['salary_max'] = None
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'success': False, 'message': 'Tiêu đề không được để trống'}), 400
        
        # Decode text fields
        title = safe_decode_text(data.get('title', ''))
        description = safe_decode_text(data.get('description', ''))
        requirements = safe_decode_text(data.get('requirements', ''))
        location = safe_decode_text(data.get('location', ''))
        employment_type = safe_decode_text(data.get('employment_type', ''))
        
        # Validate category_id
        category_id = data.get('category_id')
        if category_id:
            category = JobCategory.query.get(category_id)
            if not category:
                category_id = None
        
        # Tạo job posting mới
        new_job = JobPosting(
            recruiter_id=user.id,
            title=title,
            description=description,
            requirements=requirements,
            location=location,
            salary_min=data.get('salary_min'),
            salary_max=data.get('salary_max'),
            category_id=category_id,
            employment_type=employment_type,
            is_active=data.get('is_active', True),
            deadline=None
        )
        
        # Xử lý deadline
        if data.get('deadline'):
            deadline_str = data['deadline']
            try:
                if 'T' in deadline_str:
                    date_part, time_part = deadline_str.split('T')
                    year, month, day = map(int, date_part.split('-'))
                    if ':' in time_part:
                        time_parts = time_part.split(':')
                        hour = int(time_parts[0])
                        minute = int(time_parts[1])
                        second = int(time_parts[2]) if len(time_parts) > 2 else 0
                    else:
                        hour = minute = second = 0
                    deadline_dt = datetime(year, month, day, hour, minute, second)
                    if hour == 0 and minute == 0 and second == 0:
                        deadline_dt = datetime.combine(deadline_dt.date(), time.max)
                    new_job.deadline = deadline_dt
            except Exception as e:
                logger.error(f"Error parsing deadline: {deadline_str}, error: {str(e)}")
        
        # Xử lý upload logo
        if 'company_logo' in request.files:
            logo_file = request.files['company_logo']
            if logo_file and logo_file.filename != '':
                try:
                    logo_path = save_company_logo(logo_file, 0)
                    new_job.company_logo = logo_path
                except Exception as e:
                    logger.error(f"Error saving company logo: {str(e)}")
        
        db.session.add(new_job)
        
        try:
            db.session.flush()
            job_id = new_job.id
            
            # Rename logo file nếu cần
            if new_job.company_logo and 'logo_0_' in new_job.company_logo:
                try:
                    old_path = new_job.company_logo
                    file_ext = old_path.rsplit('.', 1)[1]
                    new_filename = f'logo_{job_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{file_ext}'
                    new_path = f'/static/uploads/company_logos/{new_filename}'
                    old_full_path = os.path.join('Flask_CVProject', 'app', old_path.lstrip('/'))
                    new_full_path = os.path.join('Flask_CVProject', 'app', new_path.lstrip('/'))
                    if os.path.exists(old_full_path):
                        os.rename(old_full_path, new_full_path)
                        new_job.company_logo = new_path
                except Exception as e:
                    logger.error(f"Error renaming logo file: {str(e)}")
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Tạo bài đăng tuyển dụng thành công',
                'job': {
                    'id': new_job.id,
                    'title': new_job.title
                }
            }), 201
        except Exception as commit_error:
            db.session.rollback()
            logger.error(f"Error committing job: {str(commit_error)}", exc_info=True)
            raise
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating job: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi tạo bài đăng: {str(e)}'
        }), 500

@recruiter_bp.route('/api/recruiter/jobs/<int:job_id>', methods=['PUT'])
@jwt_required()
def update_job(job_id):
    """API cập nhật bài đăng tuyển dụng"""
    try:
        user = check_recruiter_role()
        if not user:
            return jsonify({'success': False, 'message': 'Chỉ nhà tuyển dụng mới có quyền truy cập'}), 403
        
        job = JobPosting.query.get_or_404(job_id)
        
        # Kiểm tra job thuộc về recruiter này
        if job.recruiter_id != user.id:
            return jsonify({'success': False, 'message': 'Bạn không có quyền chỉnh sửa bài đăng này'}), 403
        
        # Nhận dữ liệu từ form-data hoặc JSON
        data = {}
        if request.is_json:
            data = request.get_json()
        else:
            data = {
                'title': request.form.get('title'),
                'description': request.form.get('description'),
                'requirements': request.form.get('requirements'),
                'location': request.form.get('location'),
                'category_id': request.form.get('category_id'),
                'salary_min': request.form.get('salary_min'),
                'salary_max': request.form.get('salary_max'),
                'employment_type': request.form.get('employment_type'),
                'deadline': request.form.get('deadline'),
                'is_active': request.form.get('is_active')
            }
            
            # Validate và convert
            if data.get('category_id'):
                try:
                    category_id = int(data['category_id']) if data['category_id'] else None
                    if category_id:
                        category = JobCategory.query.get(category_id)
                        if not category:
                            category_id = None
                    data['category_id'] = category_id
                except (ValueError, TypeError):
                    data['category_id'] = None
            else:
                data['category_id'] = None
            
            if data.get('salary_min'):
                try:
                    data['salary_min'] = float(data['salary_min'])
                except (ValueError, TypeError):
                    data['salary_min'] = None
            else:
                data['salary_min'] = None
            
            if data.get('salary_max'):
                try:
                    data['salary_max'] = float(data['salary_max'])
                except (ValueError, TypeError):
                    data['salary_max'] = None
            else:
                data['salary_max'] = None
            
            if data.get('is_active') is not None:
                data['is_active'] = data['is_active'].lower() == 'true' if isinstance(data['is_active'], str) else bool(data['is_active'])
        
        # Validate required fields
        if data.get('title') is not None and not data.get('title'):
            return jsonify({'success': False, 'message': 'Tiêu đề không được để trống'}), 400
        
        # Cập nhật các trường
        if 'title' in data:
            job.title = safe_decode_text(data['title'])
        if 'description' in data:
            job.description = safe_decode_text(data.get('description', ''))
        if 'requirements' in data:
            job.requirements = safe_decode_text(data.get('requirements', ''))
        if 'location' in data:
            job.location = safe_decode_text(data.get('location', ''))
        if 'salary_min' in data:
            job.salary_min = data['salary_min']
        if 'salary_max' in data:
            job.salary_max = data['salary_max']
        if 'category_id' in data:
            job.category_id = data['category_id']
        if 'employment_type' in data:
            job.employment_type = safe_decode_text(data.get('employment_type', ''))
        if 'is_active' in data:
            job.is_active = data['is_active']
        
        # Xử lý deadline
        if 'deadline' in data:
            if data.get('deadline'):
                deadline_str = data['deadline']
                try:
                    if 'T' in deadline_str:
                        date_part, time_part = deadline_str.split('T')
                        year, month, day = map(int, date_part.split('-'))
                        if ':' in time_part:
                            time_parts = time_part.split(':')
                            hour = int(time_parts[0])
                            minute = int(time_parts[1])
                            second = int(time_parts[2]) if len(time_parts) > 2 else 0
                        else:
                            hour = minute = second = 0
                        deadline_dt = datetime(year, month, day, hour, minute, second)
                        if hour == 0 and minute == 0 and second == 0:
                            deadline_dt = datetime.combine(deadline_dt.date(), time.max)
                        job.deadline = deadline_dt
                except Exception as e:
                    logger.error(f"Error parsing deadline: {deadline_str}, error: {str(e)}")
            else:
                job.deadline = None
        
        # Xử lý upload logo
        if 'company_logo' in request.files:
            logo_file = request.files['company_logo']
            if logo_file and logo_file.filename != '':
                try:
                    # Xóa logo cũ nếu có
                    if job.company_logo:
                        old_logo_path = os.path.join('Flask_CVProject', 'app', job.company_logo.lstrip('/'))
                        if os.path.exists(old_logo_path):
                            try:
                                os.remove(old_logo_path)
                            except:
                                pass
                    
                    # Lưu logo mới
                    logo_path = save_company_logo(logo_file, job_id)
                    job.company_logo = logo_path
                except Exception as e:
                    logger.error(f"Error saving company logo: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cập nhật bài đăng thành công'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating job: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi cập nhật bài đăng: {str(e)}'
        }), 500

@recruiter_bp.route('/api/recruiter/jobs/<int:job_id>', methods=['DELETE'])
@jwt_required()
def delete_job(job_id):
    """API xóa bài đăng tuyển dụng"""
    try:
        user = check_recruiter_role()
        if not user:
            return jsonify({'success': False, 'message': 'Chỉ nhà tuyển dụng mới có quyền truy cập'}), 403
        
        job = JobPosting.query.get_or_404(job_id)
        
        # Kiểm tra job thuộc về recruiter này
        if job.recruiter_id != user.id:
            return jsonify({'success': False, 'message': 'Bạn không có quyền xóa bài đăng này'}), 403
        
        # Xóa logo nếu có
        if job.company_logo:
            try:
                logo_path = os.path.join('Flask_CVProject', 'app', job.company_logo.lstrip('/'))
                if os.path.exists(logo_path):
                    os.remove(logo_path)
            except:
                pass
        
        db.session.delete(job)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Xóa bài đăng thành công'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting job: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi xóa bài đăng: {str(e)}'
        }), 500

@recruiter_bp.route('/api/recruiter/jobs/<int:job_id>/applications', methods=['GET'])
@jwt_required()
def get_job_applications(job_id):
    """API lấy danh sách CV ứng tuyển cho một job"""
    try:
        user = check_recruiter_role()
        if not user:
            return jsonify({'success': False, 'message': 'Chỉ nhà tuyển dụng mới có quyền truy cập'}), 403
        
        job = JobPosting.query.get_or_404(job_id)
        
        # Kiểm tra job thuộc về recruiter này
        if job.recruiter_id != user.id:
            return jsonify({'success': False, 'message': 'Bạn không có quyền truy cập bài đăng này'}), 403
        
        # Lấy query parameters
        status = request.args.get('status')
        category_id = request.args.get('category_id', type=int)
        sort_by = request.args.get('sort_by', 'date')
        
        # Base query
        query = JobApplication.query.filter_by(job_posting_id=job_id)
        
        # Filter by status
        if status:
            query = query.filter_by(status=status)
        
        # Join với CV để filter theo category
        if category_id:
            query = query.join(CV).filter(CV.predicted_category_id == category_id)
        
        # Sort
        if sort_by == 'confidence':
            query = query.join(ClassificationLog, JobApplication.cv_id == ClassificationLog.cv_id)\
                         .order_by(desc(ClassificationLog.confidence))
        elif sort_by == 'category':
            query = query.join(CV).order_by(CV.predicted_category_id)
        else:  # date
            query = query.order_by(desc(JobApplication.applied_at))
        
        applications = query.all()
        
        applications_list = []
        for app in applications:
            cv = app.cv
            category_name = None
            if cv.category:
                try:
                    category_name = safe_decode_text(cv.category.name) if cv.category.name else None
                except:
                    category_name = str(cv.category.name) if cv.category.name else None
            
            # Lấy confidence từ classification log
            classification = ClassificationLog.query.filter_by(cv_id=cv.id).order_by(desc(ClassificationLog.created_at)).first()
            confidence = classification.confidence if classification else None
            
            applications_list.append({
                'id': app.id,
                'cv_id': app.cv_id,
                'cv_file_name': cv.file_name,
                'candidate_name': app.candidate.full_name or app.candidate.email,
                'candidate_id': app.candidate_id,
                'category': category_name,
                'category_id': cv.predicted_category_id,
                'confidence': confidence,
                'status': app.status,
                'notes': app.notes,
                'applied_at': app.applied_at.isoformat() if app.applied_at else None
            })
        
        return jsonify({
            'success': True,
            'applications': applications_list,
            'total': len(applications_list)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting applications: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi tải danh sách ứng viên: {str(e)}'
        }), 500

@recruiter_bp.route('/api/recruiter/jobs/<int:job_id>/top-cvs', methods=['GET'])
@jwt_required()
def get_top_cvs(job_id):
    """API lấy top CV phù hợp với job"""
    try:
        user = check_recruiter_role()
        if not user:
            return jsonify({'success': False, 'message': 'Chỉ nhà tuyển dụng mới có quyền truy cập'}), 403
        
        job = JobPosting.query.get_or_404(job_id)
        
        # Kiểm tra job thuộc về recruiter này
        if job.recruiter_id != user.id:
            return jsonify({'success': False, 'message': 'Bạn không có quyền truy cập bài đăng này'}), 403
        
        limit = request.args.get('limit', type=int, default=100)
        
        # Lấy category của job
        job_category_id = job.category_id
        
        # Lấy CV đã nộp vào job này
        applied_query = db.session.query(
            CV,
            func.coalesce(ClassificationLog.confidence, 0.0).label('confidence'),
            JobCategory.name.label('category_name'),
            JobApplication.id.label('application_id'),
            JobApplication.status.label('application_status'),
            JobApplication.applied_at.label('application_date')
        ).join(
            JobApplication, CV.id == JobApplication.cv_id
        ).outerjoin(
            ClassificationLog, CV.id == ClassificationLog.cv_id
        ).outerjoin(
            JobCategory, CV.predicted_category_id == JobCategory.id
        ).filter(
            JobApplication.job_posting_id == job_id
        )
        
        applied_results = applied_query.all()
        
        # Decode job information
        job_title = safe_decode_text(job.title) if job.title else ''
        job_description = safe_decode_text(job.description) if job.description else ''
        job_requirements = safe_decode_text(job.requirements) if job.requirements else None
        
        top_cvs = []
        for cv, confidence, category_name, app_id, app_status, app_date in applied_results:
            confidence_score = float(confidence) if confidence else 0.0
            
            # Sử dụng AI để đánh giá match score
            ai_match_score = None
            try:
                # Ưu tiên dùng file_content đã extract sẵn (nhanh hơn)
                cv_text = None
                
                # Thử lấy từ file_content trước (đã extract khi upload)
                if cv.file_content and len(str(cv.file_content).strip()) > 50:
                    cv_text = str(cv.file_content)
                    logger.info(f"Using stored file_content for CV {cv.id} ({len(cv_text)} characters)")
                
                # Nếu không có file_content, extract lại từ file
                if not cv_text and cv.file_name:
                    # Tạo đường dẫn file từ file_name
                    cv_file_path = os.path.join(BASE_DIR, 'static', 'uploads', cv.file_name)
                    
                    # Thử các đường dẫn khác nhau nếu không tìm thấy
                    if not os.path.exists(cv_file_path):
                        # Thử đường dẫn tuyệt đối với UPLOAD_FOLDER
                        upload_folder = os.path.join(BASE_DIR, 'static', 'uploads')
                        cv_file_path = os.path.join(upload_folder, cv.file_name)
                    
                    if os.path.exists(cv_file_path):
                        # Extract text từ CV file
                        file_ext = os.path.splitext(cv.file_name)[1].lower()
                        file_type = file_ext.lstrip('.')
                        if file_type in ['pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png']:
                            cv_text = extract_text_from_file(cv_file_path, file_type)
                            if cv_text and len(cv_text.strip()) > 50:
                                logger.info(f"Extracted text from file for CV {cv.id} ({len(cv_text)} characters)")
                
                # Đánh giá bằng AI nếu có text
                if cv_text and len(cv_text.strip()) > 50:
                    # Sử dụng AI để đánh giá
                    ai_match_score = evaluate_cv_match_with_job(
                        cv_text, 
                        job_title, 
                        job_description, 
                        job_requirements
                    )
                    if ai_match_score is not None:
                        logger.info(f"AI evaluated CV {cv.id} ({cv.file_name}): {ai_match_score:.2f}")
                    else:
                        logger.warning(f"AI evaluation returned None for CV {cv.id} ({cv.file_name})")
                else:
                    logger.warning(f"No text content available for CV {cv.id} ({cv.file_name}) to evaluate")
            except Exception as e:
                logger.warning(f"Error evaluating CV {cv.id} with AI: {str(e)}", exc_info=True)
            
            # Tính match score: ưu tiên AI score, fallback về confidence + bonus
            if ai_match_score is not None:
                match_score = ai_match_score
            else:
                # Fallback: confidence + bonus nếu category match
                match_score = confidence_score
                if job_category_id and cv.predicted_category_id == job_category_id:
                    match_score = min(1.0, confidence_score + 0.3)  # Bonus 0.3, tối đa 1.0
            
            # Decode category name
            try:
                decoded_category_name = safe_decode_text(category_name) if category_name else 'Chưa phân loại'
            except:
                decoded_category_name = str(category_name) if category_name else 'Chưa phân loại'
            
            top_cvs.append({
                'cv_id': cv.id,
                'file_name': cv.file_name,
                'category': decoded_category_name,
                'category_id': cv.predicted_category_id,
                'confidence': confidence_score,
                'match_score': match_score,
                'ai_evaluated': ai_match_score is not None,
                'application_id': app_id,
                'application_status': app_status,
                'application_date': app_date.isoformat() if app_date else None,
                'uploaded_at': cv.uploaded_at.isoformat() if cv.uploaded_at else None
            })
        
        # Sắp xếp theo match_score giảm dần (cao đến thấp)
        top_cvs.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Giới hạn số lượng
        top_cvs = top_cvs[:limit]
        
        return jsonify({
            'success': True,
            'job_title': job_title,
            'top_cvs': top_cvs,
            'total': len(top_cvs)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting top CVs: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi tải top CV: {str(e)}'
        }), 500

@recruiter_bp.route('/api/recruiter/applications/<int:application_id>/status', methods=['PUT'])
@jwt_required()
def update_application_status(application_id):
    """API cập nhật trạng thái application"""
    try:
        user = check_recruiter_role()
        if not user:
            return jsonify({'success': False, 'message': 'Chỉ nhà tuyển dụng mới có quyền truy cập'}), 403
        
        # Lấy application
        application = JobApplication.query.get_or_404(application_id)
        
        # Kiểm tra job thuộc về recruiter này
        job = application.job_posting
        if job.recruiter_id != user.id:
            return jsonify({'success': False, 'message': 'Bạn không có quyền cập nhật application này'}), 403
        
        # Lấy dữ liệu từ request
        data = request.get_json() or {}
        new_status = data.get('status')
        
        # Validate status
        valid_statuses = ['pending', 'reviewed', 'shortlisted', 'rejected', 'hired']
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'message': f'Trạng thái không hợp lệ. Phải là một trong: {", ".join(valid_statuses)}'
            }), 400
        
        # Cập nhật status
        old_status = application.status
        application.status = new_status
        
        # Cập nhật reviewed_at nếu status thay đổi từ pending sang status khác
        if old_status == 'pending' and new_status != 'pending':
            application.reviewed_at = datetime.utcnow()
        
        db.session.commit()
        
        # Map status to Vietnamese
        status_map = {
            'pending': 'Chờ xem xét',
            'reviewed': 'Đã xem',
            'shortlisted': 'Đã chọn',
            'rejected': 'Từ chối',
            'hired': 'Đã tuyển'
        }
        
        return jsonify({
            'success': True,
            'message': f'Đã cập nhật trạng thái thành "{status_map.get(new_status, new_status)}". Ứng viên sẽ nhận được thông báo.',
            'application': {
                'id': application.id,
                'status': application.status,
                'reviewed_at': application.reviewed_at.isoformat() if application.reviewed_at else None
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating application status: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi cập nhật trạng thái: {str(e)}'
        }), 500

@recruiter_bp.route('/recruiter/jobs/<int:job_id>/top-cvs', methods=['GET'])
def top_cvs_page(job_id):
    """Trang hiển thị Top CV phù hợp với job"""
    return render_template('recruiter/top_cvs.html', job_id=job_id)
