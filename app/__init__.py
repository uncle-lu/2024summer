from flask import Flask
from . import admin_views
from config import Config
from flask_admin import Admin
from .extensions import db, login_manager
from .admin import MyModelView, MyAdminIndexView, PostModelView
from .models import User, Post, CodeDistribution
from .command import init_db_command


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from . import views
    app.register_blueprint(views.bp)
    app.register_blueprint(admin_views.admin_bp)

    admin = Admin(app, index_view=MyAdminIndexView(), template_mode="bootstrap4")
    admin.add_view(MyModelView(User, db.session))
    admin.add_view(PostModelView(Post, db.session))
    admin.add_view(MyModelView(CodeDistribution, db.session))

    app.cli.add_command(init_db_command)
    return app