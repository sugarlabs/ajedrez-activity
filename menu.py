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
import logging
from resourcemanager import image_manager

log = logging.getLogger()

class Menu:
	def __init__(self, screen_w, screen_h, options):
		'''The Game menu for selecting the play mode or quitting.
		options contains a list of options, such as:
		["New CPU Game", "New PvP Game", "Quit Ceibal-Chess"]. 
		The option clicked by the user is returned by the on_click
		method'''

		self.scr_w = screen_w
		self.scr_h = screen_h

		self.bg_w = 2 * screen_w / 3
		self.bg_h = 2 * screen_h / 3 + 20

		self.font = None

		self.visible = False

		self.btn_back_img = None
		self.menu_back_img = None

		self.options = options

		self.option_coords = []
		for option in self.options:
			self.option_coords.append((0,0))

	def toggle_visible(self):
		if self.visible:
			self.visible = False
		else:
			self.visible = True

	def render(self, surface):
		if not self.visible:
			return

		if self.font is None:
			self.font = pygame.font.Font(None, 30)

		#Render bg:
		bg_x = (self.scr_w - self.bg_w) / 2
		bg_y = (self.scr_h - self.bg_h) / 2
		if not self.menu_back_img:
			self.load_menu_bg("menu_back.png")

		surface.blit(self.menu_back_img, pygame.Rect(bg_x, bg_y, self.bg_w, self.bg_h))

		#Render menu options:
		entry_w = 2 * self.bg_w / 3
		entry_x = bg_x + (self.bg_w - entry_w) / 2
		entry_y = bg_y + (self.bg_h - (self.font.get_height()+ 40 + 20)*len(self.options)) / 2
		#print "bg_h:", self.bg_h, "entries_height:", (self.font.get_height()+20)*len(self.options)

		for i in range(0, len(self.options)):
			option = self.options[i]
			#text_sface = self.font.render(option, 1, (255, 255, 255))
			text_sface = self.font.render(option, 1, (170, 88, 0))

			entry_h = text_sface.get_height() + 20

			#Button background:
			if not self.btn_back_img:
				self.btn_back_img = image_manager.get_image("btn_back.png")

			entry_x = bg_x + (self.bg_w - self.btn_back_img.get_width()) / 2
			surface.blit(self.btn_back_img, pygame.Rect(entry_x, entry_y, entry_w, entry_h))
			
			#Button text:
			x = entry_x + (self.btn_back_img.get_width() - text_sface.get_width())/2
			surface.blit(text_sface, (x, entry_y+(self.btn_back_img.get_height()-text_sface.get_height())/2))

			#self.option_coords[i] = (entry_x, entry_y, entry_x+entry_w, entry_y+entry_h)
			self.option_coords[i] = (entry_x, entry_y, entry_x+self.btn_back_img.get_width(), \
						entry_y+self.btn_back_img.get_height())

			entry_y += entry_h + 40

	def on_click(self, x, y):
		if not self.visible:
			raise Exception("Called on_click on the menu while it was hidden!")
		
		for i in range(0, len(self.options)):
			coords = self.option_coords[i]
			if x > coords[0] and x < coords[2] and y > coords[1] and y < coords[3]:
				log.debug("Selected %s", self.options[i])
				return self.options[i]
		return None

	def load_menu_bg(self, filename):
		'''Load an image file from the data directory and store it in dest'''
		bg1 = image_manager.get_image(filename)
		bg2 = image_manager.get_image("menu_back2.png")
		
		bg1 = pygame.transform.scale(bg1, (self.bg_w, self.bg_h))
		bg2 = pygame.transform.scale(bg2, (int(self.bg_w/1.1), int(self.bg_h/1.1)))
		self.menu_back_img = bg1
		tx = (bg1.get_width()-bg2.get_width())/2
		ty = (bg1.get_height()-bg2.get_height())/2
		self.menu_back_img.blit(bg2, bg2.get_rect().move(tx, ty))
