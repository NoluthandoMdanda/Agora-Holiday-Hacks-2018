from flask import Blueprint
from flask import (render_template, url_for, flash,
                   redirect, request, abort, Blueprint)
from flask_login import current_user, login_required
from flask_platform import db
from flask_platform.models import Show
from flask_platform.shows.forms import ShowForm

shows = Blueprint('shows', __name__)

@shows.route("/show/new", methods=['GET', 'POST'])
@login_required
def new_show():
    form = ShowForm()
    if form.validate_on_submit():
        show = Show(title=form.title.data, description=form.description.data, author=current_user, 
            category=form.category.data, show_language=form.show_language.data)
        db.session.add(show)
        db.session.commit()
        flash('Your show has been created!', 'success')
        return redirect(url_for('main.home'))
    return render_template('create_show.html', title='New Show',
                           form=form, legend='New Show')


@shows.route("/show/<int:show_id>")
def show(show_id):
    show = Show.query.get_or_404(show_id)
    return render_template('show.html', title=show.title, show=show)


@shows.route("/show/<int:show_id>/update", methods=['GET', 'POST'])
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
        return redirect(url_for('shows.show', show_id=show.id))
    elif request.method == 'GET':
        show.title = show.title
        show.description = show.description
        show.category = show.category
        show.show_language = show.show_language
    return render_template('create_show.html', title='Update Show',
                           form=form, legend='Update Show')


@shows.route("/show/<int:show_id>/delete", methods=['POST'])
@login_required
def delete_show(show_id):
    show = Show.query.get_or_404(show_id)
    if show.author != current_user:
        abort(403)
    db.session.delete(show)
    db.session.commit()
    flash('Your show has been deleted!', 'success')
    return redirect(url_for('main.home'))