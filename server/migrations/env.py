from flask import Flask, request, session, jsonify, current_app
from alembic import context
from models import User, Article
from datetime import timedelta

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "your_secret_key_here"  

# Configure session expiration
app.permanent_session_lifetime = timedelta(days=1)

# Authorization helper
def get_current_user():
    user_id = session.get("user_id")
    if user_id:
        return User.query.get(user_id)
    return None

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    session["user_id"] = user.id
    session.permanent = True  # Set session expiration
    return jsonify({"message": f"Welcome, {user.username}!"}), 200

@app.route("/logout", methods=["DELETE"])
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Logged out successfully"}), 204

@app.route("/check_session", methods=["GET"])
def check_session():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify({"username": user.username}), 200

@app.route("/member_only_articles", methods=["GET"])
def member_only_articles():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    articles = Article.query.filter_by(is_member_only=True).all()
    return jsonify([article.to_dict() for article in articles]), 200

@app.route("/member_only_article/<int:article_id>", methods=["GET"])
def member_only_article(article_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    article = Article.query.filter_by(id=article_id, is_member_only=True).first()
    if not article:
        return jsonify({"error": "Article not found or not restricted"}), 404

    return jsonify(article.to_dict()), 200

# Migration functions
config = context.config
config.set_main_option(
    'sqlalchemy.url',
    str(current_app.extensions['migrate'].db.get_engine().url).replace('%', '%%')
)
target_db = current_app.extensions['migrate'].db

def get_metadata():
    return target_db.metadatas.get(None, target_db.metadata)

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=get_metadata(), literal_binds=True)
    
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = current_app.extensions['migrate'].db.get_engine()
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=get_metadata())
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()