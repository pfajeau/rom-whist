import romwhist
from romwhist import app, socketio
from flask_babel import Babel
import test

# Use the browser's language preferences to select an available translation
# add to you main app code
# @babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

# def get_locale():
#    return 'en'

babel = Babel(app, locale_selector=get_locale)


if __name__ == '__main__':
    app = romwhist.create_app()

    # socketio.run(app, debug=True)
