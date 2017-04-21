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
from board import LEFT, RIGHT
from errors import UndoError

def _coord_to_code(c):
	return '%s%d' % (chr(0x61+c[0]), 8-c[1])

# Move classes
class BaseMove(object):
	def __init__(self, fro, to):
		self.fro = fro
		self.to = to
		self.peformed = False
		self.acting_piece = None

		self.type = self.__class__.__name__

	def __eq__(self, other):
		'''Compare instances. Two moves are equal if they take a piece from the
		cell to the same cell'''
		return isinstance(other, BaseMove) and \
				self.fro == other.fro and \
				self.to == other.to

	def __ne__(self, other):
		'''Compare instances. Two moves are not equal if they are not equal.'''
		return not (self == other)

	def perform(self, board):
		self.performed = True
		piece = board[self.fro].piece
		piece.moved(self, board)

	def undo(self, board):
		if not self.performed:
			raise UndoError("Move never performed: from (%d,%d) to (%d,%d)" % \
							(self.fro + self.to))
		piece = board[self.to].piece
		piece.moved_back(self, board)
		self.performed = False

	def causes_check(self, board, owner):
		self.perform(board)
		checked = board.king_is_checked(owner)
		self.undo(board)
		return checked

	def __repr__(self):
		return '%s((%s, %s), (%s, %s))' % (
			(self.__class__.__name__,) +
			self.fro + self.to
		)

class Move(BaseMove):
	'''Represents a regular piece movement in chess.'''
	def __init__(self, fro, to):
		super(Move, self).__init__(fro, to)
		self.attacking = False

	def __eq__(self, other):
		'''Compare instances. Two moves are equal if they take a piece from the
		cell to the same cell'''
		return isinstance(other, Move) and \
				self.fro == other.fro and \
				self.to == other.to

	def perform(self, board):
		'''Perform a move on a board.'''
		super(Move, self).perform(board)
		self.src_piece = board[self.fro].piece
		self.dst_piece = board[self.to].piece

		board[self.to].piece = self.src_piece
		board[self.fro].piece = None

	def undo(self, board):
		'''Undo the effects of a move on a board.'''
		super(Move, self).undo(board)

		board[self.fro].piece = self.src_piece
		board[self.to].piece = self.dst_piece

	def __str__(self):
		if self.acting_piece:
			piece_code = self.acting_piece.CODE
		else:
			piece_code = ''
		#return '%s%s%s' % (piece_code, self.attacking and 'x' or '',  _coord_to_code(self.to))
		return "%s%s" % (_coord_to_code(self.fro), _coord_to_code(self.to))

class EnPassant(BaseMove):
	def __init__(self, fro, dir, owner):
		assert dir in (LEFT, RIGHT)
		super(EnPassant, self).__init__(
			fro,
			(fro[0] + dir, fro[1] + owner.pawn_dir))
		self.attacking = True

	def perform(self, board):
		super(EnPassant, self).perform(board)
		# destination can not have a piece since the captured pawn has just movd
		self.src_piece = board[self.fro].piece
		self.captured = board[self.to[0], self.fro[1]].piece

		board[self.fro].piece = None
		board[self.to].piece = self.src_piece
		board[self.to[0], self.fro[1]].piece = None

	def undo(self, board):
		super(EnPassant, self).undo(board)

		board[self.fro].piece = self.src_piece
		board[self.to].piece = None
		board[self.to[0], self.fro[1]].piece = self.captured

	def __str__(self):
		#return '%s(ep)' % _coord_to_code(self.to)
		return '%s%s' % (_coord_to_code(self.fro), \
				_coord_to_code(self.to))

