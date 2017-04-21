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
import time
from cell import Cell
from errors import MoveError
import logging
log = logging.getLogger()

WHITE = 'white'
BLACK = 'black'

LEFT = -1
RIGHT = 1
UP = -1
DOWN = 1

WHITE_RANK = 7
WHITE_PAWN_DIR = UP
BLACK_RANK = 0
BLACK_PAWN_DIR = DOWN

class Player(object):
	def __init__(self, name, rank, pawn_dir):
		self.name = name
		self.en_passant = None
		self.enemy = None
		self.rank = rank
		self.castling_performed = False
		self.pawn_dir = pawn_dir

	def __str__(self):
		return self.name

class Board(object):
	'''Representation of the board. A board holds the piece instances that
	live in it. It is also responsible for asking moves to perform themselves,
	storing them in the move stack (for undo) and for asking pieces to render
	themselves.

	A board's individual cells can be accessed using the array subscript
	operator twice. Eg. board[0][0] contains the cell (instance of class
	Cell) at the row 0, column 0. Boards are column-major like a 2D
	coordinate system, meaning board[i][j] will access column i, row j.

	Individual pieces may be accessed through their cells, like so:
	board[i][j].piece will reference the piece stored at the cell at
	column i, row j.

	Boards by default are not hypothetical unless they are created by a call
	to clone() on an exisiting board. Hypothetical boards are used by the
	pieces to determine their moves and stop recursion.
	Conversely, special parameter hypothetical is used to flag whether moves
	are being calculated for a hypothetical board (such as checking if the
	king is checked after moving to some cell). This parameter prevents an
	inifite recursion when checking a king's possible moves for instance.

	Boards contain a move stack used to implement undo and a list of dirty
	cells that need to have their clean_moves method called after a move is
	successfully performed.

	'''
	def __init__(self, width=1, height=1):
		'''Create a new instance of Board.

		Parameters width and height specify
		the board's visual width and height for rendering purposes.

		'''
		self.w, self.h = width, height
		self.board = []
		self.move_stack = []
		self.dirty_cells = []

		self.cells = []

		self.white = Player(WHITE, WHITE_RANK, WHITE_PAWN_DIR)
		self.black = Player(BLACK, BLACK_RANK, BLACK_PAWN_DIR)
		self.white.enemy = self.black
		self.black.enemy = self.white
		self.players = [self.white, self.black]

		#Current turn
		self.current_turn = self.white
		self.turns = 1

		#Populate the board with Cells:
		for i in range(0, 8):
			self.board.append([])
			for j in range(0, 8):
				if i % 2 != j % 2:
					color = (0, 0, 0)
				else:
					color = (255, 255, 255)
				cell = Cell((i, j), width/8, color)
				self.board[i].append(cell)
				self.cells.append(cell)

	def __getitem__(self, col):
		'''Overload operator[] so Board cells can be accessed using the
		boad[column][row] convention.

		'''
		return self.board[col[0]][col[1]]

	#def on_cell_selected(self, selected_cell):
	#	'''Handle cell selected events sent by the Board Controller.
	#
	#	This will involve determining the movements for the piece in the
	#	selected cell and updating every destination cell's move list.
	#
	#	'''
	#
	#	if not selected_cell.piece:
	#		return
	#
	#	moves = selected_cell.piece.get_moves(selected_cell.i, selected_cell.j, self)
	#	for move in moves:
	#		col, row = move.to_c, move.to_r
	#		self.board[col][row].add_move(move)
	#		self.dirty_cells.append((col,row))

	def can_move_piece_in_cell_to(self, cell, to):
		'''Determine whether the piece in the cell can move
		to the (to[0], to[1]) cell in the board.

		Returns True if there is a piece in selected_cell and it can move to
		board[to]. This method must be called before calling
		move_piece_in_cell_to.

		'''
		if cell.piece:
			move = cell.piece.get_move(cell.pos, to, self)
			return move is not None and \
					not move.causes_check(self, cell.piece.owner)
		else:
			return False


	def move_piece_in_cell_to(self, player, fro, to, **options):
		'''
		Move a piece from position "fro" to position "to".

		This method checks whether a piece is actually at "fro" and that its
		owner is the given "player" parameter.

		"options" is an optional parameter used to provide move metadata, such
		as the piece a pawn is crowned to.
		'''

		if not self[fro].piece:
			raise MoveError("No piece to move at (%d,%d)" % fro)

		if self[fro].piece.owner != player:
			raise MoveError("Piece at (%d,%d) is not from player %s" %
													(fro[0], fro[1], player))

		move = self[fro].piece.get_move(fro, to, self, **options)
		if not move:
			raise MoveError(
			"No moves take from (%d,%d) to (%d,%d) that this piece knows of" %
				(fro + to))

		self.move_stack.append(move)
		move.perform(self)

		#for col,row in self.dirty_cells:
		#	self.board[col][row].clear_moves()
		self.next_turn()
		return move

	def perform_move(self, move):
		'''Apply a move on the board.

		Normally, callers will use the board.move_piece_in_cell_to method in order
		to move the piece stored in the selected cell to a certain cell in the
		board.

		This method is useful for applying moves on the board which come from
		external sources, such as a Chess Engine (GNU Chess) or over the network
		(when implemented).

		'''

		if not self[move.fro].piece:
			raise MoveError("Cannot move from (%d,%d) to (%d,%d). No piece there." %
								(move.fro + move.to))

		self.move_stack.append(move)
		move.perform(self)
		self.next_turn()
		return move

	def undo_move(self):
		if self.move_stack:
			self.previous_turn()
			self.move_stack.pop().undo(self)

	def get_all_moves(self, owner, attack_only = False, filter_check=False):
		'''Get all owner's moves'''
		#rebuild move cache:
		all_moves = []
		for cell in self.cells:
			if cell.piece and cell.piece.owner == owner:
				all_moves.extend(cell.piece.get_moves(
					cell.pos, self, attack_only,
					filter_check=filter_check))

		return all_moves

	def has_moves(self, owner, filter_check=True):
		for cell in self.cells:
			piece = cell.piece
			if piece and piece.owner == owner and \
			   piece.has_moves(cell.pos, self, filter_check=filter_check):
				return True
		return False

	def get_all_attack_moves(self, owner, piece=None):
		'''Get all owner's enemy's moves.'''
		attack_moves = self.get_all_moves(owner, attack_only=True, filter_check=False)
		if piece is not None:
			return [x for x in attack_moves if self[x.to] == piece]
		else:
			return attack_moves

	def king_is_checked(self, owner):
		'''Check whether the king of the given owner is under attack'''
		#Find the king and all attacks
		king_pos = self.get_king_position(owner)
		for move in self.get_all_attack_moves(owner.enemy):
			if move.to == king_pos:
				return True
		return False

	def king_is_checkmated(self, owner):
		return not self.has_moves(owner, filter_check=True) and \
				self.king_is_checked(owner)

	def get_king_position(self,owner):
		'''Find the owner's (white or black) king's position'''
		for cell in self.cells:
			if cell.piece and cell.piece.type == "king" and \
				cell.piece.owner == owner:
				return cell.pos
		raise Exception("Error: %s king not found" % owner)

	def next_turn(self):
		'''Make the change of turn.'''
		self.turns += 1
		self.current_turn = self.current_turn.enemy
		return self.current_turn

	def previous_turn(self):
		self.turns -= 1
		self.current_turn = self.current_turn.enemy
		return self.current_turn

	def put_piece_at(self, piece, pos):
		if pos[0] < 0 or pos[0] > 7 or pos[1] < 0 or pos[1] > 7:
			raise Exception("Indices out of board: (%d, %d)" % pos)

		self[pos].piece = piece
		self.moves_cache_dirty = True

	def pick(self, x, y):
		'''Try to pick piece in the cell below the x,y screen position.
		If the cell does not contain a piece, return None.'''
		for cell in self.cells:
			if cell.contains(x, y):
				return cell
		return None
