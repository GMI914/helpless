from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user
import os
from dbase import User, Post, GalleryPhoto
from forms import NewPostForm
from app import app, db, photos


@app.route('/')
@app.route('/index')
def index():
    posts = Post.query.all()
    return render_template('index.html', posts=posts)


@app.route('/my_posts')
@login_required
def my_posts():
    posts = Post.query.filter_by(user_id=current_user.id)
    return render_template('my_posts.html', posts=posts, current_user=current_user)


@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = NewPostForm()

    if form.validate_on_submit():
        post = Post(user_id=current_user.id, title=form.title.data, content=form.content.data)
        db.session.add(post)
        db.session.commit()
        if form.photo.data:
            cur_post = Post.query.filter_by(user_id=current_user.id, title=form.title.data).order_by('id')[-1]
            img_name = photos.save(form.photo.data, name='blog_' + str(cur_post.id) + '.jpeg')
            cur_post.photo = '/media/img/' + img_name
        db.session.commit()

        return redirect(url_for('my_posts'))

    return render_template('new_post.html', form=form)


@app.route('/delete/<id>')
@login_required
def delete(id):
    if Post.query.filter_by(id=id, user_id=current_user.id).first():
        if Post.query.filter_by(id=id).first().photo:
            _dir = Post.query.filter_by(id=id).first().photo[1:]
            os.remove(_dir)
        Post.query.filter_by(id=id).delete()
        db.session.commit()
    return redirect(url_for('my_posts'))


@app.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    form = NewPostForm()
    if Post.query.filter_by(id=id, user_id=current_user.id).first():
        post = Post.query.filter_by(id=id).first()
        if request.method == 'POST':
            post = Post.query.filter_by(id=id).first()
            post.title = form.title.data
            post.content = form.content.data
            if form.photo.data:
                cur_post = Post.query.filter_by(id=id).first()
                if cur_post.photo:
                    _dir = cur_post.photo[1:]
                    os.remove(_dir)
                img_name = photos.save(form.photo.data, name='blog_' + str(cur_post.id) + '.jpeg')
                cur_post.photo = '/media/img/' + img_name
            db.session.commit()
            return redirect(url_for('my_posts'))
        form.title.data = post.title
        form.content.data = post.content
    return render_template('edit.html', form=form, id=id)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST' and 'photo' in request.files:
        new_photo = GalleryPhoto(user_id=current_user.id)
        db.session.add(new_photo)
        db.session.commit()
        cur_photo = GalleryPhoto.query.filter_by(user_id=current_user.id).order_by('id')[-1]
        photo_name = photos.save(request.files['photo'], name='gallery_' + str(cur_photo.id) + '.jpeg')
        cur_photo.name = '/media/img/' + photo_name
        db.session.commit()

        return redirect(url_for('my_gallery'))
    return render_template('upload.html')


@app.route('/upload_prof', methods=['GET', 'POST'])
@login_required
def upload_prof():
    if request.method == 'POST' and 'photo' in request.files:
        new_photo = GalleryPhoto(user_id=current_user.id)
        db.session.add(new_photo)
        db.session.commit()
        cur_photo = GalleryPhoto.query.filter_by(user_id=current_user.id).order_by('id')[-1]
        photo_name = photos.save(request.files['photo'], name='gallery_' + str(cur_photo.id) + '.jpeg')
        cur_photo.name = '/media/img/' + photo_name
        current_user.avatar = '/media/img/' + photo_name
        db.session.commit()

        return redirect(url_for('my_posts'))
    return redirect(url_for('edit_prof'))


@app.route('/my_gallery')
@login_required
def my_gallery():
    photo = GalleryPhoto.query.filter_by(user_id=current_user.id)
    return render_template('my_gallery.html', photos=photo, current_user=current_user)


@app.route('/del_img/<id>')
@login_required
def del_img(id):
    if GalleryPhoto.query.filter_by(id=id, user_id=current_user.id).first().name == current_user.avatar:
        current_user.avatar = '/media/img/default_p.jpeg'
        db.session.commit()
        return redirect(url_for('my_posts'))
    else:
        _dir = GalleryPhoto.query.filter_by(id=id).first().name[1:]
        os.remove(_dir)
        GalleryPhoto.query.filter_by(id=id).delete()
        db.session.commit()
    return redirect(url_for('my_gallery'))


@app.route('/edit_prof')
@login_required
def edit_prof():
    return render_template('edit_prof.html', photo=GalleryPhoto.query.filter_by(name=current_user.avatar).first())
