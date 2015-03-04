#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Converts apptaster files to html5."""

from __future__ import with_statement
from contextlib import closing

import codecs
import logging
import os.path
import sys
import xml.etree.ElementTree as ET
import zipfile


DIRNAME = "-html"


def process_screen(zip_main, xml_screen, basedir, home_screen_id,
		valid_screens):
	"""f(ZipInfo, Element, string, string, [string]) -> None

	Pass the zip to extract from the resources and the xml screen node you want
	to extract. The function will create an HTML file and extract the
	associated image, creating a hyperlinked imagemap for it.

	Pass the basedir where all files are to be created and the identifier of
	the home screen. This will be copied to be the index.html file.

	The home_screen_id specifies what is the home screen identifier, should a
	link be made to it. The valid_screens contains a list of strings with the
	existing screen identifiers, which is used to filter strange zeroth links
	in the xml pMultipleLinks/multipleLink section.
	"""
	screen_id = xml_screen.get("id")
	screen_name = xml_screen.find("name").text
	screen_file = xml_screen.find("portraitFileName").text
	html_file = os.path.join(basedir, "%s.html" % screen_id)
	logging.info("Creating %r", html_file)
	with closing(codecs.open(html_file, "wb", "utf-8")) as o:
		o.write("<html><head><meta http-equiv=")
		o.write('"Content-Type" content="text/html; charset=UTF-8"><title>')
		o.write(screen_name)
		o.write("</title></head><body><h1>")
		o.write(screen_name)
		o.write("</h1><img src='%s' usemap='#m'><map name='m'>" % screen_file)
        img_maps = []
		for link in (xml_screen.findall("portraitLinks/link") +
				xml_screen.findall("pMultipleLinks/multipleLink/link") +
				xml_screen.findall("timerLink/link")):
			target_id = link.get("targetId")
			link_type = link.get("type")
			if link_type not in ["1", "3", '4']:
				print "Unknown link type", link_type
				continue
			if "3" == link_type:
				href = "javascript:history.back()"
			elif link_type in ['1', '']:
				href = "%s.html" % target_id
				if target_id not in valid_screens:
					continue
			elif link_type in ['4']:
				# see https://github.com/gradha/apptaster-to-html/pull/2#issuecomment-75604197
				duration = int(float(link.get('timer')) * 1000)
				href = "%s.html" % target_id
				o.write(('<script>setTimeout(function() '
						 '  { document.location = "%s"} ' 
						 ', %s);</script>' % (href, duration)))
			x = int(float(link.get("x")))
			y = int(float(link.get("y")))
			w = int(float(link.get("w")))
			h = int(float(link.get("h")))
			# make sure later links are above previous links
			img_maps.append('<area shape="rect" coords="%d,%d,%d,%d" href="%s">' % (
				x - w / 2, y - h / 2, x + w / 2, y + h / 2, href))
		# reverse to match how apptaster does that. if not reversed
		# links that are overlayed by previous links might not work. 
		for map in reversed(img_maps):
			o.write(map)
		o.write("</body></html>")

	img_file = os.path.join(basedir, screen_file)
	with closing(open(img_file, "wb")) as o:
		o.write(zip_main.read(screen_file))

	if home_screen_id == screen_id:
		with closing(open(html_file, "rb")) as input_file:
			with closing(open(os.path.join(basedir, "index.html"), "wb")) as o:
				o.write(input_file.read())


def process_apptaster(apptaster_filename):
	"""f(string) -> None

	Opens an apptaster zipfile and starts to extract the files"
	"""
	try:
		zip_main = zipfile.ZipFile(apptaster_filename)
	except:
		logging.error("Couldn't open zip file %r", apptaster_filename)
		return

	basedir, filename = os.path.split(apptaster_filename)
	basename = os.path.splitext(filename)[0] + DIRNAME
	basedir = os.path.join(basedir, basename)
	try: os.makedirs(basedir)
	except: pass

	root = ET.fromstring(zip_main.read("project"))
	home_screen_id = root.find("screens").get("startScreenId")
	valid_screens = [x.get("id") for x in root.findall("screens/screen")]
	for screen in root.findall("screens/screen"):
		process_screen(zip_main, screen, basedir, home_screen_id, valid_screens)


def main():
	"""f() -> None

	Main entry point of the application.
	"""
	args = [x for x in sys.argv[1:] if x.lower().find(".apptaster") > 0]
	if not args:
		print "Usage: %s files" % sys.argv[0]
		return

	errors = 0
	for filename in args:
		try:
			process_apptaster(filename)
		except:
			logging.exception("Error processing %r", filename)
			errors = errors + 1

	return errors


if "__main__" == __name__:
	logging.basicConfig(level = logging.INFO)
	main()

# vim:tabstop=4 shiftwidth=4
