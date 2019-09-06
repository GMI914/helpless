from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from flask_uploads import UploadSet, configure_uploads, IMAGES
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'iloveyou!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
photos = UploadSet('photos', IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = 'static/img'
configure_uploads(app, photos)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))
    posts = db.relationship('Posts', backref='post_author', lazy=True)
    photo = db.relationship('Photos', backref='photo_author', lazy=True)


class Posts(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(50))
    content = db.Column(db.Text(3000))
    date_posted = db.Column(db.String(20), nullable=False, default=datetime.now().strftime("%m/%d/%Y"))
    photo = db.relationship('Photos', backref='posts_photo', lazy=True)


class Photos(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, default='/static/img/default_p.jpeg')
    type = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')


class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])


class NewPostForm(FlaskForm):
    title = StringField('title', validators=[InputRequired(), Length(min=1, max=50)])
    content = TextAreaField('content', validators=[Length(min=1, max=3000)])


@app.route('/')
@app.route('/index')
def index():
    posts = Posts.query.all()
    return render_template('index.html', posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('my_posts'))

        return render_template('login.html', form=form, error='invalid username or password')

    return render_template('login.html', form=form, error='')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        if User.query.filter_by(username=username).first():
            return render_template('signup.html', error='arsebobs ukve dzmao', form=form)
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        new_photo = Photos(user_id=User.query.filter_by(username=form.username.data).first().id, type='profile')
        db.session.add(new_photo)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('signup.html', form=form, error='')


@app.route('/my_posts')
@login_required
def my_posts():
    posts = Posts.query.filter_by(user_id=current_user.id)
    return render_template('my_posts.html', posts=posts, current_user=current_user,
                           photo=Photos.query.filter_by(user_id=current_user.id, type='profile').first())


@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = NewPostForm()

    if form.validate_on_submit():
        post = Posts(user_id=current_user.id, title=form.title.data, content=form.content.data)
        db.session.add(post)
        db.session.commit()

        posts = Posts.query.filter_by(user_id=current_user.id)
        return redirect(url_for('my_posts'))

    return render_template('new_post.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/delete/<id>')
@login_required
def delete(id):
    if Posts.query.filter_by(id=id, user_id=current_user.id).first():
        Posts.query.filter_by(id=id).delete()
        db.session.commit()
    return redirect(url_for('my_posts'))


@app.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    form = NewPostForm()
    if Posts.query.filter_by(id=id, user_id=current_user.id).first():
        post = Posts.query.filter_by(id=id).first()
        if request.method == 'POST':
            post = Posts.query.filter_by(id=id).first()
            post.title = form.title.data
            post.content = form.content.data
            db.session.commit()
            return redirect(url_for('my_posts'))
    form.title.data = post.title
    form.content.data = post.content
    return render_template('edit.html', form=form, id=id)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        new_photo = Photos(user_id=current_user.id, type='gallery')
        db.session.add(new_photo)
        db.session.commit()
        new_photo = Photos.query.filter_by(user_id=current_user.id, type='gallery').order_by('id')[-1]
        photo_name = photos.save(request.files['photo'], name=str(new_photo.id) + '.jpeg')
        new_photo.name = '/static/img/' + photo_name
        db.session.commit()

        return redirect(url_for('my_gallery'))
    return render_template('upload.html')


@app.route('/upload_prof', methods=['GET', 'POST'])
@login_required
def upload_prof():
    if request.method == 'POST' and 'photo' in request.files:
        old_photo = Photos.query.filter_by(user_id=current_user.id, type='profile').first()
        if old_photo.name == '/static/img/default_p.jpeg':
            new_photo = photos.save(request.files['photo'],
                                    name=str(Photos.query.filter_by(user_id=current_user.id,
                                                                    type='profile').first().id)+'.jpeg')
            old_photo.name = '/static/img/'+new_photo
            db.session.commit()
        else:
            old_photo.type = 'gallery'
            new_photo = Photos(user_id=current_user.id, type='profile')
            db.session.add(new_photo)
            db.session.commit()
            new_photo_name = photos.save(request.files['photo'],
                                         name=str(Photos.query.filter_by(user_id=current_user.id,
                                                                         type='profile').first().id) + '.jpeg')
            new_photo = Photos.query.filter_by(user_id=current_user.id, type='profile').first()
            new_photo.name = '/static/img/' + new_photo_name
            db.session.commit()

        return redirect(url_for('my_posts'))
    return redirect(url_for('edit_prof'))


@app.route('/my_gallery')
@login_required
def my_gallery():
    photoz = Photos.query.filter_by(user_id=current_user.id, type='gallery')
    return render_template('my_gallery.html', photos=photoz, current_user=current_user)


@app.route('/del_img/<id>')
@login_required
def del_img(id):
    if Photos.query.filter_by(id=id).first().name != '/static/img/default_p.jpeg':
        if Photos.query.filter_by(id=id, user_id=current_user.id).first().type == 'profile':
            _dir = Photos.query.filter_by(id=id).first().name[1:]
            os.remove(_dir)
            cur_photo = Photos.query.filter_by(id=id).first()
            cur_photo.name = '/static/img/default_p.jpeg'
            db.session.commit()
            return redirect(url_for('my_posts'))
        if Photos.query.filter_by(id=id, user_id=current_user.id).first().type == 'gallery':
            _dir = Photos.query.filter_by(id=id).first().name[1:]
            os.remove(_dir)
            Photos.query.filter_by(id=id, type='gallery').delete()
            db.session.commit()
    return redirect(url_for('my_gallery'))


@app.route('/edit_prof')
@login_required
def edit_prof():
    return render_template('edit_prof.html',
                           photo=Photos.query.filter_by(user_id=current_user.id, type='profile').first())


if __name__ == '__main__':
    app.run(debug=True)
