from flask import render_template, request, Blueprint
from flask_platform.models import Show


main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    shows = Show.query.order_by(Show.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', shows=shows)

@main.route("/about")
def about():
    return render_template('about.html', title='About')



