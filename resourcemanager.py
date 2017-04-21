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
import pygame
import os
import logging

log = logging.getLogger()

class ImageManager:
	'''Load and manage images, making them available through the applications.
	All image access should be performed through the singleton instance of
	this class, under the name imagem_anager. Usage of pygame.image.load
	should be avoided in favor of image_manager.get_image(<img_file_name>).'''

	def __init__(self):
		'''Create a new instance of ImageManager. Only one instance of
		this class should exist at any time, which is accessible as
		the variable "image_manager"'''
		self.images = { }

	def get_image(self, imgname):
		'''Look for an image in the internal image dictionary. If the
		image is available, return it, otherwise load it from disk and keep
		an keep a reference to it.'''
		try:
			return self.images[imgname]
		except KeyError, err:
			log.debug("Image '%s' not found. Loading...", imgname)

		try:
			path = os.environ["SUGAR_BUNDLE_PATH"]
			if not "Ajedrez.activity" in path:
				print "Running ceibal-chess from Terminal or some other place"
				path = ""
		except:
			path = ""

		self.images[imgname] = pygame.image.load(os.path.join(path, "data_bw", imgname))
		log.debug("Image '%s': %dx%d" % (imgname, \
					self.images[imgname].get_width(), \
					self.images[imgname].get_height()))
		return self.images[imgname]

#ImageManager singleton
image_manager = ImageManager()
