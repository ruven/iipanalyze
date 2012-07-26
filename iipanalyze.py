#!/usr/bin/python
#-*- coding: iso-8859-15 -*-

#    iipanalyze: Tool for analyzing incoming IIP protocol image requests to the IIPImage server. 
#    It can output data on which are the most viewed parts of a particular image and display histograms showing 
#    tile usage, globally or per resolution level. It can also output image maps showing visually which parts 
#    of a particular image are most viewed for any given resolution.

#    Copyright (C) <2012>  <Laurent Le Guen>

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
import datetime
from time import mktime as mktime

#Check if matplotlib is installed or not
matplot = 0
try:
	import matplotlib.pyplot as plt
except ImportError:
	matplot = 1

def help():
	print "\niipanalyze: version 0.2\n"
	print 'Tool for analyzing incoming IIP protocol image requests to the IIPImage server.'
	print 'Requires web server log file in Common Log Format (CLF).'
	print 'Can display hotspot map and histogram showing number of hits per tile.'
	print 'Options:'
	print '	-h --help				Print this help'
	print '	-l --logfile <logfile>			Web server log file in common log format (CLF)'
	print '	-i --image <full name of the image>	Name of the image you want to search e.g. "test.tif"'
	print '	-r --resolution <resolution>		Resolution between 0 and the max available resolution of image'
	print '	-o --output <output hotspot map>	Select an output file for the hotspot map'
	print '	-w --width <width of hotspot map>	Width of the hotspot map image'
	print '	-b --background				Apply a background to the hotspot map image'
	print '	-g --gamma <gamma>			Apply a gamma to hotspot map (can improve visibility of tiles)'
	print '	-a --address <IP address>		Filter by IP address'
	print ' -u --user <user agent>			Filter by user agent'
	print '	-p --plot				Plot histogram (requires matplotlib)'
	print '	-t --time				Plot the histogram of connection activitity with respect to time'
	print '	-n --bins				Select the number of bins for the "time histogram"'
	print '	-d --range				Select an interval of time on the "time histogram"'
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
	print "resolution\ttile\t\tnumber"
	for item in tri_restil:
		print (item[0])[0] , "\t\t" , (item[0])[1] , "\t\t" , item[1]


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
	plt.xlabel("Tiles")
	plt.ylabel("Number of hits")
	plt.title("Tiles vs Number of hits")
	plt.show()
	

#Convert months in letter to months in number
def define_month(hour_expression):
	if hour_expression.group(2) == "Jan":
		month = 1
	if hour_expression.group(2) == "Feb":
		month = 2
	if hour_expression.group(2) == "Mar":
		month = 3
	if hour_expression.group(2) == "Apr":
		month = 4
	if hour_expression.group(2) == "May":
		month = 5
	if hour_expression.group(2) == "Jun":
		month = 6
	if hour_expression.group(2) == "Jul":
		month = 7
	if hour_expression.group(2) == "Aug":
		month = 8
	if hour_expression.group(2) == "Sep":
		month = 9
	if hour_expression.group(2) == "Oct":
		month = 10
	if hour_expression.group(2) == "Nov":
		month = 11
	if hour_expression.group(2) == "Dec":
		month = 12
	return month

def define_full_date(line):
	hour_expression = re.search(r'\[(.*?)/(.*?)/(.*?):(.*?):(.*?):(.*?) +', line)
	month = define_month(hour_expression)
	hour = datetime.time(int(hour_expression.group(4)),int(hour_expression.group(5)),int(hour_expression.group(6)))
	dat = datetime.date(int(hour_expression.group(3)), month, int(hour_expression.group(1)))
	full_date = datetime.datetime.combine(dat, hour)
	return full_date

