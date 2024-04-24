import click
from faker import Faker
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash
from .extensions import db

fake = Faker()

def read_file_to_string(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        print(f"文件未找到：{file_path}")
        return None
    except Exception as e:
        print(f"读取文件时出错：{e}")
        return None

@click.command('init-db')
@with_appcontext
def init_db_command():
    from .models import User, Post, Role, CodeDistribution
    db.drop_all()
    db.create_all()

    # 创建新用户
    user1 = User(username='john', password_hash=generate_password_hash('1234'))
    user2 = User(username='susan', password_hash=generate_password_hash('1234'))
    adminuser = User(username='admin', role=Role.ADMIN, password_hash=generate_password_hash('admin'))

    users = [
        User(username=fake.user_name(), role=Role.USER, password_hash=generate_password_hash('password'))
        for _ in range(10)
    ]
    db.session.add_all(users)
    db.session.add(user1)
    db.session.add(user2)
    db.session.add(adminuser)
    db.session.commit() 

    # 创建博客文章
    posts = [
        Post(title=fake.sentence(), body=fake.text(max_nb_chars=2000), author=user, position=_)
        for user in users
        for _ in range(5)  # 每个用户生成5篇文章
    ]
    db.session.add_all(posts)
    db.session.commit()

    import os
    oldc = read_file_to_string("tests/old_code.cpp")
    newc = read_file_to_string("tests/new_code.cpp")
    codes = [
        CodeDistribution(description=fake.user_name(), user=user, old_code=oldc, new_code=newc)
        for user in users
        for _ in range(5)
    ]
    db.session.add_all(codes)
    db.session.commit()

    click.echo('Initialized the database.')