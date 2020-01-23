# coding=utf-8

# pylint: disable=E1101
# //https://github.com/PyCQA/pylint/issues/3134

from __future__ import absolute_import
import octoprint.events
import octoprint.plugin
from octoprint.util import RepeatedTimer
from datetime import datetime
from boto3 import resource
from requests import get, post, head
from mimetypes import guess_extension

class SnapPlugin(octoprint.plugin.EventHandlerPlugin,
								 octoprint.plugin.StartupPlugin,
								 octoprint.plugin.SettingsPlugin,
                 octoprint.plugin.AssetPlugin,
                 octoprint.plugin.TemplatePlugin):

	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict(
			interval=0,
			iam_access_key_id="",
			iam_secret_access_key="",
			s3_bucket_name="",
			webhook_url="",
		)

	def on_after_startup(self):
		self._logger.info("Oh Snap! (Current Interval: %s)", self._settings.get(["interval"]))

	# TODO Refactor if possible these event calls into meta invocations similar to `.send` or `.call` in node.
	# https://stackoverflow.com/questions/3951840/how-to-invoke-a-function-on-an-object-dynamically-by-name

	# Octopi events to handle
	TIMER_START_EVENTS = [
		"PrintStarted",
		"PrintResumed",
	]	

	# Update the interval loop
	TIMER_UPDATE_EVENTS = [
		"SettingsUpdated"
	]

	# End the loop events
	TIMER_STOP_EVENTS = [
		"PrintFailed",
		"PrintDone",
		"PrintCancelling",
		"PrintCancelled",
		"PrintPaused",
	]

	def execute_timer_event(self, event):
		if event in self.TIMER_START_EVENTS:
			self.start_printing_timer()
		elif event in self.TIMER_STOP_EVENTS:
			self.stop_printing_timer()
		elif event in self.TIMER_UPDATE_EVENTS:
			self.restart_printing_timer()
		else:
			return

	def on_event(self, event, payload):
		self.execute_timer_event(event)

	# Timer for interval
	printing_timer = None

	# Event for timer
	def printing_timer_tick(self):
		self._logger.debug("timer tick at interval %s", self._settings.get(["interval"]))
		snapshot_url = self.snapshot_to_s3()
		self.send_ifttt(snapshot_url)

	# Passed to timer as interval function to dynamically change interval.
	def printing_timer_interval(self):
		return int(self._settings.get(["interval"]))

	# Start
	def start_printing_timer(self, run_first = False):
		self._logger.debug("start timer")

		# Create and start the timer.
		self.printing_timer = RepeatedTimer(
			self.printing_timer_interval, self.printing_timer_tick, run_first = run_first
		)
		self.printing_timer.start()

	# Stop
	def stop_printing_timer(self):
		self._logger.debug("stop timer")
		if self.printing_timer != None:
			self.printing_timer.cancel()
			self.printing_timer = None
		return

	# Restart
	def restart_printing_timer(self):
		self._logger.debug("restart timer")

		if self.printing_timer == None:
			return

		self.stop_printing_timer()
		self.start_printing_timer(True)

	def snapshot_to_s3(self):
		s3_bucket = self._settings.get(["s3_bucket_name"])

		# Get the content-type for extension and a timestamp for key 
		snapshot_url = self._settings.global_get(["webcam","snapshot"])
		extension = guess_extension(head(snapshot_url).headers['content-type'])
		object_key = datetime.utcnow().strftime("%m-%d-%Y_%H:%M:%S") + extension

		# Create object
		s3_object = resource(
			's3',
			aws_access_key_id=self._settings.get(["iam_access_key_id"]),
			aws_secret_access_key=self._settings.get(["iam_secret_access_key"])
		).Object(s3_bucket, object_key)
		
		# Stream to s3
		with get(snapshot_url, stream=True) as r:
			s3_object.put(
				Body=r.content,
				ACL='public-read'
			)

		return "https://%s.s3.amazonaws.com/%s" % (s3_bucket, object_key)

	def send_ifttt(self, snapshot_url):
		json = {'value1':'this is value_1','value2':'this is value_2','value3':snapshot_url}
		post(self._settings.get(["webhook_url"]), data=json)

	def get_template_configs(self):
		return [
			dict(type="settings", custom_bindings=False)
    ]

	##~~ AssetPlugin mixin

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/snap.js"],
			css=["css/snap.css"],
			less=["less/snap.less"]
		)

	##~~ Softwareupdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		return dict(
			snap=dict(
				displayName="Snap Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="codyolsen",
				repo="OctoPrint-Snap",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/codyolsen/OctoPrint-Snap/archive/{target_version}.zip"
			)
		)

# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Snap"
__plugin_pythoncompat__ = ">=2.7,<4"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = SnapPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}

