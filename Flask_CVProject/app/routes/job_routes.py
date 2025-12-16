"""
Routes cho ứng viên xem và apply jobs
"""

import logging
import re
from flask import Blueprint, render_template, request, jsonify
from app.extensions import db
from app.models import JobPosting, JobApplication, JobCategory, User, CV
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, time, timezone
from sqlalchemy import desc, or_, and_

logger = logging.getLogger(__name__)

def fix_vietnamese_encoding(text):
    """
    Cố gắng sửa lỗi encoding tiếng Việt khi đọc từ database.
    Sử dụng cùng logic với fix_common_vietnamese_errors trong recruiter_routes
    """
    if not text or not isinstance(text, str):
        return text
    
    # Import hàm từ recruiter_routes
    try:
        from app.routes.recruiter_routes import fix_common_vietnamese_errors
        return fix_common_vietnamese_errors(text)
    except ImportError:
        # Fallback nếu không import được
        return text

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
                if '' not in decoded:
                    return decoded
            except (UnicodeDecodeError, UnicodeError):
                continue
        # Cuối cùng, ignore errors
        return text.decode('utf-8', errors='replace').replace('', '')
    
    # Nếu đã là string
    if isinstance(text, str):
        # Kiểm tra xem string có phải là UTF-8 hợp lệ không
        try:
            # Thử encode/decode để kiểm tra
            text.encode('utf-8').decode('utf-8')
            # Nếu có ký tự replacement (), có thể đã bị decode sai
            if '' in text:
                # Có thể cần decode lại từ bytes gốc
                # Nhưng không có bytes gốc, nên chỉ có thể fix một phần
                pass
            return text
        except (UnicodeEncodeError, UnicodeDecodeError):
            # String không phải UTF-8 hợp lệ
            # Có thể đã bị double encoding hoặc encoding sai
            try:
                # Thử decode lại: encode với latin-1 rồi decode với utf-8
                # (để fix double encoding)
                fixed = text.encode('latin-1', errors='ignore').decode('utf-8', errors='replace')
                return fixed.replace('', '')
            except:
                # Cuối cùng, chỉ loại bỏ ký tự không hợp lệ
                try:
                    return text.encode('utf-8', errors='replace').decode('utf-8').replace('', '')
                except:
                    return text
    
    # Nếu không phải string hay bytes, convert sang string
    try:
        return str(text)
    except:
        return ''

job_bp = Blueprint('job', __name__)

def get_user_id_from_jwt():
    """Helper function to get user_id from JWT identity and convert to int"""
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        return int(user_id)
    return user_id

# ============= Page Routes =============

@job_bp.route('/jobs/<int:job_id>', methods=['GET'])
def job_detail_page(job_id):
    """Trang chi tiết job cho ứng viên"""
    return render_template('job_detail.html', job_id=job_id)

# ============= API Endpoints =============

