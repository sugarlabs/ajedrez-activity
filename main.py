#!/usr/bin/env python
#
#    Ceibal Chess - A chess activity for Sugar.
#    Copyright (C) 2008, 2009 Alejandro Segovia <asegovi@gmail.com>
#
#   This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#

import sys
import time
import traceback
import logging

logging.basicConfig(
	#level=logging.NOTSET,
	level=logging.DEBUG,
	format='%(asctime)s %(levelname)s %(message)s',
	)
log = logging.getLogger()

try:
	import pygame

except Exception, ex:
	print >>sys.stderr, \
	"""\n\n############################################################
	You don't have pygame installed or is not inside PYTHONPATH,
	read the trace for aditional information
	############################################################\n\n"""
	print >>sys.stderr, ex.message
	log.exception(ex)
	sys.exit(1)

try:
	from board import *
	from piece import *
	from boardcontroller import *
	#from messenger import *
	from menu import *
	from ui import StatePanel, BoardRenderer
	from resourcemanager import image_manager

except Exception, ex:
	print >>sys.stderr, \
	"""\n\n##########################################
	Something went wrong loading game modules,
	read the trace for additional information
	##########################################\n\n"""
	print >>sys.stderr, ex.message
	log.exception(ex)
	sys.exit(1)

class CeibalChess(object):
	def __init__(self, dump=False):
		self.controller = None
		self.screen = None
		self.game_code = None
		self.dump_path = None

	def start(self, scr_w, scr_h, dump=False):
		self.debug = dump
		try:
			if dump:
				self._init_dump()
			try:
				self._run(scr_w, scr_h)
				return 0
			except KeyboardInterrupt:
				return 0
			except:
				log.exception("Caught unhandled exception, dumping and cleaning up...")
				if dump:
					self._save_dump()
				print >>sys.stderr,\
					"Ceibal-Chess is done crashing... "\
					"Game code was: %s.\nHave a nice day :) " % self.game_code
				return -1
		finally:
			self._cleanup()

	def _init_dump(self):
		self.game_code = str(int(time.time()))
		home = os.environ.get("HOME")
		if home:
			self.dump_path = os.path.join(home, ".cchess")
		else:
			self.dump_path = ".cchess"
		if not os.path.isdir(self.dump_path):
			os.mkdir(self.dump_path)

	def _save_dump(self):
		try:
			trace_file = open(os.path.join(self.dump_path, self.game_code + ".trace"), "w")
			try:
				traceback.print_exc(file=trace_file)
			finally:
				trace_file.close()

			#Dump screen to image file
			if self.screen:
				pygame.image.save(self.screen, os.path.join(self.dump_path, self.game_code + ".png"))
		except:
			pass

	def _run(self, scr_w, scr_h):
		pygame.init()

		#Messages
		game_messages = {}
		game_messages["checkmate"] = Message("Checkmate!", 10, 40, (255, 0, 0))
		game_messages["check"] = Message("Check", 10, 40, (128, 0, 0))
		game_messages["none"] = Message("", 10, 40)

		#XO: 1200x900
		if len(sys.argv) == 3:
			scr_w = int(sys.argv[1])
			scr_h = int(sys.argv[2])

		size = width, height = scr_h - 70, scr_h - 70

		#Screen config
		self.screen = pygame.display.set_mode((scr_w, scr_h))
		pygame.display.set_caption("Ceibal-Chess")

		surface = pygame.Surface(size)
		bg_img = image_manager.get_image("bg.png")
		bg_img = pygame.transform.scale(bg_img, (scr_w, scr_h))
		log.info("Starting width=%s height=%s", scr_w, scr_h)

		#Center chessboard in screen
		screen_rect = self.screen.get_rect()
		sface_rect = surface.get_rect()
		delta_x = (screen_rect.w - sface_rect.w) / 2
		delta_y = (screen_rect.h - sface_rect.h) / 2

		clock = pygame.time.Clock()

		board = Board(width, height)

		menu_opts = ["New CPU Game", "Player vs. Player", \
				"Credits", "Quit Ceibal-Chess"]
		menu = Menu(scr_h, scr_h, menu_opts)
		menu.visible = True

		#LOG related:
		#Unique identifier for this game (used for logs)

		#Controller
		self.controller = BoardController(board, MODE_P_VS_P)
		self.controller.init_board()

		#FPS
		#messenger.messages["FPS"] = Message("FPS: (calculating)", 10, 10)
		fps = 0
		last_time = time.time()

		#Create UI Elements:
		turn_display = StatePanel(scr_w - scr_w/6, scr_h/40, 120, 120)
		board_renderer = BoardRenderer(width, height)

		#Post an ACTIVEEVENT to render the first time
		pygame.event.post(pygame.event.Event(pygame.ACTIVEEVENT))

		while 1:
			fps += 1
			new_time = time.time()
			if new_time - last_time > 1:
				#messenger.messages["FPS"] = Message("FPS: " + str(fps/5.0), 10, 10)
				last_time = new_time
				fps = 0

			#clock.tick(30)
			if not menu.visible:
				self.controller.update()

			#Event handling
			event = pygame.event.wait()
			#discard mousemotion event (too expensive)
			while event.type == pygame.MOUSEMOTION:
				event = pygame.event.wait()

			if event.type == pygame.QUIT:
				self.controller.close()
				break

			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					menu.toggle_visible()
				if event.key == pygame.K_u and not menu.visible:
					self.controller.undo_move()
				#else:
				#	controller.close()
				#	sys.exit(0)

			if event.type == pygame.MOUSEBUTTONDOWN:
				x, y = pygame.mouse.get_pos()

				if not menu.visible:
					clicked_cell = board.pick(x-delta_x, y-delta_y)
					if clicked_cell:
						self.controller.on_cell_clicked(clicked_cell)
				else:
					option = menu.on_click(x-delta_x, y-delta_y)
					if option:
						if option == menu_opts[3]:
							self.controller.close()
							break
						elif option in menu_opts[0:2]:
							game_mode = MODE_P_VS_CPU
							if option == menu_opts[1]:
								game_mode = MODE_P_VS_P
							board = Board(width, height)
							self.controller.close("Started new game")
							self.controller = BoardController(board, game_mode, self.debug)
							self.controller.init_board()
							menu.visible = False
							turn_display.set_state("move_white")
			if not menu.visible:
				print "Checking if king is checkmated:"
				t_ini = time.time()
				checkmated = board.king_is_checkmated(board.current_turn)
				print "Check if checkmate for %s took %.5f secs" % \
					(board.current_turn, time.time() - t_ini)

				if checkmated:
					#print "Checkmate for", board.current_turn
					#messenger.messages["check"] = game_messages["checkmate"]
					#self.controller.game_state = "checkmate"
					turn_display.set_state("checkmate_" + board.current_turn.name)
					self.controller.on_checkmate()

				elif board.king_is_checked(board.current_turn):
					#messenger.messages["check"] = game_messages["check"]
					turn_display.set_state("check_" + board.current_turn.name)
				else:
					#messenger.messages["check"] = game_messages["none"]
					turn_display.set_state("move_" + board.current_turn.name)

			#time visual update:
			t_ini = time.time()

			self._clear(self.screen)
			self._clear(surface)

			self.screen.blit(bg_img, bg_img.get_rect())

			board_renderer.render_background(board, surface)

			if self.controller.selected_cell is not None:
				board_renderer.render_moves_for_piece_in_cell(board, surface, self.controller.selected_cell)

			board_renderer.render_foreground(board, surface)

			menu.render(surface)

			self.screen.blit(surface, sface_rect.move(delta_x, delta_y))

			if not menu.visible:
				turn_display.render(self.screen)

			messenger.render_messages(self.screen)

			self._update()

			log.debug("Visual refresh took %.5f secs", (time.time() - t_ini))

	def _update(self, ):
		pygame.display.flip()

	def _clear(self, surface):
		surface.fill((0, 0, 0))

	def _cleanup(self):
		if self.controller:
			self.controller.close()

if __name__ == "__main__":
	rc = CeibalChess().start(933,  700, dump=True)
	sys.exit(rc)