#Create the final list to plot the time histogram
def create_list(full_time, dic, ranged, range_interv, interval):
	#Create a dictionnary from the list
	for key, val in full_time:
		dic.setdefault(key, []).append(val)

	#Bring back every values from epoch time to zero second
	for i in dic:
		count = 0
		for j in dic[i]:
			if count == 0:
				init = dic[i][0]
			if j-init != 0:
				dic[i][count] = j-init
			else:
				dic[i][count] = 0
			count += 1

	#If there are more than one user, add each time from each user
	var = 0
	for i in dic.values():
		if var == 0:
			resultat = i
			var = 1
		else:
			resultat = resultat + i

	#If user wants to define an interval
	resultat = sorted(resultat)
	if ranged == 1:
		for r in resultat:
			if int(r) <= range_interv and int(r) > 0:
				interval.append(r)
	else:
		for r in resultat:
			if int(r) > 0:
				interval.append(r)
	return interval


#Plot the time histogram
def plot_time(create_li, bina, ranged, address_ip, user_agent):
	plt.hist(create_li, bins=bina)
	if (address_ip == 1 or user_agent == 1):
		plt.xlabel("Time (sec) since the first visit of the user")
	else:
		plt.xlabel("Time (sec) since the first visit of each user")
	plt.ylabel("Number of visited tiles")
	plt.title("Time (sec) vs Number of visited tiles")
	plt.show()




