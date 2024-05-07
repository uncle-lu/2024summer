from flask import render_template, redirect, url_for, flash, request, Blueprint, g, jsonify, current_app, abort, send_file
from flask_login import current_user, login_user, login_required, logout_user
from werkzeug.utils import secure_filename
from .models import User, Post, CodeDistribution, Task, FileUpload
from .forms import LoginForm
from .extensions import db
import difflib, os

bp = Blueprint('main', __name__)

def get_all_posts(user_id):
    return Post.query.filter_by(user_id=user_id).order_by(Post.position).all()

def get_post(post_id):
    return Post.query.get(post_id)

@bp.before_request
def load_user():
    if current_user.is_authenticated:
        g.user = current_user
    else:
        g.user = None  # 确保 g.user 总是存在

@bp.context_processor
def inject_user():
    return {'user': g.user}

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash('登录成功', "seccess")
            return redirect(url_for('main.index'))
        else:
            flash('错误的用户名或密码')
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/posts')
@login_required
def posts():
    posts = get_all_posts(current_user.id)
    selected_post = None
    post_id = request.args.get('post_id')
    if post_id:
        selected_post = get_post(post_id)
        if selected_post.user_id != current_user.id:
            selected_post = None
    return render_template('base_posts.html', posts=posts, selected_post=selected_post)

@bp.route('/update_position', methods=['POST'])
@login_required
def update_position():
    post_positions = request.json['positions']
    for position, post_id in enumerate(post_positions):
        post = Post.query.get(post_id)
        if post and post.user_id == current_user.id:
            post.position = position
    db.session.commit()
    return jsonify(success=True)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    posts = get_all_posts(current_user.id)
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        post = Post(title=title, body=body, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main.posts', post_id=post.id))
    return render_template('edit_post.html', posts=posts)

@bp.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    posts = get_all_posts(current_user.id)
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        post.title = request.form['title']
        post.body = request.form['body']
        db.session.commit()
        return redirect(url_for('main.posts', post_id=post_id))
    return render_template('edit_post.html', post=post, posts=posts)

@bp.route('/code_diffs')
@login_required
def view_code_diffs():
    code_diffs = CodeDistribution.query.filter_by(user_id=current_user.id).order_by(CodeDistribution.timestamp).all()
    selected_diff = None
    diff_html = None
    diff_id = request.args.get('diff_id')
    if diff_id:
        selected_diff = CodeDistribution.query.filter_by(id=diff_id, user_id=current_user.id).first()
        if selected_diff :
            diff = difflib.unified_diff(
                selected_diff.old_code.splitlines(keepends=True),
                selected_diff.new_code.splitlines(keepends=True),
                fromfile='old_code.cpp', tofile='new_code.cpp', lineterm='',
                n = 10000
            )
            diff_html = '\n'.join(diff)
    return render_template('view_code_diffs.html', code_diffs=code_diffs, selected_diff=selected_diff, diff_html=diff_html)

@bp.route('/tasks')
@login_required
def list_tasks():
    tasks = Task.query.order_by(Task.is_active.desc(), Task.timestamp.desc()).all()
    for task in tasks:
        task.upload = FileUpload.query.filter_by(task_id=task.id, user_id=current_user.id).first()
    return render_template('tasks.html', tasks=tasks)

@bp.route('/download_file/<int:file_id>')
@login_required
def download_file(file_id):
    file = FileUpload.query.get_or_404(file_id)
    if file.user_id != current_user.id:
        abort(403)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
    if not os.path.exists(file_path):
        abort(404, description=f"File not found. {file_path}")
    try:
        return send_file(file_path, as_attachment=True, download_name=file.filename)
    except Exception as e:
        abort(500, description=str(e))


@bp.route('/tasks/<int:task_id>/upload', methods=['GET', 'POST'])
@login_required
def upload_file(task_id):
    task = Task.query.get_or_404(task_id)
    if not task.is_active:
        flash('This task is currently inactive and cannot accept uploads.', 'warning')
        return redirect(url_for('main.list_tasks'))

    if request.method == 'POST':
        file = request.files['file']
        if file:
            existing_upload = FileUpload.query.filter_by(user_id=current_user.id, task_id=task_id).first()
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            if existing_upload:
                os.remove(existing_upload.filepath)
                existing_upload.filename = filename
                existing_upload.filepath = filepath
            else:
                upload = FileUpload(filename=filename, filepath=filepath, user_id=current_user.id, task_id=task_id)
                db.session.add(upload)
            file.save(filepath)
            db.session.commit()
            flash('File uploaded successfully', 'success')
            return redirect(url_for('main.list_tasks'))
    return redirect(url_for('main.list_tasks'))