@job_bp.route('/api/jobs', methods=['GET'])
def get_jobs():
    """
    API lấy danh sách jobs công khai (không cần đăng nhập)
    Hỗ trợ filter và search
    """
    try:
        # Query parameters
        search = request.args.get('search', '').strip()
        category_id = request.args.get('category_id', type=int)
        location = request.args.get('location', '').strip()
        employment_type = request.args.get('employment_type', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        
        # Base query - chỉ lấy jobs đang active
        # Sử dụng UTC để so sánh, nhưng chỉ so sánh ngày (không so sánh giờ) để tránh lỗi timezone
        from datetime import timedelta, time
        now = datetime.utcnow()
        # End of today (23:59:59) - jobs hết hạn trong ngày hôm nay vẫn được hiển thị
        today_end = datetime.combine(now.date(), time.max)
        
        query = JobPosting.query.filter_by(is_active=True)
        
        # Filter out expired jobs - chỉ hiển thị jobs chưa hết hạn
        # Jobs có deadline >= end of today (hoặc deadline = None) sẽ được hiển thị
        query = query.filter(
            or_(
                JobPosting.deadline.is_(None),  # Không có deadline = không bao giờ hết hạn
                JobPosting.deadline >= today_end  # Deadline >= end of today = chưa hết hạn
            )
        )
        
        total_active = JobPosting.query.filter_by(is_active=True).count()
        logger.info(f"Querying jobs: is_active=True, now={now}, today_end={today_end}, total_active={total_active}")
        
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
        
        # Pagination
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        jobs = pagination.items
        
        jobs_list = []
        for job in jobs:
            # Đếm số lượng ứng viên đã apply
            application_count = JobApplication.query.filter_by(job_posting_id=job.id).count()
            
            # Check if job is expired - so sánh với end of today để tránh lỗi timezone
            # Job được coi là hết hạn nếu deadline < end of today
            if job.deadline:
                # Đảm bảo deadline là naive datetime (không có timezone)
                deadline = job.deadline
                if hasattr(deadline, 'tzinfo') and deadline.tzinfo is not None:
                    # Nếu có timezone, chuyển về UTC và bỏ timezone
                    deadline = deadline.astimezone(timezone.utc).replace(tzinfo=None)
                
                # So sánh với end of today (23:59:59)
                today_end = datetime.combine(now.date(), time.max)
                is_expired = deadline < today_end
            else:
                is_expired = False
            
            # Đảm bảo encoding đúng cho các trường text
            title = safe_decode_text(job.title) if job.title else None
            description = safe_decode_text(job.description) if job.description else None
            requirements = safe_decode_text(job.requirements) if job.requirements else None
            location = safe_decode_text(job.location) if job.location else None
            category_name = safe_decode_text(job.category.name) if job.category and job.category.name else None
            employment_type = safe_decode_text(job.employment_type) if job.employment_type else None
            recruiter_name = safe_decode_text(job.recruiter.full_name) if job.recruiter and job.recruiter.full_name else (safe_decode_text(job.recruiter.email) if job.recruiter else None)
            
            # Cố gắng fix các lỗi encoding phổ biến
            title = fix_vietnamese_encoding(title) if title else None
            description = fix_vietnamese_encoding(description) if description else None
            requirements = fix_vietnamese_encoding(requirements) if requirements else None
            location = fix_vietnamese_encoding(location) if location else None
            
            # Truncate description và requirements nếu cần
            if description and len(description) > 200:
                description = description[:200] + '...'
            if requirements and len(requirements) > 200:
                requirements = requirements[:200] + '...'
            
            jobs_list.append({
                'id': job.id,
                'title': title,
                'description': description,
                'requirements': requirements,
                'location': location,
                'salary_min': float(job.salary_min) if job.salary_min else None,
                'salary_max': float(job.salary_max) if job.salary_max else None,
                'category': category_name,
                'category_id': job.category_id,
                'employment_type': employment_type,
                'deadline': job.deadline.isoformat() if job.deadline else None,
                'is_expired': is_expired,
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'application_count': application_count,
                'recruiter_name': recruiter_name,
                'company_logo': job.company_logo if hasattr(job, 'company_logo') and job.company_logo else None
            })
        
        total_active = JobPosting.query.filter_by(is_active=True).count()
        logger.info(f"Returning {len(jobs_list)} jobs (total active in DB: {total_active}, filtered by deadline)")
        
        if len(jobs_list) == 0 and total_active > 0:
            # Debug: Kiểm tra các jobs active nhưng bị filter ra
            all_active_jobs = JobPosting.query.filter_by(is_active=True).all()
            expired_count = 0
            no_deadline_count = 0
            valid_count = 0
            for job in all_active_jobs:
                if job.deadline is None:
                    no_deadline_count += 1
                    valid_count += 1
                elif job.deadline >= today_end:
                    valid_count += 1
                else:
                    expired_count += 1
            logger.warning(f"No jobs returned but {total_active} active jobs exist. Expired: {expired_count}, No deadline: {no_deadline_count}, Valid: {valid_count}")
        
        return jsonify({
            'success': True,
            'jobs': jobs_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            },
            'debug': {
                'total_active_in_db': total_active,
                'now': now.isoformat(),
                'today_end': today_end.isoformat()
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting jobs: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi tải danh sách việc làm: {str(e)}'
        }), 500

@job_bp.route('/api/jobs/<int:job_id>', methods=['GET'])
def get_job_detail(job_id):
    """API lấy chi tiết job (công khai)"""
    try:
        job = JobPosting.query.get_or_404(job_id)
        
        # Chỉ hiển thị job đang active và chưa hết hạn
        from datetime import time
        now = datetime.utcnow()
        today_end = datetime.combine(now.date(), time.max)  # End of today
        
        if not job.is_active:
            return jsonify({
                'success': False,
                'message': 'Bài đăng này không còn hoạt động'
            }), 404
        
        # Kiểm tra deadline - so sánh với end of today để tránh lỗi timezone
        if job.deadline:
            deadline = job.deadline
            # Đảm bảo deadline là naive datetime
            if hasattr(deadline, 'tzinfo') and deadline.tzinfo is not None:
                deadline = deadline.astimezone(timezone.utc).replace(tzinfo=None)
            
            if deadline < today_end:
                return jsonify({
                    'success': False,
                    'message': 'Bài đăng này đã hết hạn nộp hồ sơ'
                }), 404
        
        # Đếm số lượng ứng viên đã apply
        application_count = JobApplication.query.filter_by(job_posting_id=job.id).count()
        
        # has_applied sẽ được check từ frontend nếu user đã đăng nhập
        has_applied = False
        
        # Đảm bảo encoding đúng cho các trường text
        title = safe_decode_text(job.title) if job.title else None
        description = safe_decode_text(job.description) if job.description else None
        requirements = safe_decode_text(job.requirements) if job.requirements else None
        location = safe_decode_text(job.location) if job.location else None
        category_name = safe_decode_text(job.category.name) if job.category and job.category.name else None
        employment_type = safe_decode_text(job.employment_type) if job.employment_type else None
        
        # Cố gắng fix các lỗi encoding phổ biến
        title = fix_vietnamese_encoding(title) if title else None
        description = fix_vietnamese_encoding(description) if description else None
        requirements = fix_vietnamese_encoding(requirements) if requirements else None
        location = fix_vietnamese_encoding(location) if location else None
        recruiter_name = safe_decode_text(job.recruiter.full_name) if job.recruiter and job.recruiter.full_name else (safe_decode_text(job.recruiter.email) if job.recruiter else None)
        
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
                'category': category_name,
                'category_id': job.category_id,
                'employment_type': employment_type,
                'deadline': job.deadline.isoformat() if job.deadline else None,
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'application_count': application_count,
                'recruiter_name': recruiter_name,
                'has_applied': has_applied
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting job detail: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi tải chi tiết việc làm: {str(e)}'
        }), 500

