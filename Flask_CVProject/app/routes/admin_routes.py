"""
Routes cho admin
- Quản lý tài khoản (tìm kiếm, khóa/mở khóa)
- Thống kê (bài đăng, CV)
- Quản lý bài đăng tuyển dụng (tất cả bài đăng của tất cả nhà tuyển dụng)
"""

import os
import logging
from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import User, JobPosting, CV, JobApplication, CVData, JobCategory, ClassificationLog
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta, time, timezone
from sqlalchemy import func, desc, and_, or_

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def get_user_id_from_jwt():
    """Helper function to get user_id from JWT identity"""
    user_id = get_jwt_identity()
    if isinstance(user_id, str) and user_id.isdigit():
        return int(user_id)
    return user_id

def check_admin_role():
    """Kiểm tra user có phải admin không"""
    user_id = get_user_id_from_jwt()
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return None
    return user

# ============= HTML Pages =============
@admin_bp.route('/dashboard', methods=['GET'])
def admin_dashboard():
    """Trang dashboard admin"""
    return render_template('admin/dashboard.html')

@admin_bp.route('/users', methods=['GET'])
def admin_users():
    """Trang quản lý tài khoản"""
    return render_template('admin/users.html')

@admin_bp.route('/jobs', methods=['GET'])
def admin_jobs():
    """Trang danh sách bài đăng tuyển dụng"""
    return render_template('admin/jobs.html')

@admin_bp.route('/jobs/new', methods=['GET'])
def admin_new_job():
    """Trang tạo bài đăng tuyển dụng mới"""
    return render_template('admin/new_job.html')

@admin_bp.route('/jobs/<int:job_id>', methods=['GET'])
def admin_job_detail(job_id):
    """Trang chi tiết bài đăng tuyển dụng"""
    return render_template('admin/job_detail.html', job_id=job_id)

@admin_bp.route('/jobs/<int:job_id>/edit', methods=['GET'])
def admin_edit_job(job_id):
    """Trang chỉnh sửa bài đăng tuyển dụng"""
    return render_template('admin/edit_job.html', job_id=job_id)

@admin_bp.route('/jobs/<int:job_id>/applications', methods=['GET'])
def admin_job_applications(job_id):
    """Trang danh sách CV ứng tuyển cho một job"""
    return render_template('admin/applications.html', job_id=job_id)

@admin_bp.route('/jobs/<int:job_id>/top-cvs', methods=['GET'])
def admin_top_cvs(job_id):
    """Trang hiển thị Top CV phù hợp với job"""
    return render_template('admin/top_cvs.html', job_id=job_id)

# ============= API Endpoints =============

