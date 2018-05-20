import sys
import os
import sugargame
import sugargame.canvas
import gi
from gi.repository import GObject
import pygame
import gettext
from gettext import gettext as _

from sugar3.activity import activity
from main import CeibalChess, log

class ChessActivity(activity.Activity):
	'''
	ChessActivity provides the basic configuration for
	setting up and running Ceibal-Chess as an Activity and
	for embedding pygame in a gtk window.

	For all the methods of activity.Activity please visit:
	http://api.sugarlabs.org/epydocs/sugar.activity.activity-pysrc.html

	For the logic behind the GTK-pygame wrapping, visit:
	http://wiki.sugarlabs.org/go/Development_Team/Sugargame
	'''
	def __init__(self, handle):
		# i18n:
		bundle_path = os.environ["SUGAR_BUNDLE_PATH"]
		i18n_path = os.path.join(bundle_path, "po")
		gettext.bindtextdomain("messages", i18n_path)
		gettext.textdomain("messages")

		activity.Activity.__init__(self, handle)
		self.game= CeibalChess(self)
		self.game.canvas = sugargame.canvas.PygameCanvas(
			self,
			main=self.game.start,
			modules=[pygame.display, pygame.font])
		log.info("Starting pygame widget...")
		self.set_canvas(self.game.canvas)

	def read_file(self, filepath):
		pass
	
	def write_file(self, filepath):
		pass

	def can_close(self):
		log.info("Activity requested to stop...")
		self.game.stop()
		return True

