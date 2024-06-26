from flask import Blueprint, render_template, request, redirect, url_for, flash, g, abort, jsonify
from flask_login import login_required, current_user
from .models import User, CodeDistribution, Role, Task, FileUpload
from .forms import TaskForm
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

@admin_bp.route('/admin/tasks/new', methods=['GET', 'POST'])
@login_required
def new_task():
    if not current_user.role == Role.ADMIN:
        return redirect(url_for('main.index'))
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(title=form.title.data, description=form.description.data)
        db.session.add(task)
        db.session.commit()
        flash('Task has been created', 'success')
        return redirect(url_for('main.list_tasks'))
    return render_template('create_task.html', form=form)

@admin_bp.route('/admin/tasks')
@login_required
def list_tasks():
    if not current_user.role == Role.ADMIN:
        return redirect(url_for('main.index'))
    tasks = Task.query.order_by(Task.is_active.desc(), Task.timestamp.desc()).all()
    users = User.query.all()
    for task in tasks:
        task.uploads = []
        for user in users:
            task.uploads.append({
                "user": user,
                "isload": FileUpload.query.filter_by(task_id=task.id, user_id=user.id).first()
                })
        task.upload = FileUpload.query.filter_by(task_id=task.id, user_id=current_user.id).first()
    return render_template('admin_tasks.html', tasks=tasks)

@admin_bp.route('/toggle_task_active/<int:task_id>', methods=['POST'])
@login_required
def toggle_task_active(task_id):
    if not current_user.role == Role.ADMIN:
        abort(403)  # 确保只有管理员可以更改任务状态

    task = Task.query.get_or_404(task_id)
    new_status = request.form.get('is_active') == '1'  # 前端发送1表示激活，0表示不激活
    task.is_active = bool(new_status)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Task status updated',
        'task_id': task_id,
        'is_active': task.is_active
    })