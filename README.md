IIPAnalyze
==========

IIPAnalyze is a tool for analyzing incoming IIP protocol image requests to the IIPImage server. It can tell you which 
are the most viewed regions of a particular image and display histograms showing tile usage, globally or per 
resolution level. It can also output hotspot image maps showing visually which regions of a particular image are most 
viewed for any given resolution. In addition, it can display histograms of the most viewed tiles or of connection frequency
and time.

IIPAnalyze simply requires a web server log file from Apache, Lighttpd, Nginx, Tomcat or IIS in the widely used 
standard Common Log Format. It parses the contents of the log file and compiles a histogram of all requested tiles.

It is possible to filter by image name, resolution number, IP address and user agent. Basic output is an ordered list of tile 
indexes and their frequency to stdout. If a hotspot map is requested, a greyscale tile map is produced showing which 
regions are the most visited. The brighter the region, the more this region has been viewed. If a histogram is 
requested, a graph plotting tile index vs frequency is produced.

IIPAnalyze is a command line script written in Python and requires the Python Imaging Library in order to generate 
hotspot maps and (optionally) matplotlib if you want histogram plots.

Command Line Options
--------------------

<b>-l, –logfile</b>:
    Web server log file in common log format

<b>-i, –image</b>:
    Full name of the image you want to search e.g. “/images/test.tif”

<b>-r, –resolution</b>:
    Index of the resolution (from 0 and the maximum available resolution of the image)

<b>-a, –address</b>:
    Filter by IP address

<b>-u, --user</b>:
    Filter by user agent

<b>-o, –output</b>:
    Hotspot image map (requires Python’s PIL to be installed) 

<b>-w, –width</b>:
    Width of hotspot image map (must be used with –output option)

<b>-b, –background</b>:
    Apply background of image (contrast reduced) to the hotspot map (must be used with --output option)

<b>-g, –gamma</b>:
    Define a gamma to improve the visibility of low contrasted tiles (must be used with --output option) 

<b>-p, –plot</b>:
    Plot a histogram (requires Python’s matplotlib to be installed)

<b>-t, --time</b>:
    Plot the histogram of connection activitity with respect to time

<b>-n --bins</b>:
    Select the number of bins for the time histogram

<b>-d --range</b>:
Select an interval of time on the time histogram


For example, to generate an image, hits.jpg of width 600px with background showing the distribution of tile hits at 
resolution 5 for image test.tif from the Apache access log use the following command:

<pre>python iipanalyze -l /path/to/access.log -i test.tif -r 5 -b -o hits.jpg -w 600</pre>

------------------------------------------------------------------------------------
Please refer to the project site http://iipimage.sourceforge.net for further details

------------------------------------------------------------------------------------

<pre>(c) 2012 Ruven Pillay <ruven@users.sourceforge.net></pre>