def main(argv):

	try:
		histo = 0
		imout = 0
		resolution_image = 0
		address_ip = 0
		user_agent = 0
		gamma = 1
		background = 0
		logfile = None
		image_name = None
		expr = None
		render_width = 800
		nbr_user = 0
		nb_hits_res = 0
		month = 0
		bina = 60
		hist_bin = 0
		ranged = 0
		range_interv = 0
		hist_time = 0
		create_li = []
		resultat = []
		interval = []
		users =  []
		full_time = []
		dic = {}
	
		#Get the arguments from the command line
		try:
			opts, args = getopt.getopt(argv,"phbtl:i:r:w:o:a:g:u:n:d:",["plot=","help=","background=","time=","logfile=","image=","resolution=","width=","output=","address=","gamma=","user=","bins=","range="])
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
			if opt in ("-t","--time"):
				hist_time = 1
			if opt in ("-u", "--user"):
				user = arg
				user_agent = 1
			if opt in ("-n", "--bins"):
				bina = int(arg)
				hist_bin = 1
			if opt in ("-d", "--range"):
				range_interv = int(arg)
				ranged = 1

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
	
		#If user defines resolution
		if (resolution_image == 1):
			for line in logfile.readlines():
				expression = re.search(r'[jJ][tT][lL]=(.*?),(.*?)[( HTTP)(\?)]', line)

				#If user defines ip address and user agent
				if (address_ip == 1 and user_agent == 1):
					if ((user in line) and (address in line) and (image_name in line) and expression!=None and expression.group(1) == resolution):
						create_dic (line, resolutio, tile, restil, restildef)
						nb_hits_res += 1

				#If user only defines ip address
				elif (address_ip == 1):
					if ((address in line) and (image_name in line) and expression!=None and expression.group(1) == resolution):
						create_dic (line, resolutio, tile, restil, restildef)
						nb_hits_res += 1

				#If user only defines user agent
				elif (user_agent == 1):
					if ((user in line) and (image_name in line) and expression!=None and expression.group(1) == resolution):
						create_dic (line, resolutio, tile, restil, restildef)
						nb_hits_res += 1


				#In all other cases
				elif (image_name in line and expression!=None and expression.group(1) == resolution):
					create_dic (line, resolutio, tile, restil, restildef)
					nb_hits_res += 1

			#Print the list that shows the tiles and the number of hits
			print_dic (resolutio, tile)

			print "At resolution ",resolution, "there are ",nb_hits_res, "hits"

			#Create the image that shows the repartition of the hits on the tiles
			im = Image.new('L',size)
			draw = ImageDraw.Draw(im)
			for key in tile.keys():
				create_image (draw, new_tile_size, key, nb_tile_width, tile, tile_size, gamma)
			del draw

			#Save the final image
			if imout == 1:
				save_image (im, output, buffer,background)
			


		#In all other cases :
		else:
			for line in logfile.readlines():
				expression = re.search(r'[jJ][tT][lL]=(.*?),(.*?)[( HTTP)(\?)]', line)
				#If user defines ip address and user agent
				if (address_ip == 1 and user_agent == 1):
					if ((user in line) and (address in line) and (image_name in line) and expression!=None):
						create_dic (line, resolutio, tile, restil, restildef)

				#If user only defines ip address
				elif (address_ip == 1 ):
					if ((address in line) and (image_name in line) and expression!=None):
						create_dic (line, resolutio, tile, restil, restildef)

				#If user only defines user agent
				elif (user_agent == 1):
					if ((user in line) and (image_name in line) and expression!=None):
						create_dic (line, resolutio, tile, restil, restildef)
	
				#In all other cases
				elif ((image_name in line) and expression!=None):
					create_dic (line, resolutio, tile, restil, restildef)

			tri_restil = sorted(restil.iteritems(), reverse=True, key=operator.itemgetter(1))			
			#Print the list that shows the resolution, the tiles and the number of hits
			print_list(tri_restil)

		#Plot histogram
		if histo == 1:
			plot (tile)

		#If user wants to plot the "time histogram"
		if hist_time == 1:
			#go back to the begining of the logfile
			logfile.seek(0)
			
			for line in logfile:
				expr = re.search(r'[jJ][tT][lL]=(.*?),(.*?)[( HTTP)(\?)]', line)
				if expr!=None:
					#If user defines both IP address and user agent
					if (address_ip == 1 and user_agent == 1):
						if (address in line and user in line):
							full_date = define_full_date(line)

							ip = line[:line.find(' - - ')]
							browser = line[line.find('" "') + len('" "'):]

							if ([ip, browser]) not in users:
								users.append([ip, browser])
								nbr_user += 1
								full_time.append([(ip, browser), int(mktime(full_date.timetuple()))])
			
							else:
								full_time.append([(ip, browser), int(mktime(full_date.timetuple()))])

					#If user only defines the ip address
					elif (address_ip == 1):
						if (address in line):
							full_date = define_full_date(line)

							ip = line[:line.find(' - - ')]
							browser = line[line.find('" "') + len('" "'):]

							if ([ip, browser]) not in users:
								users.append([ip, browser])
								nbr_user += 1
								full_time.append([(ip, browser), int(mktime(full_date.timetuple()))])
			
							else:
								full_time.append([(ip, browser), int(mktime(full_date.timetuple()))])

					#If user only defines the user_agent
					elif (user_agent == 1):
						if (user in line):
							full_date = define_full_date(line)

							ip = line[:line.find(' - - ')]
							browser = line[line.find('" "') + len('" "'):]

							if ([ip, browser]) not in users:
								users.append([ip, browser])
								nbr_user += 1
								full_time.append([(ip, browser), int(mktime(full_date.timetuple()))])
			
							else:
								full_time.append([(ip, browser), int(mktime(full_date.timetuple()))])

					#In all other cases
					else:
						full_date = define_full_date(line)

						ip = line[:line.find(' - - ')]
						browser = line[line.find('" "') + len('" "'):]
						
						if ([ip, browser]) not in users:
							users.append([ip, browser])
							nbr_user += 1
							full_time.append([(ip, browser), int(mktime(full_date.timetuple()))])
			
						else:
							full_time.append([(ip, browser), int(mktime(full_date.timetuple()))])

			print "Number of user : ", nbr_user

			if full_time != []:
				#Create the final list that will be plot
				create_li = create_list(full_time, dic, ranged, range_interv, interval)

				#Plot the histogram
				plot_time(create_li, bina, ranged, address_ip, user_agent)


			

			

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