class Castling(BaseMove):
	QUEENSIDE = 'left'
	KINGSIDE = 'right'
	'''Represents a Castling move in chess.'''
	def __init__(self, castling_type, castling_owner):
		'''Create a new instance of a Castling Move. Valid castling_types
			are "left" and "right"'''
		if not castling_type in [Castling.QUEENSIDE, Castling.KINGSIDE]:
			raise Exception("Invalid Castling type: " + castling_type)
		super(Castling, self).__init__(
				(4, castling_owner.rank),
				(castling_type == Castling.KINGSIDE and 6 or 2, castling_owner.rank))
		self.castling_type = castling_type
		self.castling_owner = castling_owner

	def __eq__(self, other):
		'''Compare instances. Two castling instances are equal if they are the
		same type'''
		return isinstance(other, Castling) and \
				self.castling_type == other.castling_type

	def perform(self, board):
		'''Perform a Castling move on a board.'''
		super(Castling, self).perform(board)
		j = self.castling_owner.rank
		self.castling_owner.castling_allowed = False

		if self.castling_type == Castling.QUEENSIDE:
			board[2,j].piece = board[4,j].piece
			board[4,j].piece = None
			board[3,j].piece = board[0,j].piece
			board[0,j].piece = None
		elif self.castling_type == Castling.KINGSIDE:
			board[6,j].piece = board[4,j].piece
			board[4,j].piece = None
			board[5,j].piece = board[7,j].piece
			board[7,j].piece = None
		else:
			raise MoveError("Invalid Castling type. Valid types are '%s' and '%s'" %
				   (Castling.QUEENSIDE, Castling.KINGSIDE))

	def undo(self, board):
		'''Undo a Castling move.'''
		super(Castling, self).undo(board)
		j = board.current_turn.rank
		self.castling_owner.castling_allowed = True

		if self.castling_type == Castling.QUEENSIDE:
			board[4, j].piece = board[2, j].piece
			board[2, j].piece = None
			board[0, j].piece = board[3, j].piece
			board[3, j].piece = None
		elif self.castling_type == Castling.KINGSIDE:
			board[4, j].piece = board[6, j].piece
			board[6, j].piece = None
			board[7, j].piece = board[5, j].piece
			board[5, j].piece = None
		else:
			raise MoveError("Invalid Castling type. Valid types are '%s' and '%s'" %
				   (Castling.QUEENSIDE, Castling.KINGSIDE))

	def __str__(self):
		#if self.acting_piece:
		#	piece_code = self.acting_piece.CODE
		#else:
		#	piece_code = ''
		if self.castling_type == Castling.QUEENSIDE:
			return '0-0-0'# % piece_code
		elif self.castling_type == Castling.KINGSIDE:
			return '0-0'# % piece_code

class Crowning(BaseMove):
	'''Represents a Pawn Crowning move in chess.'''
	def __init__(self, fro, to, piece):
		super(Crowning, self).__init__(fro, to)
		self.piece = piece

	def __eq__(self, other):
		'''Compare instances. Two Crowning moves are equal if they move from
		the same cell to the same cell and crown into the same piece'''
		return isinstance(other, Crowning) and \
			self.fro == other.fro and self.to == other.to and \
			self.piece == other.piece

	def perform(self, board):
		'''Perform this move on a board.'''
		super(Crowning, self).perform(board)
		self.src_piece = board[self.fro].piece
		self.dst_piece = board[self.to].piece

		board[self.to].piece = self.piece
		board[self.fro].piece = None

	def undo(self, board):
		'''Undo the effects of this move on a board.'''
		super(Crowning, self).undo(board)
		board[self.fro].piece = self.src_piece
		board[self.to].piece = self.dst_piece

	def __str__(self):
		#if self.acting_piece:
		#	piece_code = self.acting_piece.CODE
		#else:
		#	piece_code = ''
		return '%s%s%s' % (_coord_to_code(self.fro),\
					_coord_to_code(self.to), \
					self.piece.CODE)
		#return '%s%s(%s)' % (
		#	piece_code,
		#	_coord_to_code(self.to),
		#	self.piece.CODE)

