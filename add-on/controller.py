from aqt import mw, gui_hooks
from aqt.operations import QueryOp
from aqt.qt import QAction, qconnect

import openai
import playsound
import os
import threading

from .anki import get_note_field_value_list
from .gpt import call_openai, make_edge_tts_mp3
from .gui import RunDialog, ResponseDialog
from .utils import format_prompt_list



class AIThread(threading.Thread):
    def __init__(self, api_key, model, browse_cmd, note_field, prompt_list):
        super().__init__()
        openai.api_key = api_key
        self.model = model
        self.browse_cmd = browse_cmd
        self.note_field = note_field
        self.prompt_list = prompt_list
        self.field_value_list = None
        self.response_list = []
        self.daemon = True  # Set the thread as daemon
        self.success = False

    def run(self):
        self.success = False
        
        self.field_value_list = get_note_field_value_list(mw.col, self.browse_cmd, self.note_field)

        prompt = self.prompt_list[0].replace(f"#response#", str(self.field_value_list))
        response = call_openai(prompt, self.model)
        self.response_list.append(response)

        for i in range(1, len(self.prompt_list)):
            prompt = self.prompt_list[i].replace(f"#response#", response)
            response = call_openai(prompt, self.model)
            self.response_list.append(response)
        
        self.success = True


class SoundThread(threading.Thread):
    def __init__(self, response_list, sound_language_list):
        super().__init__()
        self.response_list = response_list
        self.sound_language_list = sound_language_list
        self.daemon = True  # Set the thread as daemon

    def run(self):
        if not os.path.exists(os.path.join(os.path.dirname(__file__), "output")):
            os.makedirs(os.path.join(os.path.dirname(__file__), "output"))
        for i in range(len(self.response_list)):
            make_edge_tts_mp3(self.response_list[i], self.sound_language_list[i], os.path.join(os.path.dirname(__file__), "output", f"response_{i}.mp3"))
            playsound.playsound(os.path.join(os.path.dirname(__file__), "output", f"response_{i}.mp3"))


def show_response(field_value_list, prompt_list, response_list, parent):
    if len(prompt_list) != len(response_list):
        raise ValueError(f"Prompt length {len(prompt_list)} is not equal to response length {len(response_list)}")
    
    color = 'green'
    field_value_str = '<br>'.join(field_value_list)

    text = f"<font color='{color}'>Choosen values:</font><br>{field_value_str}<br><br>"
    for i in range(len(response_list)):
        text += f"<font color='{color}'>Prompt: {prompt_list[i]}:</font><br>Response: {response_list[i]}<br><br>"
    
    dialog = ResponseDialog(text, parent)
    dialog.exec_()


def show_response_and_play_sound(ai_success, field_value_list, prompt_list, response_list, sound_language_list, parent=mw):
    if not ai_success:
        return
    # play sound
    if mw.addonManager.getConfig(__name__)["play_sound"]:
        music_thread = SoundThread(response_list, sound_language_list)
        music_thread.start()

    # show story
    show_response(field_value_list, prompt_list, response_list, parent)


def run_add_on(query=None, parent=mw):
    def click_run_add_on(run_widget):
        run_widget.close()
        gen_response(run_widget.input_field_browse_query.text(), run_widget.input_field_note_field.text(), parent=parent)
    
    if not query:
        query = mw.addonManager.getConfig(__name__)["query"]
    run_widget = RunDialog(query, parent)
    run_widget.run_button.clicked.connect(lambda: click_run_add_on(run_widget))
    run_widget.show()


def run_add_on_browse(browser):
    action_browse = QAction("Anki Quick AI", browser)
    browser.form.menubar.addAction(action_browse)
    qconnect(action_browse.triggered, lambda: run_add_on(browser.form.searchEdit.lineEdit().text(), browser))


def gen_response(query, note_field, parent=mw) -> None:
    config = mw.addonManager.getConfig(__name__)
    prompt_list = format_prompt_list(config["prompt_list"], config["placeholder"])
    ai_thread = AIThread(config["api_key"], config["model"], query, note_field, prompt_list)

    def run_ai_thread(ai_thread):
        ai_thread.start()
        ai_thread.join()

    op_story = QueryOp(
        # the active window (main window in this case)
        parent=parent,
        # the operation is passed the collection for convenience; you can
        # ignore it if you wish
        op=lambda col: run_ai_thread(ai_thread),
        # this function will be called if op completes successfully,
        # and it is given the return value of the op
        success=lambda x: show_response_and_play_sound(ai_thread.success, ai_thread.field_value_list, config["prompt_list"], ai_thread.response_list, config["sound_language_list"], parent=parent)
    )

    op_story.with_progress(label="It may take seconds for AI to generate contents").run_in_background()





#  hooks

# Add it to the tools menu
action_mw = QAction("Anki Quick AI", mw)
qconnect(action_mw.triggered, run_add_on)
mw.form.menuTools.addAction(action_mw)

# Add it to the browse window
gui_hooks.browser_will_show.append(run_add_on_browse)

# hook for end of the deck
if mw.addonManager.getConfig(__name__)["automatic_display"]:
    gui_hooks.reviewer_will_end.append(run_add_on)
