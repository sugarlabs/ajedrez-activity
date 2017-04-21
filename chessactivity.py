import sys
import os
from sugargame.canvas import PygameCanvas
import gobject

import gettext
from gettext import gettext as _

from sugar.activity import activity
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
		self.canvas = PygameCanvas(self)
		self.set_canvas(self.canvas)
		self.chess = CeibalChess()
		self.chess.set_close_callback(self.close)
		self.show()
		gobject.idle_add(self.start_cb, None)
		#rc = CeibalChess().start(1200,  900)
		#sys.exit(rc)
	
	def start_cb(self, param):
		log.info("Starting pygame widget...")
		self.canvas.run_pygame(self.chess.start)

	def read_file(self, filepath):
		pass
	
	def write_file(self, filepath):
		pass

	def can_close(self):
		log.info("Activity requested to stop...")
		self.chess.stop()
		return True

