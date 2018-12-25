import os
import secrets
from PIL import Image

from flask import render_template, url_for, flash, redirect, request, abort
from flask_platform import app, db, bcrypt, mail
from flask_platform.forms import (RegistrationForm, LoginForm, UpdateAccountForm, 
                                ShowForm, RequestResetForm, ResetPasswordForm)
from flask_platform.models import User, Show
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message


@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    shows = Show.query.order_by(Show.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', shows=shows)

@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, about=form.about.data, country=form.country.data, languages=form.languages.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (500, 500)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/account",  methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm() 
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.about = form.about.data
        current_user.country = form.country.data
        current_user.languages = form.languages.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.about.data = current_user.about
        form.country.data = current_user.country
        form.languages.data = current_user.languages
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


@app.route("/show/new", methods=['GET', 'POST'])
@login_required
def new_show():
    form = ShowForm()
    if form.validate_on_submit():
        show = Show(title=form.title.data, description=form.description.data, author=current_user, 
            category=form.category.data, show_language=form.show_language.data)
        db.session.add(show)
        db.session.commit()
        flash('Your show has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_show.html', title='New Show',
                           form=form, legend='New Show')


@app.route("/show/<int:show_id>")
def show(show_id):
    show = Show.query.get_or_404(show_id)
    return render_template('show.html', title=show.title, show=show)


@app.route("/show/<int:show_id>/update", methods=['GET', 'POST'])
@login_required
def update_show(show_id):
    show = Show.query.get_or_404(show_id)
    if show.author != current_user:
        abort(403)
    form = ShowForm()
    if form.validate_on_submit():
        show.title = form.title.data
        show.description = form.description.data
        show.category = form.category.data
        show.show_language = form.show_language.data
        db.session.commit()
        flash('Your show has been updated!', 'success')
        return redirect(url_for('show', show_id=show.id))
    elif request.method == 'GET':
        show.title = show.title
        show.description = show.description
        show.category = show.category
        show.show_language = show.show_language
    return render_template('create_show.html', title='Update Show',
                           form=form, legend='Update Show')


@app.route("/show/<int:show_id>/delete", methods=['POST'])
@login_required
def delete_show(show_id):
    show = Show.query.get_or_404(show_id)
    if show.author != current_user:
        abort(403)
    db.session.delete(show)
    db.session.commit()
    flash('Your show has been deleted!', 'success')
    return redirect(url_for('home'))

@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    shows = Show.query.filter_by(author=user)\
        .order_by(Show.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_shows.html', shows=shows, user=user)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Pulse Password Reset Request',
                  sender='luyanda23@gmail.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
    {url_for('reset_token', token=token, _external=True)}
    If you did not make this request then simply ignore this email and no changes will be made.
    '''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)