class BasePiece(object):
	'''Base class for pieces.'''
	def __init__(self, owner):
		'''Create a new instance of Piece.'''
		self.owner = owner
		self.move_cache = []
		self.attack_cache = []
		self.type = self.__class__.__name__.lower()
		self.move_count = 0

	def __eq__(self, other):
		return isinstance(other, BasePiece) and self.type == other.type and self.owner == other.owner

	def is_turn(self, lastowner):
		if self.owner == lastowner:
			return True
		else:
			return False

	def moved(self, move, board):
		self.move_count += 1
		self.r, self.c = move.to

	def moved_back(self, move, board):
		self.move_count -= 1
		self.r, self.c = move.fro

	def get_move(self, fro, to, board, **options):
		# FIXME filter move by selected options
		for move in self.get_moves(fro, board, **options):
			if move.to == to:
				return move
		return None

	def get_moves(self, fro, board, attack_only = False, filter_check=False,
			   **options):
		moves = self._get_moves(fro, board, attack_only = attack_only, **options)
		for move in moves:
			move.acting_piece = self
		if filter_check:
			return [x for x in moves if not x.causes_check(board, self.owner)]
		else:
			return moves

	def has_moves(self, fro, board, filter_check=True):
		return len(self.get_moves(fro, board, attack_only=False, filter_check=filter_check)) > 0

DIR_N = ( 0,-1) # delta column, delta row
DIR_S = ( 0, 1)
DIR_W = (-1, 0)
DIR_E = ( 1, 0)

DIR_NE = ( 1, -1)
DIR_NW = (-1, -1)
DIR_SE = ( 1,  1)
DIR_SW = (-1,  1)

DIRS_DIAGONALS = [DIR_NE, DIR_NW, DIR_SE, DIR_SW]
DIRS_HORIZONTALS = [DIR_E, DIR_W, DIR_S, DIR_N]
DIRS_ALL = DIRS_HORIZONTALS + DIRS_DIAGONALS

def _cascades(dirs, fro, board, owner):
	'''Cascade calculates al moves from a given coordinate in all given directions.
	'''
	dests = []
	for dc,dr in dirs:
		to = (fro[0] + dc, fro[1] + dr)
		p = None
		while 0 <= to[0] < 8 and 0 <= to[1] < 8 and not p:
			p = board[to].piece
			if not p or p.owner != owner:
				dests.append(Move(fro, to))
			to = (to[0] + dc, to[1] + dr)
	return dests

class Knight(BasePiece):
	'''Representation of the Knight piece.'''

	CODE = 'N'

	def __init__(self, owner):
		'''Create a new instance of Knight. owner may be "white" or "black".'''
		super(Knight, self).__init__(owner)

	def _get_moves(self, (col, row), board, attack_only = False, **options):
		dests = []
		for x in (1,-1):
			for y in (2, -2):
				for c, r in ((col+x,row+y),(col+y,row+x)):
					if 0 <= c < 8 and 0 <= r < 8:
						p = board[c,r].piece
						if not p or p.owner != self.owner:
							dests.append(Move((col, row), (c, r)))
		return dests

class Rook(BasePiece):
	'''Representation of the Rook piece.'''

	CODE = 'R'

	def __init__(self, owner):
		'''Create a new instance of Rook. owner may be "white" or "black".'''
		super(Rook, self).__init__(owner)

	def _get_moves(self, fro, board, attack_only = False, **options):
		return _cascades(DIRS_HORIZONTALS, fro, board, self.owner)

class Bishop(BasePiece):
	'''Representation of the Bishop piece.'''

	CODE = 'B'

	def __init__(self, owner):
		'''Create a new instance of Bishop. owner may be "white" or "black".'''
		super(Bishop, self).__init__(owner)

	def _get_moves(self, fro, board, attack_only = False, **options):
		return _cascades(DIRS_DIAGONALS, fro, board, self.owner)

class Queen(BasePiece):
	'''Representation of the Queen piece'''

	CODE = 'Q'

	def __init__(self, owner):
		'''Create a new instance of Queen. owner may be "white" or "black".'''
		super(Queen, self).__init__(owner)

	def _get_moves(self, fro, board, attack_only = False, **options):
		return _cascades(DIRS_ALL, fro, board, self.owner)

