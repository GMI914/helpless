from app import db
from datetime import datetime
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=False)
    password = db.Column(db.String(80))
    posts = db.relationship('Post', backref='post_author', lazy=True)
    gallery_photos = db.relationship('GalleryPhoto', backref='photo_author', lazy=True)

    avatar = db.Column(db.String(255), nullable=False, default='/media/img/default_p.jpeg')


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(50))
    content = db.Column(db.Text(3000))
    date_posted = db.Column(db.String(20), nullable=False, default=datetime.now().strftime("%m/%d/%Y"))
    photo = db.Column(db.String(225), nullable=True)


class GalleryPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(225), nullable=False, default='/media/img/default_p.jpeg')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_posted = db.Column(db.String(20), nullable=False, default=datetime.now().strftime("%m/%d/%Y"))