@admin_bp.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    """API lấy danh sách users với tìm kiếm và phân trang"""
    try:
        admin = check_admin_role()
        if not admin:
            return jsonify({'success': False, 'message': 'Chỉ admin mới có quyền truy cập'}), 403
        
        search = request.args.get('search', '').strip()
        role = request.args.get('role', '').strip()
        is_active = request.args.get('is_active', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = User.query
        
        if search:
            search_filter = or_(
                User.email.ilike(f'%{search}%'),
                User.full_name.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        if role and role in ['candidate', 'recruiter', 'admin']:
            query = query.filter(User.role == role)
        
        if is_active.lower() == 'true':
            query = query.filter(User.is_active == True)
        elif is_active.lower() == 'false':
            query = query.filter(User.is_active == False)
        
        query = query.order_by(desc(User.created_at))
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        users = pagination.items
        
        users_data = []
        for user in users:
            cv_count = CV.query.filter_by(user_id=user.id).count()
            
            job_count = 0
            if user.role == 'recruiter':
                job_count = JobPosting.query.filter_by(recruiter_id=user.id).count()
            
            application_count = 0
            if user.role == 'candidate':
                application_count = JobApplication.query.filter_by(candidate_id=user.id).count()
            
            users_data.append({
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'cv_count': cv_count,
                'job_count': job_count,
                'application_count': application_count
            })
        
        return jsonify({
            'success': True,
            'users': users_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi tải danh sách users: {str(e)}'
        }), 500

@admin_bp.route('/api/users/<int:user_id>/toggle-active', methods=['PUT'])
@jwt_required()
def toggle_user_active(user_id):
    """API khóa/mở khóa tài khoản"""
    try:
        admin = check_admin_role()
        if not admin:
            return jsonify({'success': False, 'message': 'Chỉ admin mới có quyền truy cập'}), 403
        
        if user_id == admin.id:
            return jsonify({'success': False, 'message': 'Bạn không thể khóa chính mình'}), 400
        
        user = User.query.get_or_404(user_id)
        
        user.is_active = not user.is_active
        db.session.commit()
        
        action = "mở khóa" if user.is_active else "khóa"
        logger.info(f"Admin {admin.id} {action} tài khoản {user_id}")
        
        return jsonify({
            'success': True,
            'message': f'Đã {action} tài khoản thành công',
            'is_active': user.is_active
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling user active: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi cập nhật trạng thái tài khoản: {str(e)}'
        }), 500

@admin_bp.route('/api/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """API lấy thống kê tổng quan"""
    try:
        admin = check_admin_role()
        if not admin:
            return jsonify({'success': False, 'message': 'Chỉ admin mới có quyền truy cập'}), 403
        
        total_users = User.query.count()
        candidate_count = User.query.filter_by(role='candidate').count()
        recruiter_count = User.query.filter_by(role='recruiter').count()
        admin_count = User.query.filter_by(role='admin').count()
        active_users = User.query.filter_by(is_active=True).count()
        inactive_users = User.query.filter_by(is_active=False).count()
        
        total_jobs = JobPosting.query.count()
        active_jobs = JobPosting.query.filter_by(is_active=True).count()
        inactive_jobs = JobPosting.query.filter_by(is_active=False).count()
        
        total_cvs = CV.query.count()
        total_cv_data = CVData.query.count()
        
        total_applications = JobApplication.query.count()
        pending_applications = JobApplication.query.filter_by(status='pending').count()
        reviewed_applications = JobApplication.query.filter_by(status='reviewed').count()
        shortlisted_applications = JobApplication.query.filter_by(status='shortlisted').count()
        rejected_applications = JobApplication.query.filter_by(status='rejected').count()
        hired_applications = JobApplication.query.filter_by(status='hired').count()
        
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)
        
        jobs_last_7_days = JobPosting.query.filter(JobPosting.created_at >= seven_days_ago).count()
        jobs_last_30_days = JobPosting.query.filter(JobPosting.created_at >= thirty_days_ago).count()
        
        cvs_last_7_days = CV.query.filter(CV.uploaded_at >= seven_days_ago).count()
        cvs_last_30_days = CV.query.filter(CV.uploaded_at >= thirty_days_ago).count()
        
        applications_last_7_days = JobApplication.query.filter(JobApplication.applied_at >= seven_days_ago).count()
        applications_last_30_days = JobApplication.query.filter(JobApplication.applied_at >= thirty_days_ago).count()
        
        daily_stats = []
        for i in range(30):
            date = now - timedelta(days=29-i)
            date_start = datetime.combine(date.date(), datetime.min.time())
            date_end = datetime.combine(date.date(), datetime.max.time())
            
            jobs_count = JobPosting.query.filter(
                and_(
                    JobPosting.created_at >= date_start,
                    JobPosting.created_at <= date_end
                )
            ).count()
            
            cvs_count = CV.query.filter(
                and_(
                    CV.uploaded_at >= date_start,
                    CV.uploaded_at <= date_end
                )
            ).count()
            
            daily_stats.append({
                'date': date.date().isoformat(),
                'jobs': jobs_count,
                'cvs': cvs_count
            })
        
        return jsonify({
            'success': True,
            'statistics': {
                'users': {
                    'total': total_users,
                    'candidates': candidate_count,
                    'recruiters': recruiter_count,
                    'admins': admin_count,
                    'active': active_users,
                    'inactive': inactive_users
                },
                'jobs': {
                    'total': total_jobs,
                    'active': active_jobs,
                    'inactive': inactive_jobs,
                    'last_7_days': jobs_last_7_days,
                    'last_30_days': jobs_last_30_days
                },
                'cvs': {
                    'total': total_cvs,
                    'cv_data': total_cv_data,
                    'last_7_days': cvs_last_7_days,
                    'last_30_days': cvs_last_30_days
                },
                'applications': {
                    'total': total_applications,
                    'pending': pending_applications,
                    'reviewed': reviewed_applications,
                    'shortlisted': shortlisted_applications,
                    'rejected': rejected_applications,
                    'hired': hired_applications,
                    'last_7_days': applications_last_7_days,
                    'last_30_days': applications_last_30_days
                },
                'daily_stats': daily_stats
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi tải thống kê: {str(e)}'
        }), 500

# ============= Helper Functions =============

LOGO_UPLOAD_FOLDER = os.path.join('Flask_CVProject', 'app', 'static', 'uploads', 'company_logos')
ALLOWED_LOGO_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'}

def allowed_logo_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_LOGO_EXTENSIONS

def save_company_logo(file, job_id):
    if not file or file.filename == '':
        return None
    
    if not allowed_logo_file(file.filename):
        raise ValueError('Định dạng file không được hỗ trợ. Chỉ chấp nhận: JPG, JPEG, PNG, GIF, WEBP, SVG')

    file_ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f'logo_{job_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{file_ext}'
    filename = secure_filename(filename)
        
      
    os.makedirs(LOGO_UPLOAD_FOLDER, exist_ok=True)
    
    file_path = os.path.join(LOGO_UPLOAD_FOLDER, filename)
    file.save(file_path)
    
    return f'/static/uploads/company_logos/{filename}'

def safe_decode_text(text):
    if text is None:
        return None
    
    if isinstance(text, bytes):
        encodings = ['utf-8', 'cp1252', 'latin-1', 'iso-8859-1', 'windows-1252']
        for encoding in encodings:
            try:
                decoded = text.decode(encoding)
                if '\ufffd' not in decoded:
                    return decoded
            except (UnicodeDecodeError, UnicodeError):
                continue
        return text.decode('utf-8', errors='replace').replace('\ufffd', '')
    
    if isinstance(text, str):
        try:
            text.encode('utf-8').decode('utf-8')
            return text
        except (UnicodeEncodeError, UnicodeDecodeError):
            try:
                fixed = text.encode('latin-1', errors='ignore').decode('utf-8', errors='replace')
                return fixed.replace('\ufffd', '')
            except Exception:
                return text.encode('utf-8', errors='replace').decode('utf-8').replace('\ufffd', '')
    
    try:
        return str(text)
    except Exception:
        return ''

@admin_bp.route('/api/jobs', methods=['GET'])
@jwt_required()
def admin_get_jobs():
    """API lấy danh sách TẤT CẢ bài đăng tuyển dụng (admin có thể xem tất cả)"""
    try:
        admin = check_admin_role()
        if not admin:
            return jsonify({'success': False, 'message': 'Chỉ admin mới có quyền truy cập'}), 403
        
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        search = request.args.get('search', '').strip()
        category_id = request.args.get('category_id', type=int)
        location = request.args.get('location', '').strip()
        employment_type = request.args.get('employment_type', '').strip()
        
        # Lấy jobs với pagination và filters
        query = JobPosting.query
        
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
        
        jobs_list = []
        for job in jobs:
            try:
                application_count = JobApplication.query.filter_by(job_posting_id=job.id).count()
                
                title = safe_decode_text(job.title) if job.title else None
                description = safe_decode_text(job.description) if job.description else None
                location = safe_decode_text(job.location) if job.location else None
                category_name = safe_decode_text(job.category.name) if job.category and job.category.name else None
                
                if description and len(description) > 200:
                    description = description[:200] + '...'
                
                recruiter = User.query.get(job.recruiter_id)
                
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
                    'company_logo': getattr(job, 'company_logo', None) if hasattr(job, 'company_logo') else None,
                    'recruiter_id': job.recruiter_id,
                    'recruiter_name': recruiter.full_name if recruiter else None,
                    'recruiter_email': recruiter.email if recruiter else None
                })
            except Exception as e:
                logger.error(f"Error processing job {job.id}: {str(e)}")
                continue
        
        return jsonify({
            'success': True,
            'jobs': jobs_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting jobs: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi tải danh sách bài đăng: {str(e)}'
        }), 500

@admin_bp.route('/api/jobs', methods=['POST'])
@jwt_required()
def admin_create_job():
    try:
        admin = check_admin_role()
        if not admin:
            return jsonify({'success': False, 'message': 'Chỉ admin mới có quyền truy cập'}), 403
        
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
                'is_active': request.form.get('is_active', 'true').lower() == 'true',
                'recruiter_id': request.form.get('recruiter_id')
            }
            
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
                    data['salary_min'] = int(data['salary_min']) if data['salary_min'] else None
                except:
                    data['salary_min'] = None
            
            if data.get('salary_max'):
                try:
                    data['salary_max'] = int(data['salary_max']) if data['salary_max'] else None
                except:
                    data['salary_max'] = None
            
            recruiter_id = data.get('recruiter_id')
            if recruiter_id:
                try:
                    recruiter_id = int(recruiter_id)
                    recruiter = User.query.get(recruiter_id)
                    if not recruiter or recruiter.role != 'recruiter':
                        return jsonify({'success': False, 'message': 'Recruiter không hợp lệ'}), 400
                    data['recruiter_id'] = recruiter_id
                except (ValueError, TypeError):
                    return jsonify({'success': False, 'message': 'Recruiter ID không hợp lệ'}), 400
            else:
                return jsonify({'success': False, 'message': 'Vui lòng chọn nhà tuyển dụng'}), 400
        
        if not data.get('title'):
            return jsonify({'success': False, 'message': 'Tiêu đề không được để trống'}), 400
        
        def prepare_unicode_text(text):
            if text is None:
                return None
            if isinstance(text, bytes):
                return text.decode('utf-8')
            if isinstance(text, str):
                import unicodedata
                normalized = unicodedata.normalize('NFC', text)
                try:
                    normalized.encode('utf-8')
                    return normalized
                except:
                    return text.encode('utf-8', errors='replace').decode('utf-8')
            return str(text)
        
        title = prepare_unicode_text(data.get('title'))
        description = prepare_unicode_text(data.get('description'))
        requirements = prepare_unicode_text(data.get('requirements'))
        location = prepare_unicode_text(data.get('location'))
        employment_type = prepare_unicode_text(data.get('employment_type'))
        
        category_id = data.get('category_id')
        if category_id:
            category = JobCategory.query.get(category_id)
            if not category:
                category_id = None
        
        new_job = JobPosting(
            recruiter_id=data['recruiter_id'],
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

@admin_bp.route('/api/jobs/<int:job_id>', methods=['GET'])
@jwt_required()
def admin_get_job_detail(job_id):
    try:
        admin = check_admin_role()
        if not admin:
            return jsonify({'success': False, 'message': 'Chỉ admin mới có quyền truy cập'}), 403
        
        job = JobPosting.query.get_or_404(job_id)
        
        title = safe_decode_text(job.title) if job.title else None
        description = safe_decode_text(job.description) if job.description else None
        requirements = safe_decode_text(job.requirements) if job.requirements else None
        location = safe_decode_text(job.location) if job.location else None
        category_name = safe_decode_text(job.category.name) if job.category and job.category.name else None
        employment_type = safe_decode_text(job.employment_type) if job.employment_type else None
        
        recruiter = User.query.get(job.recruiter_id)
        
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
                'company_logo': getattr(job, 'company_logo', None) if hasattr(job, 'company_logo') else None,
                'recruiter_id': job.recruiter_id,
                'recruiter_name': recruiter.full_name if recruiter else None,
                'recruiter_email': recruiter.email if recruiter else None
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting job detail: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi tải chi tiết bài đăng: {str(e)}'
        }), 500

