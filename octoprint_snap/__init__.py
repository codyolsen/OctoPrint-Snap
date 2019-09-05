# coding=utf-8
from __future__ import absolute_import
import octoprint.events
from octoprint.util import RepeatedTimer

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin
import boto3
import requests

class SnapPlugin(octoprint.plugin.StartupPlugin,
								 octoprint.plugin.SettingsPlugin,
                 octoprint.plugin.AssetPlugin,
                 octoprint.plugin.TemplatePlugin):

	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict(
			interval=0,
			iam_access_key_id="",
			iam_secret_access_key="",
		)
 	
	def on_after_startup(self):
		self._logger.info("Oh Snap! (Current Interval: %s)" % self._settings.get(["interval"]))
		snapshotUrl = self._settings.global_get(["webcam","snapshot"])
		self._logger.info(snapshotUrl)
		

		# s3_object = boto3.resource('s3').Object(bucket_name, object_key)

		# with requests.get(url, stream=True) as r:
		# 		s3_object.put(Body=r.content)


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


# Events to handle:
# PrintStarted
# PrintFailed
# PrintDone
# PrintCancelling
# PrintCancelled
# PrintPaused
# PrintResumed

# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Snap"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = SnapPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}

