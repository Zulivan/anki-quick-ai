import openai
from PyQt6.QtWidgets import QComboBox

from ..ankiaddonconfig import ConfigManager, ConfigWindow
from .prompt_window import PromptNameTableWidget
from ..edge_tts_data import language_list, get_voice_list
from ..ai import get_avail_chat_model_list



conf = ConfigManager()

def general_tab(conf_window: ConfigWindow) -> None:
    tab = conf_window.add_tab("General")

    tab.text("Running Settings", bold=True)

    tab.checkbox("general.automatic_display", "Automatically run add-on when changing to main window")

    tab.text_input(
        "general.shortcut",
        "Shortcut for add-on:"
    )

    tab.space(20)
    tab.text("Sound", bold=True)

    tab.checkbox("general.play_sound", "Generate and automatically play sound for response")

    name_combo = tab.dropdown(
        "general.default_sound_language",
        language_list,
        language_list,
        "Default edge-tts Language",
    )

    default_language = conf.get("general.default_sound_language")
    default_voice = conf.get("general.default_edge_tts_voice")
    default_voice_list = get_voice_list(conf["general"]["default_sound_language"])
    voice_combo = tab.dropdown(
        "general.default_edge_tts_voice",
        default_voice_list,
        default_voice_list,
        "Default edge-tts Voice",
        append_updates=False
    )
    voice_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)

    def update_voice_combo(language):
        if language in language_list:
            voice_combo.clear()
            voice_combo.insertItems(0, get_voice_list(language))
        if language == default_language:
            voice_combo.setCurrentText(default_voice)

    def widget_update_voice_combo():
        voice_combo.setCurrentText(conf_window.conf.get("general.default_edge_tts_voice"))

    conf_window.widget_updates.append(widget_update_voice_combo)
    name_combo.currentTextChanged.connect(update_voice_combo)

    # This adds a stretchable blank space.
    # If you are not sure what this does,
    # Try resizing the config window without this line

    tab.stretch()


def prompt_tab(conf_window: ConfigWindow) -> None:
    tab = conf_window.add_tab("Prompt")

    prompt_name_table_widget = PromptNameTableWidget(conf)
    tab.layout().addWidget(prompt_name_table_widget)
    conf_window.execute_on_save(lambda: conf.set("prompt", prompt_name_table_widget.prompt_data))
    conf_window.widget_updates.append(prompt_name_table_widget.load_data)

    # This adds a stretchable blank space.
    # If you are not sure what this does,
    # Try resizing the config window without this line
    tab.stretch()


def ai_tab(conf_window: ConfigWindow) -> None:
    tab = conf_window.add_tab("AI")

    tab.text("Required", bold=True)

    providers = conf.get("ai_config.providers")
    default_api_provider = conf.get("ai_config.provider")
    provider_combo = tab.dropdown(
        "ai_config.provider",
        providers,
        providers,
        "Provider:",
        tooltip="Choose the provider for the AI model",
        append_updates=False
    )

    default_api_key = conf.get("ai_config.api_key")
    api_key_text_input = tab.text_input(
        "ai_config.api_key",
        "API Key:",
        tooltip="The supported APIs are OpenAI and Groq.",
    )
    tab.text('You can get API key <a href="https://platform.openai.com/account/api-keys">here</a>', html=True, size=10)

    default_avail_chat_model_list = get_avail_chat_model_list(default_api_provider, default_api_key)
    if len(default_avail_chat_model_list) == 0:
        default_avail_chat_model_list = ["API Key is not valid"]
    model_combo = tab.dropdown(
        "ai_config.model",
        default_avail_chat_model_list,
        default_avail_chat_model_list,
        "Model:",
        tooltip="Default is gpt-3.5-turbo",
        append_updates=False
    )

    def update_model(api_provider, api_key):
        avail_chat_model_list = get_avail_chat_model_list(api_provider, api_key)
        if len(avail_chat_model_list) == 0:
            avail_chat_model_list = ["API Key is not valid"]

        model_combo.clear()
        model_combo.insertItems(0, avail_chat_model_list)
        if api_key == default_api_key:
            model_combo.setCurrentText(conf.get("ai_config.model"))

    tab.widget_updates.insert(0, lambda: update_model(conf_window.conf.get("ai_config.provider"), conf_window.conf.get("ai_config.api_key")))
    api_key_text_input.textChanged.connect(lambda: update_model(conf_window.conf.get("ai_config.provider"), conf_window.conf.get("ai_config.api_key")))
    provider_combo.currentTextChanged.connect(lambda: update_model(conf_window.conf.get("ai_config.provider"), conf_window.conf.get("ai_config.api_key")))

    tab.space(20)

    tab.text("Advanced", bold=True)
    tab.text('<a href="https://platform.openai.com/docs/api-reference/chat/create#chat/create-temperature">More Details</a>', html=True, size=10)

    tab.number_input(
        "ai_config.temperature",
        "Sampling temperature:",
        decimal=True,
        minimum=0,
        maximum=2,
        tooltip="Between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.",
    )

    tab.number_input(
        "ai_config.max_tokens",
        "Max Token:",
        minimum=0,
        maximum=2147483647,
        tooltip="The maximum number of tokens to generate in the chat completion. The total length of input tokens and generated tokens is limited by the model's context length.",
    )

    tab.number_input(
        "ai_config.presence_penalty",
        "Presence Penalty:",
        decimal=True,
        minimum=-2.0,
        maximum=2.0,
        tooltip="Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.",
    )

    tab.number_input(
        "ai_config.frequency_penalty",
        "Frequency Penalty:",
        decimal=True,
        minimum=-2.0,
        maximum=2.0,
        tooltip="Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.",
    )

    # This adds a stretchable blank space.
    # If you are not sure what this does,
    # Try resizing the config window without this line
    tab.stretch()



conf.use_custom_window()
conf.add_config_tab(general_tab)
conf.add_config_tab(prompt_tab)
conf.add_config_tab(ai_tab)
