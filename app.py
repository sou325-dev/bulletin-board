from flask import Flask, render_template, request, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from datetime import timedelta, timedelta

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bbs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024 * 1024 # 画像の容量制限(現在1スレッドで500GBまで使える)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm'}

db = SQLAlchemy(app)


class Board(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)


class Thread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    board_id = db.Column(db.Integer, db.ForeignKey('board.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    body = db.Column(db.Text, nullable=True)
    image_filename = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    boards = Board.query.order_by(Board.name).all()
    return render_template('index.html', boards=boards)


@app.route('/board/add', methods=['POST'])
def add_board():
    name = request.form.get('name', '').strip()
    if name and not Board.query.filter_by(name=name).first():
        db.session.add(Board(name=name))
        db.session.commit()
    return redirect(url_for('index'))


@app.route('/board/<int:board_id>')
def board_view(board_id):
    board = Board.query.get_or_404(board_id)
    threads = Thread.query.filter_by(board_id=board_id).order_by(Thread.created_at.desc()).all()
    return render_template('board.html', board=board, threads=threads)


@app.route('/thread/add/<int:board_id>', methods=['POST'])
def add_thread(board_id):
    title = request.form.get('title', '').strip()
    name = request.form.get('name', '').strip() or request.cookies.get('username', '名無しさん')
    body = request.form.get('body', '').strip()
    file = request.files.get('image')

    filename = None
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    if title:
        t = Thread(board_id=board_id, title=title)
        db.session.add(t)
        db.session.commit()

        if body or filename:
            p = Post(thread_id=t.id, name=name, body=body, image_filename=filename)
            db.session.add(p)
            db.session.commit()

    
    resp = make_response(redirect(url_for('board_view', board_id=board_id)))
    resp.set_cookie('username', name, max_age=60*60*24*365) 
    return resp


@app.route('/thread/<int:thread_id>')
def thread_view(thread_id):
    thread = Thread.query.get_or_404(thread_id)
    posts = Post.query.filter_by(thread_id=thread_id).order_by(Post.created_at.asc()).all()
    board = Board.query.get(thread.board_id)
    return render_template('thread.html', thread=thread, posts=posts, board=board)


@app.route('/post/add/<int:thread_id>', methods=['POST'])
def add_post(thread_id):
    name = request.form.get('name', '').strip() or request.cookies.get('username', '名無しさん')
    body = request.form.get('body', '').strip()
    file = request.files.get('image')

    filename = None
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    if body or filename:
        p = Post(thread_id=thread_id, name=name, body=body, image_filename=filename)
        db.session.add(p)
        db.session.commit()

    resp = make_response(redirect(url_for('thread_view', thread_id=thread_id)))
    expires = datetime.utcnow() + timedelta(days=365*100) # 100年後にユーザー名のリセットする
    resp.set_cookie('username', name, expires=expires)

    return resp

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='192.168.3.25', port=5000, debug=True)
