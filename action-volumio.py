#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# See https://volumio.github.io/docs/API/Command_Line_Client.html for commands

from hermes_python.hermes import Hermes
from snipshelpers.thread_handler import ThreadHandler
from snipshelpers.config_parser import SnipsConfigParser
import Queue
from subprocess import call

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

_id = "snips-skill-volumio"


class SkillVolumio:
    def __init__(self):
        try:
            config = SnipsConfigParser.read_configuration_file(CONFIG_INI)
        except:
            config = None

        self.queue = Queue.Queue()
        self.thread_handler = ThreadHandler()
        self.thread_handler.run(target=self.start_blocking)
        self.thread_handler.start_run_loop()
        print("[VOLUMIO] Started")

    def callback(self, hermes, intent_message):
        print("[VOLUMIO] Received intent {}".format(intent_message.intent.intent_name))

        actions = {
            "volumeUp": self.volume_up,
            "volumeDown": self.volume_down,
            "resumeMusic": self.resume_music,
            "speakerInterrupt": self.speaker_interrupt,
            "previousSong": self.previous_song,
            "nextSong": self.next_song,

            "playArtist": self.not_implemented,
            "getInfos": self.not_implemented,
            "addSong": self.not_implemented,
            "radioOn": self.not_implemented,
            "playAlbum": self.not_implemented,
            "playPlaylist": self.not_implemented,
        }

        result = actions[intent_message.intent.intent_name](hermes, intent_message)
        self.terminate_feedback(hermes, intent_message, result or "")

    def start_blocking(self, run_event):
        while run_event.is_set():
            try:
                self.queue.get(False)
            except Queue.Empty:
                with Hermes(MQTT_ADDR) as h:
                    h.subscribe_intents(self.callback).start()

    def volume_up(self, hermes, intent_message):
        # percent = self.extract_volume_higher(intent_message, None)
        self.execute_volumio_command("volume", "plus")

    def volume_down(self, hermes, intent_message):
        self.execute_volumio_command("volume", "minus")

    def resume_music(self, hermes, intent_message):
        self.execute_volumio_command("play")

    def speaker_interrupt(self, hermes, intent_message):
        self.execute_volumio_command("pause")

    def previous_song(self, hermes, intent_message):
        self.execute_volumio_command("previous")

    def next_song(self, hermes, intent_message):
        self.execute_volumio_command("next")

    def not_implemented(self, hermes, intent_message):
        return "Not implemented"

    @staticmethod
    def execute_volumio_command(command, *args):
        parameters = ["volumio", "command"]
        for arg in args:
            [].append(arg)
        call(parameters)

    def extract_volume_higher(self, intent_message, default_volume):
        volume = default_volume
        if intent_message.slots.volume_higher:
            volume = intent_message.slots.volume_higher.first().value
        if volume < 0:
            volume = 0
        if volume > 100:
            volume = 100
        return volume

    def terminate_feedback(self, hermes, intent_message, feedback=""):
        hermes.publish_end_session(intent_message.session_id, feedback)


if __name__ == "__main__":
    SkillVolumio()
