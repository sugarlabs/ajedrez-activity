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

#class DebugMessenger:
#	def __init__(self):
#		print "creating new debug messenger"
#		self.messages = []
#		self.y_spacing = 25
#		self.surface_h = 200
#
#	def render_messages(self, surface):
#		self.surface_h = surface.get_height()
#		y = 10
#		for message in self.messages:
#			font = pygame.font.Font(None, 25) 
#			text_color = font.render(message, 1, (90, 255, 90))
#			surface.blit(text_color, (10, y))
#			y += self.y_spacing
#
#	def add_message(self, message):
#		'''Add a message to this messenger. Always use this method to
#		add messages, since the internal structure of this class may
#		be changed in the future.'''
#		self.messages.append(message)
#		while len(self.messages)*self.y_spacing > self.surface_h/2:
#			print "pop"
#			self.messages.pop(0)

class Message():
	def __init__(self, text, x = 0, y = 0, color = (0, 255, 0)):
		self.x = x
		self.y = y
		self.text = text
		self.color = color

class Messenger():
	def __init__(self):
		#print "creating new messenger"
		self.messages = {}
		self.font = None

	def render_messages(self, surface):
		if self.font is None:
			self.font = pygame.font.Font(None, 25)
		for key,message in self.messages.iteritems():
			text_sface = self.font.render(message.text, 1, message.color)
			surface.blit(text_sface, (message.x, message.y))

messenger = Messenger()

