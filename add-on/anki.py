from aqt import mw



def get_words(browse_cmd):
    card_id_list = mw.col.find_cards(browse_cmd)
    words = [mw.col.get_card(card_id).note()[mw.addonManager.getConfig(__name__)["note_field"]] for card_id in card_id_list]
    return words