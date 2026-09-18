from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify, abort

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Unauthorized. Please login.'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """
    Enforces that the current logged-in user belongs to one of the specified roles.
    Works for both web HTML routes and JSON REST endpoints.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'error': 'Unauthorized. Please login.'}), 401
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            user_role = session.get('role')
            if user_role not in allowed_roles:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'error': 'Forbidden: You do not have permission to perform this action.'}), 403
                flash('Access Denied: You are not authorized to view this page.', 'danger')
                if user_role == 'applicant':
                    return redirect(url_for('applicant.dashboard'))
                elif user_role in ['officer', 'admin']:
                    return redirect(url_for('officer.dashboard'))
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
