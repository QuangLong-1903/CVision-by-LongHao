import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Flask, jsonify, request
from app.extensions import db, migrate, jwt, cors

def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object('config.Config')
    
    # Đảm bảo Flask sử dụng UTF-8 encoding
    flask_app.config['JSON_AS_ASCII'] = False
    flask_app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
    
    # Đảm bảo request encoding là UTF-8
    @flask_app.before_request
    def before_request():
        if request.is_json:
            # Đảm bảo JSON được decode đúng UTF-8
            try:
                if hasattr(request, 'get_json'):
                    request.get_json(force=True)
            except:
                pass

    # Khởi tạo các extension
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    jwt.init_app(flask_app)
    cors.init_app(flask_app)
    
    # Event listener để đảm bảo Unicode được xử lý đúng với SQL Server
    try:
        from sqlalchemy import event
        from sqlalchemy.pool import Pool
        import pyodbc
        
        @event.listens_for(Pool, "connect")
        def set_sqlserver_python_unicode(dbapi_conn, connection_record):
            """Đảm bảo pyodbc connection sử dụng Unicode đúng cách"""
            try:
                # Set encoding cho pyodbc để hỗ trợ Unicode
                # QUAN TRỌNG: Điều này đảm bảo pyodbc xử lý Unicode đúng
                # Với SQL Server, nên dùng cp1252 hoặc utf-8 tùy vào collation
                # Thử UTF-8 trước, nếu không được thì dùng cp1252
                try:
                    dbapi_conn.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8', errors='replace')
                    dbapi_conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8', errors='replace')
                    dbapi_conn.setencoding(encoding='utf-8')
                except:
                    # Fallback: dùng cp1252 nếu UTF-8 không hoạt động
                    try:
                        dbapi_conn.setdecoding(pyodbc.SQL_CHAR, encoding='cp1252', errors='replace')
                        dbapi_conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8', errors='replace')
                        dbapi_conn.setencoding(encoding='utf-8')
                    except:
                        pass
            except Exception as e:
                # Nếu không có pyodbc hoặc method không tồn tại, bỏ qua
                pass
    except ImportError:
        # Nếu không có pyodbc, bỏ qua
        pass
    
    # JWT Error Handlers
    from flask_jwt_extended.exceptions import JWTDecodeError, NoAuthorizationError, InvalidHeaderError
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired', 'message': 'Please login again'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token', 'message': str(error)}), 422
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Authorization required', 'message': 'Please login first'}), 401

    # Import models
    import app.models.user
    import app.models.cv
    import app.models.classification_log
    import app.models.cvprocessingqueue
    import app.models.jobcategory
    import app.models.categorystatistic
    import app.models.mlmodel
    import app.models.useractivitylog
    import app.models.systemlog
    import app.models.jobposting
    import app.models.jobapplication
    import app.models.cvdata

    from app.routes.cv_routes import cv_bp
    from app.routes.user_routes import user_bp  

    flask_app.register_blueprint(cv_bp)
    flask_app.register_blueprint(user_bp, url_prefix="/api/users")
    
    from app.routes.auth_routes import auth_bp
    flask_app.register_blueprint(auth_bp)
    
    from app.routes.recruiter_routes import recruiter_bp
    flask_app.register_blueprint(recruiter_bp)
    
    from app.routes.job_routes import job_bp
    flask_app.register_blueprint(job_bp)
    
    from app.routes.cv_builder_routes import cv_builder_bp
    flask_app.register_blueprint(cv_builder_bp)
    
    from app.routes.admin_routes import admin_bp
    flask_app.register_blueprint(admin_bp)
    
    # Middleware để đảm bảo tất cả responses có charset UTF-8
    @flask_app.after_request
    def after_request(response):
        # Set charset UTF-8 cho tất cả text responses
        if response.content_type and 'text' in response.content_type:
            response.charset = 'utf-8'
        # Set charset UTF-8 cho JSON responses
        if response.content_type and 'json' in response.content_type:
            response.charset = 'utf-8'
        return response

    return flask_app
