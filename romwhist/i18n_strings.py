from flask_babel import gettext as _

# Define all strings that need to be passed to the templates


def i18n():
    __i18n = dict()
    __i18n["join_game"] = _("join_game")
    __i18n["new_game"] = _("new_game")
    __i18n["alias"] = _("alias")
    
    __i18n["bet"] = _("bet")
    __i18n["bets"] = _("bets")
    __i18n["wins"] = _("wins")
    __i18n["points"] = _("points")
    __i18n["score"] = _("score")
    __i18n["scoresheet"] = _("scoresheet")
    
    __i18n["remove_player"] = _("remove_player")
    __i18n["add_ai"] = _("add_ai")
    __i18n["leave_game"] = _("leave_game")
    __i18n["stop_game"] = _("stop_game")
    __i18n["start_game"] = _("start_game")
    __i18n["restart_hand"] = _("restart_hand")
    
    __i18n["ohell"] = _("ohell")
    __i18n["belote"] = _("belote")
    __i18n["contree"] = _("contree")

    __i18n["game_over"] = _("game_over")
    __i18n["ok"] = _("ok")
    __i18n["cancel"] = _("cancel")
    __i18n["round_winner"] = _("round_winner")
    __i18n["with_the"] = _("with_the")
    __i18n["winner"] = _("winner")

    __i18n["trump"] = _("trump")
    __i18n["user"] = _("user")
    __i18n["left_game"] = _("left_game")


    # This block may not be required
    __i18n["select"] = _("select")
    __i18n["spade"] = _("spade")
    __i18n["heart"] = _("heart")
    __i18n["diamond"] = _("diamond")
    __i18n["club"] = _("club")
    __i18n["pass"] = _("pass")
    __i18n["contre"] = _("contre")
    __i18n["surcontre"] = _("surcontre")
    __i18n["contré"] = _("contré")
    __i18n["surcontré"] = _("surcontré")

    # This block may not be required
    __i18n["two"] = _("two")
    __i18n["three"] = _("three")
    __i18n["four"] = _("four")
    __i18n["five"] = _("five")
    __i18n["six"] = _("six")
    __i18n["seven"] = _("seven")
    __i18n["eight"] = _("eight")
    __i18n["nine"] = _("nine")
    __i18n["ten"] = _("ten")
    __i18n["jack"] = _("jack")
    __i18n["queen"] = _("queen")
    __i18n["king"] = _("king")
    __i18n["ace"] = _("ace")
    
    __i18n["copyright"] = _("copyright")
    __i18n["game_id"] = _("game_id")
    __i18n["chat"] = _("chat")
    __i18n["send"] = _("send")

    __i18n["confirm_leave_game"] = _("confirm_leave_game")
    __i18n["confirm_remove_player"] = _("confirm_remove_player")
    __i18n["confirm_stop_game"] = _("confirm_stop_game")
    __i18n["confirm_add_ai"] = _("confirm_add_ai")
    __i18n["confirm_restart_hand"] = _("confirm_restart_hand")
    __i18n["bet_not_allowed"] = _("bet_not_allowed")

    return __i18n

def i18n_val(key):
    return i18n.get[key]