class King(BasePiece):
	'''Representation of the King piece'''

	CODE = 'K'

	def __init__(self, owner):
		'''Create a new instance of King. owner may be "white" or "black".'''
		super(King, self).__init__(owner)

	def _get_moves(self, (col, row), board, attack_only = False, **options):
		dests = []
		for dc in [-1,0,1]:
			for dr in [-1,0,1]:
				c = col + dc
				r = row + dr
				if 0 <= c < 8 and 0 <= r < 8:
					p = board[c,r].piece
					if not p or (p.owner != self.owner):
						dests.append(Move((col,row),(c,r)))

		if not attack_only:
			threats = [x.to for x in board.get_all_attack_moves(self.owner.enemy)]
			#Castling
			if not self.move_count and \
				not board.king_is_checked(self.owner):
				right_rook = board[7,row].piece
				left_rook = board[0,row].piece
				if right_rook and not right_rook.move_count and \
					not board[col+1,row].piece and \
					not board[col+2,row].piece and \
					(col+2, row) not in threats and \
					(col+1, row) not in threats:
						dests.append(Castling(Castling.KINGSIDE, self.owner))

				if left_rook and not left_rook.move_count and \
					not board[col-1,row].piece and \
					not board[col-2,row].piece and \
					not board[col-3,row].piece and \
					(col-2, row) not in threats and \
					(col-1, row) not in threats:
						dests.append(Castling(Castling.QUEENSIDE, self.owner))
			dests = filter(lambda x: x.to not in threats, dests)
		return dests

class Pawn(BasePiece):
	'''Representation of the Pawn piece.'''

	CODE = 'P'

	def __init__(self, owner):
		super(Pawn, self).__init__(owner)
		'''Create a new instance of Pawn. owner may be "white" or "black".'''
		self.en_passant = 0

	def moved(self, move, board):
		if move.to[1] == self.owner.rank + self.owner.pawn_dir * 3:
			self.en_passant = board.turns

	def _get_moves(self, (col, row), board, attack_only = False, **options):
		dests = []
		dr = self.owner.pawn_dir
		rank = self.owner.rank

		#Bound checking:
		if 0 <= row + dr < 8:
			#Normal move or Crowning?
			if not attack_only:
				if row + dr != 0 and row + dr != 7:
					if not board[col, row + dr].piece:
						dests.append(Move((col, row), (col, row + dr)))
				else:
					if not board[col, row + dr].piece:
						# create the piece from the given class name :ugh:
						type = options.get('type', Queen.CODE)
						dests.append(Crowning((col, row), (col, row + dr),
							PIECES_BY_CODE[type](self.owner)))

				#Double step:
				if row == rank + dr and \
					not board[col, row + 2*dr].piece and \
					not board[col, row + 1*dr].piece:
					dests.append(Move((col, row), (col, row + 2 * dr)))

			#Attack moves:
			for dir in LEFT, RIGHT:
				if 0 <= col + dir < 8:

					# normal attack
					p = board[col+dir, row+dr].piece
					if p and p.owner != self.owner:
						if row + dr != 0 and row + dr != 7:
							dests.append(Move((col, row), (col + dir, row + dr)))
						else:
							# Crowning attack
							dests.append(Crowning((col, row), (col + dir, row + dr), Queen(self.owner)))

					# en passant
					elif row == (self.owner.enemy.rank + self.owner.enemy.pawn_dir * 3):
						p = board[col + dir, row].piece
						if p and p.owner != self.owner and p.type == self.type and p.en_passant == board.turns -1:
							dests.append(EnPassant((col, row), dir, self.owner))
		return dests

PIECES = (Rook, Knight, Queen, King, Pawn, Bishop)
PIECES_BY_CODE = dict([(x.CODE, x) for x in PIECES])
