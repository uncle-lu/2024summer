from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from flask_login import login_required, current_user
from .models import User, CodeDistribution, Role
from .extensions import db
from datetime import datetime, timezone

admin_bp = Blueprint('myadmin', __name__)

@admin_bp.before_request
def load_user():
    if current_user.is_authenticated:
        g.user = current_user
    else:
        g.user = None  # 确保 g.user 总是存在

@admin_bp.context_processor
def inject_user():
    return {'user': g.user}

@admin_bp.route('/publish', methods=['GET', 'POST'])
@login_required
def publish_code():
    if not current_user.role == Role.ADMIN:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        old_code = request.form.get('old_code')
        new_code = request.form.get('new_code')
        user_id = request.form.get('user_id')
        description = request.form.get('description')

        code_diff = CodeDistribution(
            old_code=old_code,
            new_code=new_code,
            description=description,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id
        )
        db.session.add(code_diff)
        db.session.commit()
        flash('Code diff published successfully.', 'success')
        return redirect(url_for('myadmin.publish_code'))

    users = User.query.all()
    return render_template('publish_code.html', users=users)