import sys
from sugar.activity import activity
from main import CeibalChess

class ChessActivity(activity.Activity):
	def __init__(self, handle):
		activity.Activity.__init__(self, handle)
		rc = CeibalChess().start(1200,  900)
		sys.exit(rc)
