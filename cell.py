#
#    Ceibal Chess - A chess activity for Sugar.
#    Copyright (C) 2009 Alejandro Segovia <asegovi@gmail.com>
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

class Cell(object):
	'''A Cell instance represents a cell in a Board which may or may not store
	a piece.

	Cells are the objects that know where pieces are in the board.
	Positions in the board are representd by the i and j
	attributes, where i is the column the cell is at within the board and j is
	the row the cell is at in the board.

	In order to simplify the implementation of the board, cells are aware of the
	valid moves that take to them. This is stored in the special list "moves" and
	works as follows:

	1) When a cell is selected on the board and its moves are calculated, cells
	where that piece may move to are notified by having their add_move method
	called.

	2) When the user requests a move to be performed, the board will match the
	valid moves at the given destination's cell with the cell selected at the
	moment (the cell that contains the piece that's about to be moved).

	3) The move is performed and all the cells move lists are cleared.
	'''
	def __init__(self, pos, size, color, piece = None):
		'''Create a new instance of Cell.
		Expected parameters are:
			color: the color of the cell.
			pos: the cell position.
			size: attribute determining the size of the cell when rendered.
			piece: the piece this cell contains (None by default).
		'''
		self.color = color
		self.piece = piece
		self.size = size
		self.pos = pos
		self.moves = []

	def __getitem__(self, idx):
		return self.pos[idx]

	def __eq__(self, other):
		return isinstance(other, Cell) and self.pos == other.pos

	def contains(self, x, y):
		'''Return True if this cell contains the given (x,y) point,
		False otherwise. This method is used to implement pick()ing into the
		board.'''
		tx = self[0] * self.size
		ty = self[1] * self.size

		if x > tx and x < tx + self.size and \
			y > ty and y < ty + self.size:
				return True

	def add_move(self, move):
		'''Add a move to the list of possible moves that take pieces to this cell.'''
		self.moves.append(move)

	def clear_moves(self):
		'''Erase the list of possible moves that take pieces into this cell. '''
		self.moves = []