@job_bp.route('/api/jobs/<int:job_id>/check-application', methods=['GET'])
@jwt_required()
def check_application(job_id):
    """API kiểm tra xem user đã apply chưa"""
    try:
        user_id = get_user_id_from_jwt()
        existing_application = JobApplication.query.filter_by(
            job_posting_id=job_id,
            candidate_id=user_id
        ).first()
        
        return jsonify({
            'success': True,
            'has_applied': existing_application is not None
        }), 200
    except:
        return jsonify({
            'success': False,
            'has_applied': False
        }), 200

@job_bp.route('/api/jobs/<int:job_id>/apply', methods=['POST'])
@jwt_required()
def apply_job(job_id):
    """API ứng viên apply vào job"""
    try:
        user_id = get_user_id_from_jwt()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': 'Người dùng không tồn tại'}), 404
        
        # Kiểm tra user có phải candidate không
        if user.role != 'candidate':
            return jsonify({'success': False, 'message': 'Chỉ ứng viên mới có thể ứng tuyển'}), 403
        
        job = JobPosting.query.get_or_404(job_id)
        
        if not job.is_active:
            return jsonify({'success': False, 'message': 'Bài đăng này không còn hoạt động'}), 400
        
        # Kiểm tra đã apply chưa
        existing_application = JobApplication.query.filter_by(
            job_posting_id=job_id,
            candidate_id=user_id
        ).first()
        
        if existing_application:
            return jsonify({'success': False, 'message': 'Bạn đã ứng tuyển cho vị trí này rồi'}), 400
        
        data = request.get_json() or {}
        cv_id = data.get('cv_id')
        
        # Nếu không có cv_id, lấy CV mới nhất của user
        if not cv_id:
            latest_cv = CV.query.filter_by(user_id=user_id).order_by(desc(CV.uploaded_at)).first()
            if not latest_cv:
                return jsonify({'success': False, 'message': 'Bạn cần có ít nhất một CV để ứng tuyển'}), 400
            cv_id = latest_cv.id
        else:
            # Kiểm tra CV thuộc về user
            cv = CV.query.get(cv_id)
            if not cv or cv.user_id != user_id:
                return jsonify({'success': False, 'message': 'CV không hợp lệ'}), 400
        
        # Tạo application
        new_application = JobApplication(
            job_posting_id=job_id,
            cv_id=cv_id,
            candidate_id=user_id,
            status='pending'
        )
        
        db.session.add(new_application)
        db.session.commit()
        
        logger.info(f"User {user_id} applied to job {job_id} with CV {cv_id}")
        
        return jsonify({
            'success': True,
            'message': 'Ứng tuyển thành công!',
            'application_id': new_application.id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error applying to job: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi ứng tuyển: {str(e)}'
        }), 500

