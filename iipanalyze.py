#!/usr/bin/python
#-*- coding: iso-8859-15 -*-

#    iipanalyze: Tool for analyzing incoming IIP protocol image requests to the IIPImage server. 
#    It can output data on which are the most viewed parts of a particular image and display histograms showing 
#    tile usage, globally or per resolution level. It can also output image maps showing visually which parts 
#    of a particular image are most viewed for any given resolution.

#    Copyright (c) 2012 IIPImage
#    Author: <Laurent Le Guen>

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import sys
import getopt
import operator
import Image, ImageDraw
import urllib
import re
import math
import StringIO
import exceptions

#Check if matplotlib is installed or not
matplot = 0
try:
	import matplotlib.pyplot as plt
except ImportError:
	matplot = 1

def help():
	print "\niipanalyze: version 0.1\n"
	print 'Tool for analyzing incoming IIP protocol image requests to the IIPImage server.'
	print 'Requires web server log file in Common Log Format (CLF).'
	print 'Can display hotspot map and histogram showing number of hits per tile.'
	print 'Options:'
	print '	-h --help				Print this help'
	print '	-l --logfile <logfile>			Web server log file in common log format (CLF)'
	print '	-i --image <full name of the image>	Name of the image you want to search e.g. "test.tif"'
	print '	-r --resolution <resolution>		Resolution between 0 and the max available resolution of image'
	print '	-a --address <IP address>		Filter by IP address'
	print '	-o --output <output hotspot map>	Select an output file for the hotspot map'
	print '	-w --width <width of hotspot map>	Width of the hotspot map image'
	print '	-g --gamma <gamma>			Apply a gamma to hotspot map (can improve visibility of tiles)'
	print '	-b --background				Apply background of image to the hotspot map'
	print '	-p --plot				Plot histogram (requires matplotlib)'
	print "\nSee http://iipimage.sourceforge.net for more details\n"


#Quick function to get the url of the image from the logfile
def get_url (logfile, image_name):
	begin_url = 'GET '
	end_url = 'FIF='
	for line in logfile:
		if (image_name in line):
			url = line[line.find(begin_url) + len(begin_url):line.find(end_url)]
	return url


#Create the dictionnaries
def create_dic (line, resolutio, tile, restil, restildef):
	try:
		expression = re.search(r'[jJ][tT][lL]=(.*?),(.*?)[( HTTP)(\?)]', line)
		if expression!=None:
			resol = int(expression.group(1))
			if len(expression.group(2)) != 0:
				til = int(expression.group(2))

				resolutio[resol] = resolutio.get(resol,0) + 1
				tile[til] = tile.get(til,0) + 1
				restil[(resol,til)] = (resolutio.get(resol,0) and tile.get(til,0))
	except:
		return


#Print dictionnary that shows the tiles
def print_dic (resolutio, tile):
	print "resolution : " , resolutio
	print "Tile\tnumber"
	for key,value in iter(sorted(tile.iteritems(), reverse=True, key=operator.itemgetter(1))):
		print("{}\t{}".format(key, value))


#Print the list that shows the resolution, the tile and the number of hit
def print_list (tri_restil):
	print "resolution\ttile\tnumber"
	for item in tri_restil:
		print (item[0])[0] , "\t" , (item[0])[1] , "\t" , item[1]


