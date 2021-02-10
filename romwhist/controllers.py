"""
This module implements webapp controllers.

@author: Philippe Fajeau
"""

from flask import flash


def flash_errors(form):
    """Generate flashes for errors"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'error')


# e.g. controllers
# def register():
#     context = {"title": "home"}
#     return render_template("foo.html", **context)
#
# def register_api():
#     return jsonify({"first_name": "foo"}), 200
