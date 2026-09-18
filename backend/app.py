import os
from pathlib import Path
from flask import Flask, render_template, send_from_directory, session, request
from backend.config import Config, BASE_DIR
from backend.database.db import db

def create_app(config_class=Config):
    # Paths for templates and static assets
    template_dir = BASE_DIR / 'frontend' / 'templates'
    static_dir = BASE_DIR / 'frontend' / 'static'

    app = Flask(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir)
    )
    
    # Load configuration
    app.config.from_object(config_class)
    app.config['SQLALCHEMY_DATABASE_URI'] = config_class.get_database_uri()

    # Ensure uploads directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize SQLAlchemy
    db.init_app(app)

    # Register Route Blueprints
    from backend.routes.auth import auth_bp
    from backend.routes.applicant import applicant_bp
    from backend.routes.officer import officer_bp
    from backend.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(applicant_bp)
    app.register_blueprint(officer_bp)
    app.register_blueprint(api_bp)

    # Route for serving uploaded documents
    @app.route('/uploads/documents/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # Global Context Processor: Notification count & session info
    @app.context_processor
    def inject_globals():
        unread_notifs = 0
        recent_notifs = []
        user_role = session.get('role')
        user_name = session.get('full_name')
        
        if 'user_id' in session:
            try:
                from backend.models.models import Notification
                unread_notifs = Notification.query.filter_by(user_id=session['user_id'], is_read=False).count()
                recent_notifs = Notification.query.filter_by(user_id=session['user_id']).order_by(Notification.created_at.desc()).limit(5).all()
            except Exception:
                unread_notifs = 0
                recent_notifs = []

        return {
            'unread_notifications_count': unread_notifs,
            'recent_notifications': recent_notifs,
            'current_user_role': user_role,
            'current_user_name': user_name,
            'current_path': request.path
        }

    # Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('public/error.html', error_code=403, error_title="Access Forbidden", error_message="You do not have permission to access this resource."), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('public/error.html', error_code=404, error_title="Page Not Found", error_message="The requested page could not be located."), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('public/error.html', error_code=500, error_title="Internal Server Error", error_message="Something went wrong on our end. Please try again later."), 500

    return app