#Create the final image
def create_image (draw, new_tile_size, key, nb_tile_width, tile, tile_size, gamma):
	
	x = new_tile_size*(key-(nb_tile_width*(key//nb_tile_width)))
	y = new_tile_size*(key//nb_tile_width)
	x1 = new_tile_size*(key-(nb_tile_width*((key//nb_tile_width)))+1)
	y1 = new_tile_size*((key//nb_tile_width)+1)
	fill_value = (tile[key]**gamma)*256/(max(tile.values())**gamma)
	draw.rectangle( [ x,y,x1,y1 ],fill=(fill_value) )


#Save the final image
def save_image (im, output, buffer,background):
	im.save(output)
	if background == 1:
		im1 = Image.open(output)
		im_url = Image.open(StringIO.StringIO(buffer))
		mask = im1.point(lambda i: 200)
		im_url.paste(im1,(0,0),mask)
		im_url.save(output)


#Function that plot the histogram
def plot (tile):
	plt.bar(tile.keys(), tile.values(), align='center')
	plt.xlabel("Tile Index")
	plt.ylabel("Number of hits")
	plt.title("Tile Index vs Number of hits")
	plt.show()
	




def main(argv):

	try:
		histo = 0
		imout = 0
		resolution_image = 0
		address_ip = 0
		gamma = 1
		background = 0
		logfile = None
		image_name = None
		render_width = 800
	
		#Get the arguments from the command line
		try:
			opts, args = getopt.getopt(argv,"phbl:i:r:w:o:a:g:",["plot=","help=","background=","logfile=","image=","resolution=","width=","output=","address=","gamma="])
		except getopt.GetoptError:
			help()
			return

		for opt, arg in opts:
			if opt == '-h':
				help()
				return
			if opt in ("-l", "--logfile"):
				logfile = arg
			if opt in ("-i", "--image"):
				image_name = arg
			if opt in ("-r", "--resolution"):
				resolution = arg
				resolution_image = 1
			if opt in ("-w", "--width"):
				render_width = int(arg)
			if opt in ("-o", "--output"):
				output = arg
				imout = 1
			if opt in ("-a", "--address"):
				address = arg
				address_ip = 1
			if opt in ("-p","--plot"):
				if matplot == 0:
					histo = 1
				else:
					histo = 0
					print "Matplotlib is not installed"
			if opt in ("-g","--gamma"):
				gamma = float(arg)
			if opt in ("-b","--background"):
				background = 1

		#Get the informations from the logfile
		if not(logfile and image_name):
			help()
			print "Must give logfile and image name"
			return

		logfile = open(logfile,'r')
		url = get_url(logfile, image_name)

		#Get the resolution number from the web
		try:
			resolution_number = int((urllib.urlopen("%4sFIF=%4s&obj=resolution-number" % (url,image_name))).read()[20:])
		except:
			help()
			print 'Unable to get number of resolutions from server with URL ', "%4sFIF=%4s&obj=resolution-number" % (url,image_name)
			sys.exit()


		if (resolution_image == 1 and (int(resolution) < 0 or int(resolution) > (resolution_number-1))):
			help()
			print 'Resolution must be between', 0, 'and', (resolution_number-1)
			sys.exit()
			

		image_Size = (urllib.urlopen("%4sFIF=%4s&obj=max-size" % (url,image_name))).read()[11:] #Get the image size from the web
	
		#Definition of the characteristics of the image 
		image_width = int(image_Size.split()[0])
		image_height = int(image_Size.split()[1])

		image_size = (image_width,image_height)

		Tile_size = (urllib.urlopen("%4sFIF=%4s&obj=tile-size" % (url,image_name))).read()[12:15]

		tile_size = float(Tile_size)
	
		#Adaptation to the size of the image selected by the user
		if (resolution_image == 1 and int(resolution) != resolution_number-1): #If the resolution is different from the max resolution
			new_tile_size = (tile_size*render_width/image_width)*(2**((resolution_number-1)-int(resolution)))
			nb_tile_width = math.ceil(image_width/tile_size/(2**((resolution_number-1)-int(resolution))))
			nb_tile_height = math.ceil(image_height/tile_size/(2**((resolution_number-1)-int(resolution))))
		else: #Else if it is the max resolution
			new_tile_size = tile_size*render_width/image_width
			nb_tile_width = math.ceil(image_width/tile_size)
			nb_tile_height = math.ceil(image_height/tile_size)
	
		size = (render_width, (render_width*image_height)/image_width)

		#Put the image into a buffer
		image_url = (urllib.urlopen("%4sFIF=%4s&wid=%d&cvt=jpeg" % (url,image_name,render_width)))
		buffer = image_url.read()

		#go back to the begining of the logfile
		logfile.seek(0)

		#Define dictionnaries
		resolutio = {}
		tile = {}
		restil = {}
		restildef = {}
	
		#If user defines both resolution and ip address
		if (resolution_image == 1 and address_ip == 1):
			for line in logfile.readlines():
				expression = re.search(r'[jJ][tT][lL]=(.*?),(.*?)[( HTTP)(\?)]', line)
				if ((address in line) and (image_name in line) and expression!=None and expression.group(1) == resolution):
					create_dic (line, resolutio, tile, restil, restildef)

			#Print the list that shows the tiles and the number of hits
			print_dic (resolutio, tile)	
		
			#Create the image that shows the repartition of the hits on the tiles
			im = Image.new('L',size)
			draw = ImageDraw.Draw(im)
			for key in tile.keys():
				create_image (draw, new_tile_size, key, nb_tile_width, tile, tile_size, gamma)
			del draw

			#Save the final image
			if imout == 1:
				save_image (im, output, buffer,background)
			
		#If user only defines the resolution
		elif resolution_image == 1:
			for line in logfile.readlines():
				expression = re.search(r'[jJ][tT][lL]=(.*?),(.*?)[( HTTP)(\?)]', line)
				if (image_name in line and expression!=None and expression.group(1) == resolution):
					create_dic (line, resolutio, tile, restil, restildef)
			
			#Print the list that shows the tiles and the number of hits
			print_dic (resolutio, tile)	
		
			#Create the image that shows the repartition of the hits on the tiles
			im = Image.new('L',size)	
			draw = ImageDraw.Draw(im)
			for key in tile.keys():
				create_image (draw, new_tile_size, key, nb_tile_width, tile, tile_size, gamma)
			del draw

			#Save the final image
			if imout == 1:
				save_image (im, output, buffer,background)

		#If user only defines the ip address
		elif address_ip == 1:
			for line in logfile.readlines():
				expression = re.search(r'[jJ][tT][lL]=(.*?),(.*?)[( HTTP)(\?)]', line)
				if ((address in line) and (image_name in line) and expression!=None):
					create_dic (line, resolutio, tile, restil, restildef)
					tri_restil = sorted(restil.iteritems(), reverse=True, key=operator.itemgetter(1))

			#Print the list that shows the resolution, the tiles and the number of hits
			print_list(tri_restil)

		#In all other cases :
		else:
			for line in logfile.readlines():
				expression = re.search(r'[jJ][tT][lL]=(.*?),(.*?)[( HTTP)(\?)]', line)
				if (image_name in line and expression!=None):
					create_dic (line, resolutio, tile, restil, restildef)
					tri_restil = sorted(restil.iteritems(), reverse=True, key=operator.itemgetter(1))

			#Print the list that shows the resolution, the tiles and the number of hits
			print_list(tri_restil)

		#Plot histogram
		if histo == 1:
			plot (tile)

		#Close the logfile
		logfile.close()

	except IOError as (errno, strerror):
		help()	
		print "I/O error({0}): {1}".format(errno, strerror)

	except SystemExit as (errno, strerror):
		help()
		print "System error({0}): {1}".format(errno, strerror)

	except:
		help()
		print "Unexpected error:", sys.exc_info()[0]

if __name__ == "__main__":
	main(sys.argv[1:])