@job_bp.route('/my-applications', methods=['GET'])
def my_applications_page():
    """Trang xem trạng thái ứng tuyển của ứng viên"""
    return render_template('my_applications.html')

@job_bp.route('/api/candidate/applications', methods=['GET'])
@jwt_required()
def get_my_applications():
    """API lấy danh sách job applications của ứng viên hiện tại"""
    try:
        user_id = get_user_id_from_jwt()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': 'Người dùng không tồn tại'}), 404
        
        # Kiểm tra user có phải candidate không
        if user.role != 'candidate':
            return jsonify({'success': False, 'message': 'Chỉ ứng viên mới có quyền truy cập'}), 403
        
        # Query parameters
        status = request.args.get('status')  # pending, reviewed, shortlisted, rejected, hired
        sort_by = request.args.get('sort_by', 'date')  # date, job_title
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Base query - lấy tất cả applications của user
        query = JobApplication.query.filter_by(candidate_id=user_id)
        
        # Filter by status
        if status:
            query = query.filter_by(status=status)
        
        # Sort
        if sort_by == 'job_title':
            query = query.join(JobPosting).order_by(JobPosting.title)
        else:  # date (default)
            query = query.order_by(desc(JobApplication.applied_at))
        
        # Pagination
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        applications = pagination.items
        
        applications_list = []
        for app in applications:
            job = app.job_posting
            cv = app.cv
            
            # Map status to Vietnamese
            status_map = {
                'pending': 'Chờ xem xét',
                'reviewed': 'Đã xem',
                'shortlisted': 'Đã chọn',
                'rejected': 'Đã từ chối',
                'hired': 'Đã tuyển'
            }
            
            # Lấy category name cho CV (tương tự như trong cv_routes.py)
            cv_category_name = None
            if cv.predicted_category_id:
                try:
                    category = JobCategory.query.get(cv.predicted_category_id)
                    if category:
                        cv_category_name = category.name
                except Exception as e:
                    logger.warning(f"Error getting category name for CV {cv.id}: {str(e)}")
                    cv_category_name = None
            
            applications_list.append({
                'id': app.id,
                'job': {
                    'id': job.id,
                    'title': job.title,
                    'location': job.location,
                    'category': job.category.name if job.category else None,
                    'employment_type': job.employment_type,
                    'deadline': job.deadline.isoformat() if job.deadline else None,
                    'is_active': job.is_active
                },
                'cv': {
                    'id': cv.id,
                    'file_name': cv.file_name,
                    'predicted_category': cv_category_name
                },
                'status': app.status,
                'status_text': status_map.get(app.status, app.status),
                'notes': app.notes,
                'applied_at': app.applied_at.isoformat() if app.applied_at else None,
                'reviewed_at': app.reviewed_at.isoformat() if app.reviewed_at else None
            })
        
        return jsonify({
            'success': True,
            'applications': applications_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting my applications: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi tải danh sách ứng tuyển: {str(e)}'
        }), 500

