from flask_admin import AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import Select2Widget
from wtforms import SelectField
from flask_login import current_user
from flask import redirect, url_for, request
from .models import Role, User

class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.role == Role.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('main.login', next=request.url))
    
class PostModelView(ModelView):
    column_list = ('title', 'body', 'user_id')
    form_columns = ('title', 'body', 'user')
    form_extra_fields = {
        'user': SelectField('User', choices=[], widget=Select2Widget())
    }

    def on_form_prefill(self, form, id):
        form.user.choices = [(user.id, user.username) for user in User.query.all()]

    def scaffold_form(self):
        form_class = super(PostModelView, self).scaffold_form()
        form_class.user = SelectField('User', choices=[], widget=Select2Widget())
        return form_class
    
    def on_model_change(self, form, model, is_created):
        model.user_id = form.user.data

    def is_accessible(self):
        return current_user.role == Role.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('main.login', next=request.url))

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.role == Role.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('main.login', next=request.url))
