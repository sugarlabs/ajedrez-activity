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
import pygame
import os
import gettext
from gettext import gettext as _
from resourcemanager import image_manager

class StatePanel:
	'''Shows the current game state in a panel. The displayed game state 
	usually implies displaying the current turn (white or black), and 
	indicating a Checkmate.'''
	
	def __init__(self, x, y, w, h):
		'''Create a new instance of State Panel.
		x,y are the position where the panel will be rendered.
		w,h are the panel's desired size.'''
		
		self.state = "move_white"
		self.x, self.y, self.w, self.h = x, y, w, h
		self.loaded = False
	
	def set_state(self, state):
		'''Set the state to the given parameter.
		Valid states are: move_white, move_black, check_white, check_black,
		checkmate_white and checkmate_black .'''
		if not state in ["move_white", "move_black", "check_white", \
				"check_black", "checkmate_white", "checkmate_black"]:
			raise Exception("Invalid State: " + state)
		self.state = state
	
	def initialize(self):
		'''Initialize Fonts, Images, etc.'''
		self.bg = pygame.transform.scale( \
			image_manager.get_image("menu_back.png"), (self.w, self.h))
		
		pawn_white = image_manager.get_image("pawnwhite.png")
		pawn_black = image_manager.get_image("pawnblack.png")
		king_white = image_manager.get_image("kingwhite.png")
		king_black = image_manager.get_image("kingblack.png")
		
		self.turn_imgs = { "move_white" : pawn_white, \
				"move_black" : pawn_black, \
				"check_white" : king_white, \
				"check_black" : king_black, \
				"checkmate_white" : king_white, \
				"checkmate_black" : king_black }
		
		font = pygame.font.Font(None, 25)
		self.turn_text = font.render(_("Current Turn:"), 1, (255, 255, 255))
		self.check_text = font.render(_("Check:"), 1, (255, 255, 0))
		self.mate_text = font.render(_("Checkmate:"), 1, (255, 20, 20))
		
		self.loaded = True
	
	def render(self, surface):
		'''Render this panel on the given surface.'''
		
		if not self.loaded:
			self.initialize()
		
		x,y,w,h = self.x, self.y, self.w, self.h
		
		surface.blit(self.bg, pygame.Rect(x,y,w,h))
		
		if self.state in ["move_white", "move_black"]:
			surface.blit(self.turn_text, (x+(w-self.turn_text.get_width())/2.0, w/5.5))
		elif self.state in ["check_white", "check_black"]:
			surface.blit(self.check_text, (x+(w-self.check_text.get_width())/2.0, w/5.5))
		else:
			surface.blit(self.mate_text, (x+(w-self.mate_text.get_width())/2.0, w/5.5))
		
		img = self.turn_imgs[self.state]
		iw, ih = img.get_width(), img.get_height()
		surface.blit(img, pygame.Rect(x + (w-iw)/2, y + (h-ih)/2, iw, ih))

class BoardRenderer(object):
	def __init__(self, w, h):
		self.background = None
		self.w = w
		self.h = h
		self.cell_renderer = CellRenderer(PieceRenderer())

	def render_moves_for_piece_in_cell(self, board, surface, cell):
		'''Highlight possible moves for the piece in the given cell'''
		if cell.piece is None:
			raise Exception("cell does not contain a piece!")

		#select hightlight colors:
		if cell.piece.owner == board.current_turn:
			color = (0, 255, 0)
			color2 = (0, 180, 0)
		else:
			color = (255, 0, 0)
			color2 = (180, 0, 0)

		dests = cell.piece.get_moves(cell.pos, board, filter_check=True)

		for dest in dests:
			self.cell_renderer.render_as_highlight(board[dest.to], surface, color)
		self.cell_renderer.render_as_highlight(cell, surface, color2)

	def render_background(self, board, surface):
		'''Render the checkboard background'''
		if self.background is None:
			#Create alternating background
			self.background = pygame.Surface((self.w, self.h))
			for i in range(0, 8):
				for j in range(0, 8):
					self.cell_renderer.render_background(board[i, j], self.background)

			#Load texture and blit it
			texture = image_manager.get_image("wood.png")
			texture = pygame.transform.scale(texture, (self.w, self.h))
			self.background.blit(texture, texture.get_rect())

		surface.blit(self.background, self.background.get_rect())

	def render_foreground(self, board, surface):
		'''Render cell contents. Call render_foreground on each cell.'''
		for i in range(0, 8):
			for j in range(0, 8):
				self.cell_renderer.render_foreground(board[i, j], surface)

class CellRenderer(object):
	def __init__(self, piece_renderer):
		self.piece_renderer = piece_renderer

	def render_background(self, cell, surface):
		'''Render the cell's background onto the given surface'''
		tx = cell[0] * cell.size
		ty = cell[1] * cell.size
		surface.fill(cell.color, pygame.Rect(tx, ty, cell.size, cell.size))

	def render_foreground(self, cell, surface):
		'''Render the cell's foreground. Currently, this just forwards the
		rendering call to the contained piece, if any. Rendering is performed
		on the given surface.'''
		if cell.piece:
			self.piece_renderer.render(cell.pos, cell.size, cell.piece, surface)

	def render_as_highlight(self, cell, surface, color = (0, 255, 0)):
		'''Render the cell highlighted with a given color onto the given
		surface. Used to highlight possible piece movements.'''
		tx = cell[0] * cell.size
		ty = cell[1] * cell.size
		surface.fill(color, pygame.Rect(tx+5, ty+5, cell.size-10, cell.size-10))

class PieceRenderer(object):
	def render(self, pos, size, piece, surface):
		'''
		Render the piece. x,y are the top left corner of the
		container cell; cell_size is its size
		'''
		img = image_manager.get_image('%s%s.png' % (piece.type, piece.owner.name))
		w,h = img.get_width(), img.get_height()
		tx = pos[0]*size + (size - w) / 2
		ty = pos[1]*size + (size - h) / 2

		surface.blit(img, pygame.Rect(tx, ty, w, h))