@admin_bp.route('/api/jobs/<int:job_id>', methods=['PUT'])
@jwt_required()
def admin_update_job(job_id):
    try:
        admin = check_admin_role()
        if not admin:
            return jsonify({'success': False, 'message': 'Chỉ admin mới có quyền truy cập'}), 403
        
        job = JobPosting.query.get_or_404(job_id)
        
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
                'is_active': request.form.get('is_active', 'true').lower() == 'true',
                'recruiter_id': request.form.get('recruiter_id')
            }
            
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
                    data['salary_min'] = int(data['salary_min']) if data['salary_min'] else None
                except:
                    data['salary_min'] = None
            
            if data.get('salary_max'):
                try:
                    data['salary_max'] = int(data['salary_max']) if data['salary_max'] else None
                except:
                    data['salary_max'] = None
            
            if data.get('recruiter_id'):
                try:
                    recruiter_id = int(data['recruiter_id'])
                    recruiter = User.query.get(recruiter_id)
                    if not recruiter or recruiter.role != 'recruiter':
                        return jsonify({'success': False, 'message': 'Recruiter không hợp lệ'}), 400
                    data['recruiter_id'] = recruiter_id
                except (ValueError, TypeError):
                    return jsonify({'success': False, 'message': 'Recruiter ID không hợp lệ'}), 400
        
        if 'title' in data:
            job.title = data['title']
        if 'description' in data:
            job.description = data['description']
        if 'requirements' in data:
            job.requirements = data['requirements']
        if 'location' in data:
            job.location = data['location']
        if 'salary_min' in data:
            job.salary_min = data['salary_min']
        if 'salary_max' in data:
            job.salary_max = data['salary_max']
        if 'category_id' in data:
            category_id = data['category_id']
            if category_id:
                category = JobCategory.query.get(category_id)
                if not category:
                    category_id = None
            job.category_id = category_id
        if 'employment_type' in data:
            job.employment_type = data['employment_type']
        if 'is_active' in data:
            job.is_active = data['is_active']
        if 'recruiter_id' in data:
            job.recruiter_id = data['recruiter_id']
        if 'deadline' in data:
            if data['deadline']:
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
        
        if 'company_logo' in request.files:
            logo_file = request.files['company_logo']
            if logo_file and logo_file.filename != '':
                try:
                    if job.company_logo:
                        old_logo_path = os.path.join('Flask_CVProject', 'app', job.company_logo.lstrip('/'))
                        if os.path.exists(old_logo_path):
                            try:
                                os.remove(old_logo_path)
                            except:
                                pass
                    
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

