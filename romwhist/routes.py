"""
This module implements routes.

author: Philippe Fajeau

"""
from flask import Blueprint
from . import controllers
from romwhist import app
from flask import render_template, request, flash, session, url_for, redirect
# from .forms import ContactForm, SignupForm, SigninForm


@app.route("/")
def index():
    # TODO - add here endpoint of resource where you want to land on page load. e.g.
    # return redirect(url_for("auth_blueprint.home"))
    return render_template("index.html")

@app.route("/phil")
def test():
    return render_template("index.html", username="Phil")

@app.route("/boot")
def bootex():
    return render_template("bootex.html")

# e.g blueprint and routes
# auth_blueprint = Blueprint("auth", "auth", url_prefix="/auth")
# auth_blueprint.add_url_rule("register", "register", controllers.register)
