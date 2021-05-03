pybabel extract . -F translations/babel.ini -k _l -o translations/messages.pot 
pybabel update -i translations/messages.pot -N -d translations
