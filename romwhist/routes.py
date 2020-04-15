"""
This module implements routes.

author: Philippe Fajeau

"""
from flask import Blueprint
from . import controllers
from romwhist import app
from flask import render_template, request, flash, session, url_for, redirect
from .forms import LoginForm
from flask_login import current_user, login_user
from romwhist.models import User
from romwhist.extensions import db


@app.route("/")
@app.route("/index")
def index():
    # TODO - add here endpoint of resource where you want to land on page load. e.g.
    # return redirect(url_for("auth_blueprint.home"))
    return render_template("index.html")

@app.route("/base")
def base():
    # TODO - add here endpoint of resource where you want to land on page load. e.g.
    # return redirect(url_for("auth_blueprint.home"))
    return render_template("base.html")

@app.route("/phil")
def test():
    return render_template("index.html")

@app.route("/boot")
def bootex():
    return render_template("bootex.html")

@app.route("/login",methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    print ("Hello")
    if form.validate_on_submit():
        print ("Hello2")
        user = User.query.filter_by(username=form.username.data).first()
        if user is None:
            user = User(username=form.username.data)
            db.session.add(user)
            db.session.commit()
        print("Uathentication succss")
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


# e.g blueprint and routes
# auth_blueprint = Blueprint("auth", "auth", url_prefix="/auth")
# auth_blueprint.add_url_rule("register", "register", controllers.register)
