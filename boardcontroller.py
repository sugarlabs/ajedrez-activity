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

from piece import *
from messenger import *
from chessengine import *

MODE_P_VS_CPU = 0
MODE_P_VS_P = 1

import logging
log = logging.getLogger()

class BoardController:
	PLAYING = 'playing'
	CHECKMATE = 'checkmate'
	def __init__(self, board, mode = MODE_P_VS_P, debug=False):
		'''Create a new board controller.'''
		self.board = board
		self.selected_cell = None
		self.board.current_turn = self.board.black #will be flipped
		self.board.next_turn() #set turn to white and show a message
		self.game_state = BoardController.PLAYING

		self.mode = mode
		self.debug = debug
		self.checkmate = False

		self.ai = None
		if mode == MODE_P_VS_CPU:
			try:
				self.ai = GnuChessEngine()
			except Exception,ex:
				log.error("Cannot start gnuchess. Defaulting to PvP.")
				log.exception(ex)
				self.mode = MODE_P_VS_P
		#no last known player move
		self.last_p_move = None

	def close(self, message = None):
		if self.ai:
			self.ai.close()
			self.ai = None
		if message:
			log.info(message + "\n")

	def undo_move(self):
		#FIXME: check if its possible to remove game_state variable.
		#self.game_state = BoardController.PLAYING
		if self.checkmate:
			return
		
		self.selected_cell = None #unselect piece (if any)

		self.board.undo_move()
		if self.ai:
			self.ai.undo()
			# first undo was ai move, now undo players
			self.board.undo_move()

	#TODO: Add castling and en-passant pawns indications.
	def init_board_text(self, text):
		'''Initialize board to a serialized position'''
		column, row = 0, 0
		kind_by_char = {'P': Pawn, 'N': Knight, 'B': Bishop,
						  'R': Rook, 'Q': Queen, 'K': King}
		for char in text:
			player = char.isupper() and self.board.white or self.board.black
			kind = kind_by_char.get(char.upper())
			
			if kind:
				self.board.put_piece_at(kind(player), (column, row))
			if column == 7:
				column, row = -1, row + 1
			column = column + 1
		
		self.board.current_turn = self.board.white
		self.checkmate = self.board.king_is_checkmated(self.board.current_turn)

	def init_board(self):
		'''Initialize board to starting chess configuration'''
		self.init_board_text("rnbqkbnr" + "p" * 8 + "." * 32 + "P" * 8 + "RNBQKBNR")

	def update(self):
		'''
		Perform updates on the board such as animations (not implemented yet) 
		and calling the IA.
		'''
		#TODO: Animate piece movements
		
		#Call IA:
		if self.ai and self.board.current_turn == self.board.black and \
			self.game_state != BoardController.CHECKMATE:
			if self.last_p_move:
				self.ai.move(self.last_p_move, self)
				if self.debug:
					self.ai.assert_sync(self.board)

	def on_checkmate(self):
		'''Handle checkmate events.'''
		self.close("Checkmated")
		self.checkmate = True

	def on_cell_clicked(self, clicked_cell):
		'''Handle mouse events from the user. This method gets called
		by the event control code when the user clicks on a cell.'''
		
		# Select a piece?
		if clicked_cell.piece and not self.selected_cell:
			self.selected_cell = clicked_cell
		else:
			# Move piece or deselect
			if self.selected_cell:
				if self.selected_cell.piece.is_turn(self.board.current_turn) and \
					(self.selected_cell != clicked_cell):
					self.move_piece(clicked_cell)
				else:
					self.selected_cell = None
			else:
				pass

	def move_piece(self, cell):
		'''Move the currently selected piece to a new cell.
		The currently selected piece is at self.selected_cell.'''
		
		if self.checkmate:
			return
		
		# Try to move the piece on the board:
		if self.board.can_move_piece_in_cell_to(self.selected_cell, cell.pos):
			move = self.board.move_piece_in_cell_to(
				self.board.current_turn,
				self.selected_cell.pos,
				cell.pos)
			if self.ai:
				self.last_p_move = move
			self.selected_cell = None
		else:
			if cell.piece:
				self.selected_cell = cell

	def move(self, player, fro, to, **options):
		'''
		Move a piece from position "fro" to position "to".

		This method checks whether a piece is actually at "fro" and that its
		owner is the given "player" parameter.

		"options" is an optional parameter used to provide move metadata, such
		as the piece a pawn is crowned to.
		'''
		
		if self.checkmate:
			return
		
		log.debug("%s: %d, %d to %d, %d", player, fro[0], fro[1], to[0], to[1])
		
		self.board.move_piece_in_cell_to(player, fro, to, **options)
