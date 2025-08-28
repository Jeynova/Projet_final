[tags: flask, django, sqlalchemy, orm]

# Flask avec patterns Django

## Modèles SQLAlchemy style Django ORM

```python
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations Django-style
    posts = db.relationship('Post', backref='author', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'

    # Méthodes Django-style
    @classmethod
    def get_by_email(cls, email):
        return cls.query.filter_by(email=email).first()
```

## Blueprint structure (Django apps)

```python
# src/routes/users.py
from flask import Blueprint, request, jsonify
from ..models import User, db

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('/', methods=['GET'])
def list_users():
    users = User.query.all()
    return jsonify([{'id': u.id, 'email': u.email} for u in users])

@users_bp.route('/', methods=['POST'])
def create_user():
    data = request.get_json()
    user = User(email=data['email'], password_hash=data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'id': user.id}), 201
```

## Main app registration (Django urls.py style)

```python
# src/main.py
from flask import Flask
from .models import db
from .routes.users import users_bp
from .routes.posts import posts_bp

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://...'

    # Initialize extensions
    db.init_app(app)

    # Register blueprints (Django apps)
    app.register_blueprint(users_bp)
    app.register_blueprint(posts_bp)

    return app
```

## Admin-style interface

```python
# src/admin.py
from flask import Blueprint, render_template
from .models import User, Post

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
def dashboard():
    stats = {
        'users': User.query.count(),
        'posts': Post.query.count(),
    }
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/users')
def list_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)
```
