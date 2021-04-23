from flask_babel import gettext as _

i18n = dict()


def init_strings():
    print (_("remove_player"))
    i18n["remove_player"] = _("remove_player")