@admin_bp.route('/api/jobs/<int:job_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_job(job_id):
    try:
        admin = check_admin_role()
        if not admin:
            return jsonify({'success': False, 'message': 'Chỉ admin mới có quyền truy cập'}), 403
        
        job = JobPosting.query.get_or_404(job_id)
        
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

@admin_bp.route('/api/jobs/<int:job_id>/applications', methods=['GET'])
@jwt_required()
def admin_get_job_applications(job_id):
    try:
        admin = check_admin_role()
        if not admin:
            return jsonify({'success': False, 'message': 'Chỉ admin mới có quyền truy cập'}), 403
        
        job = JobPosting.query.get_or_404(job_id)
        
        # Lấy query parameters
        status = request.args.get('status')
        category_id = request.args.get('category_id', type=int)
        sort_by = request.args.get('sort_by', 'date')
        
        # Base query
        query = JobApplication.query.filter_by(job_posting_id=job_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if category_id:
            query = query.join(CV).filter(CV.predicted_category_id == category_id)
        
        if sort_by == 'confidence':
            query = query.join(ClassificationLog, JobApplication.cv_id == ClassificationLog.cv_id)\
                         .order_by(desc(ClassificationLog.confidence))
        elif sort_by == 'category':
            query = query.join(CV).order_by(CV.predicted_category_id)
        else:
            query = query.order_by(desc(JobApplication.applied_at))
        
        applications = query.all()
        
        applications_list = []
        for app in applications:
            cv = app.cv
            category_name = cv.category.name if cv.category else None
            
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

@admin_bp.route('/api/jobs/<int:job_id>/top-cvs', methods=['GET'])
@jwt_required()
def admin_get_top_cvs(job_id):
    """API lấy top CV phù hợp với job (admin có thể xem tất cả)"""
    try:
        admin = check_admin_role()
        if not admin:
            return jsonify({'success': False, 'message': 'Chỉ admin mới có quyền truy cập'}), 403
        
        job = JobPosting.query.get_or_404(job_id)
        
        limit = request.args.get('limit', type=int, default=100)
        
        job_category_id = job.category_id
        
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
        
        top_cvs = []
        for cv, confidence, category_name, app_id, app_status, app_date in applied_results:
            confidence_score = float(confidence) if confidence else 0.0
            
            match_score = confidence_score
            if job_category_id and cv.predicted_category_id == job_category_id:
                match_score = min(confidence_score + 0.3, 1.0)
            
            top_cvs.append({
                'cv_id': cv.id,
                'file_name': cv.file_name,
                'category': category_name or 'Chưa phân loại',
                'category_id': cv.predicted_category_id,
                'confidence': confidence_score,
                'uploaded_at': cv.uploaded_at.isoformat() if cv.uploaded_at else None,
                'has_applied': True,
                'application_id': app_id,
                'application_status': app_status,
                'application_date': app_date.isoformat() if app_date else None,
                'match_score': match_score
            })
        
        top_cvs.sort(key=lambda x: -x['match_score'])
        top_cvs = top_cvs[:limit]
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'job_title': job.title,
            'job_category_id': job_category_id,
            'job_category_name': job.category.name if job.category else None,
            'top_cvs': top_cvs,
            'total': len(top_cvs)
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting top CVs: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi tải top CV: {str(e)}'
        }), 500

@admin_bp.route('/api/recruiters', methods=['GET'])
@jwt_required()
def admin_get_recruiters():
    try:
        admin = check_admin_role()
        if not admin:
            return jsonify({'success': False, 'message': 'Chỉ admin mới có quyền truy cập'}), 403
        
        recruiters = User.query.filter_by(role='recruiter', is_active=True).order_by(User.full_name).all()
        
        recruiters_list = []
        for recruiter in recruiters:
            recruiters_list.append({
                'id': recruiter.id,
                'email': recruiter.email,
                'full_name': recruiter.full_name
            })
        
        return jsonify({
            'success': True,
            'recruiters': recruiters_list
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting recruiters: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Lỗi khi tải danh sách nhà tuyển dụng: {str(e)}'
        }), 500

