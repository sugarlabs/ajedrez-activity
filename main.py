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

import os
import sys
import time
import traceback
import logging
import gtk
import gettext
from gettext import gettext as _

logging.basicConfig(
	#level=logging.NOTSET,
	level=logging.DEBUG,
	format='%(asctime)s %(levelname)s %(message)s',
	)
log = logging.getLogger()

try:
	import pygame
	vers = pygame.vernum
	# Force to False for rendering like on the XO
	alpha_blending = vers[0] >= 1 and vers[1] >= 8
	if not alpha_blending:
		log.warn("Pygame version does not support alpha blending. Disabling...")

except Exception, ex:
	print >>sys.stderr, \
	"""\n\n############################################################
	You either do not have pygame installed or it's not within PYTHONPATH,
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
		self.close_callback = None

	def start(self, scr_w=1200, scr_h=900, dump=False, gtk_embedded=True):
		log.warn("LANG is %s" % os.environ["LANG"])
		self.debug = dump
		self.gtk_embedded = gtk_embedded
		try:
			if dump:
				self._init_dump()
			try:
				self.done = False
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
	
	def set_close_callback(self, close_callback):
		self.close_callback = close_callback

	def stop(self):
		self.controller.close()
		self.done = True

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
		game_messages["checkmate"] = Message(_("Checkmate!"), 10, 40, (255, 0, 0))
		game_messages["check"] = Message(_("Check"), 10, 40, (128, 0, 0))
		game_messages["none"] = Message("", 10, 40)

		#XO: 1200x900
		if len(sys.argv) == 3:
			scr_w = int(sys.argv[1])
			scr_h = int(sys.argv[2])

		size = width, height = scr_h - 70, scr_h - 70

		#Screen config
		if not self.gtk_embedded:
			self.screen = pygame.display.set_mode((scr_w, scr_h))
		else:
			self.screen = pygame.display.get_surface()
		pygame.display.set_caption("Ceibal-Chess")

		surface = pygame.Surface(size)
		bg_img = image_manager.get_image("bg.png")
		bg_img = pygame.transform.scale(bg_img, (scr_w, scr_h))
		log.info("Starting width=%s height=%s", scr_w, scr_h)

		accum_surface = pygame.Surface((scr_w, scr_h), pygame.SRCALPHA)

		#Center chessboard in screen
		screen_rect = self.screen.get_rect()
		sface_rect = surface.get_rect()
		delta_x = (screen_rect.w - sface_rect.w) / 2
		delta_y = (screen_rect.h - sface_rect.h) / 2

		clock = pygame.time.Clock()

		board = Board(width, height)

		menu_opts = [_("New CPU Game"), _("Player vs. Player"), \
				_("Credits"), _("Quit Ceibal-Chess")]
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
		turn_display = StatePanel(scr_w - scr_w/6.5, scr_h/40, 120, 120)
		board_renderer = BoardRenderer(width, height)

		clock = pygame.time.Clock()
		#Post an ACTIVEEVENT to render the first time
		pygame.event.set_blocked(pygame.MOUSEMOTION)
		pygame.event.post(pygame.event.Event(pygame.ACTIVEEVENT))

		while not self.done:
			fps += 1
			new_time = time.time()
			if new_time - last_time > 1:
				#messenger.messages["FPS"] = Message("FPS: " + str(fps/5.0), 10, 10)
				last_time = new_time
				fps = 0

			# no more than 30 FPS
			clock.tick(20)


			#Event handling
			if self.gtk_embedded:
				while gtk.events_pending():
					gtk.main_iteration()

			#event = pygame.event.wait()
			for event in pygame.event.get():
				#discard mousemotion event (too expensive)
				#while event.type == pygame.MOUSEMOTION:
				#	event = pygame.event.wait()

				if event.type == pygame.QUIT:
					self.controller.close()
					self.done = True
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
								self.done = True
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
				
				# This dirty piece of code makes the refresh and checkmate check only happen when needed
				# Need to fix this and how the _update function works.
				#if (board.current_turn.name == "black") or \
				#  ((board.current_turn.name == "white") and \
				#   (event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEBUTTONUP)) or \
				#   (turn_display.loaded == False):


				self._update(board_renderer, board, surface, accum_surface, menu, sface_rect, delta_x, delta_y, bg_img, turn_display)

				# Update IA if on "player vs cpu" mode and menu is not visible:
				if not menu.visible:
					self.controller.update()

		log.debug("Exiting...")
		if not self.gtk_embedded:
			pygame.quit()

		if self.close_callback:
			self.close_callback()
		

	def _update(self, board_renderer, board, surface, accum_surface, menu, sface_rect, delta_x, delta_y, bg_img, turn_display):
		if not menu.visible:
			#print "Checking if king is checkmated:"
			t_ini = time.time()
			checkmated = board.king_is_checkmated(board.current_turn)
			#print "Check if checkmate for %s took %.5f secs" % \
			#(board.current_turn, time.time() - t_ini)

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

		#No need to clear the buffers if we are redrawing them from scratch
		#self._clear(self.screen)
		#self._clear(surface)

		self.screen.blit(bg_img, bg_img.get_rect())
		#accum_surface.blit(bg_img, bg_img.get_rect())
		#surface.blit(bg_img, bg_img.get_rect())

		board_renderer.render_background(board, surface)

		if self.controller.selected_cell is not None:
			board_renderer.render_moves_for_piece_in_cell(board, surface, self.controller.selected_cell)

		board_renderer.render_foreground(board, surface)
		
		menu.render(surface)

		global alpha_blending

		if not menu.visible:
			if alpha_blending:
				turn_display.render(accum_surface)

		# Frame alpha blending
		if alpha_blending:
			debug_t = pygame.time.get_ticks()
			fade_time = 350.0 #Time in ms the animation lasts
			blit_accum_t = 0

			last_blit = pygame.time.get_ticks()

			while blit_accum_t < fade_time:
				curr_t = pygame.time.get_ticks()
				delta_t = curr_t - last_blit
				blit_accum_t += delta_t

				surface.set_alpha(int(blit_accum_t / float(fade_time) * 255))
				#self.screen.blit(surface, sface_rect.move(delta_x, delta_y))
				accum_surface.blit(surface, sface_rect.move(delta_x, delta_y))

				#self.screen.blit(accum_surface, accum_surface.get_rect())
				self.screen.blit(accum_surface, sface_rect)
				pygame.display.flip()
				last_blit = curr_t


			#print "fade in lasted", pygame.time.get_ticks() - debug_t, "ms"
		else:
			self.screen.blit(surface, sface_rect.move(delta_x, delta_y))

		if not menu.visible and not alpha_blending:
			turn_display.render(self.screen)
		
		pygame.display.flip()

		messenger.render_messages(self.screen)
                #log.debug("Visual WHITE refresh took %.5f secs", (time.time() - t_ini))
		pygame.display.flip()

	def _clear(self, surface):
		surface.fill((0, 0, 0))

	def _cleanup(self):
		if self.controller:
			self.controller.close()

if __name__ == "__main__":
	# i18n
	gettext.bindtextdomain("messages", "./po/")
	gettext.textdomain("messages")

	# Check if we are running on a XO or not.
	if os.access("/sys/power/olpc-pm", os.F_OK):
		resolution = (1200, 900)
	else:
		resolution = (933, 700)
	rc = CeibalChess().start(dump=True, gtk_embedded=False, *resolution)
	sys.exit(rc)
