import zulip
import json, requests, os, sys
# blame Python 2 not me
try:
    import ConfigParser as configparser
except:
    import configparser

class ScrambleBot():

    def __init__(self, zulip_username, zulip_api_key, key_word, subscribed_streams=[], debug=False):
        """
        ScrambleBot takes a zulip username and api key, a word or phrase to respond to,
        and a list of the zulip streams it should be active in.
        """
        self.debug = debug

        self.username = zulip_username
        self.api_key = zulip_api_key
        self.key_word = key_word.lower()

        self.subscribed_streams = subscribed_streams
        self.client = zulip.Client(zulip_username, zulip_api_key)
        self.subscriptions = self.subscribe_to_streams()

    @property
    def streams(self):
        """Standardizes a list of streams in the form [{'name': stream}]"""
        if not self.subscribed_streams:
            streams = [{"name": stream["name"]} for stream in self.get_all_zulip_streams()]
            return streams
        else: 
            streams = [{"name": stream} for stream in self.subscribed_streams]
            return streams


    def get_all_zulip_streams(self):
        """Call Zulip API to get a list of all streams"""

        response = requests.get("https://api.zulip.com/v1/streams", auth=(self.username, self.api_key))
        if response.status_code == 200:
            return response.json()["streams"]
        elif response.status_code == 401:
            raise RuntimeError("check your auth")
        else:
            raise RuntimeError(":( we failed to GET streams.\n(%s)" % response)


    def subscribe_to_streams(self):
        """Subscribes to zulip streams"""
        self.client.add_subscriptions(self.streams)


    def respond(self, msg):
        """Checks msg against key_word. If key_word is in msg, calls send_message()"""

        content = msg["content"].lower()

        if self.key_word in content:

            # speeds up escaping from zulip
            if self.debug and "crash" in content:
                sys.exit()

            self.send_message(msg) 
               

    def send_message(self, msg):
        """Sends a message to zulip stream"""

        self.client.send_message({
            "type": "stream",
            "subject": msg["subject"],
            "to": msg["display_recipient"],
            "content": "testing"
            })


    def main(self):
        """Blocking call that runs forever. Calls self.respond() on every message received."""
        self.client.call_on_each_message(lambda msg: self.respond(msg))

try:
    config = configparser.ConfigParser()
    config.read("config.ini")
    zulip_username = config.get("api", "key")
    zulip_api_key = config.get("api", "email")
except:
    zulip_username = os.environ["SCRAMBLEBOT_USR"]
    zulip_api_key = os.environ["SCRAMBLEBOT_API"]

key_word = "@**ScrambleBot**"
# if it is blank, bot will subscribe to all streams
subscribed_streams = ["test-bot"]
debug = (len(sys.argv) == 2 and sys.argv[1] == "--DEBUG")

new_bot = ScrambleBot(zulip_username, zulip_api_key, key_word, subscribed_streams, debug)
new_bot.main()