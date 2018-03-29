#!/usr/bin/env python3

import tkinter as tk
import math, os, random, tempfile
from PIL import ImageTk, Image, ExifTags
import configparser

# Config
config = configparser.ConfigParser()
config.read('config.ini')

seconds_to_wait = 60
image_dir = os.path.abspath('images')

if 'Common' in config:
	common = config['Common']
	if 'SecondsToWait' in common:
		seconds_to_wait = int(common['SecondsToWait'])
	if 'Directory' in common:
		image_dir = os.path.expandvars(common['Directory'])

print('Seconds To Wait:', seconds_to_wait)
print('Image Directory:', image_dir)

# Base window config.
window = tk.Tk()
window.geometry('200x200')
window.attributes('-fullscreen', True)
window.configure(background='black')

# Get window geometry.
window.update_idletasks()
window.update()
window_width, window_height = window.geometry().split('+')[0].split('x')
window_width = int(window_width)
window_height = int(window_height)

def generate_image_db():
	fd, path = tempfile.mkstemp()
	with open(path, 'w') as f:
		for root, directories, filenames in os.walk(image_dir):
			for filename in filenames:
				# https://stackoverflow.com/questions/5899497/checking-file-extension
				if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
					f.write(os.path.join(root,filename) + "\n")
		os.close(fd)
	return path

def random_line(file_path):
	with open(file_path, 'r') as f:
		line = next(f)
		for num, aline in enumerate(f):
			if random.randrange(num + 2):
				 continue
			line = aline
		return line.rstrip()

image_db_path = generate_image_db()
print('Image Database:', image_db_path)

def update_image(path):
	try:
		new_img = Image.open(path)
	except:
		return False

	# Rotate image as needed.
	# https://medium.com/@giovanni_cortes/rotate-image-in-django-when-saved-in-a-model-8fd98aac8f2a
	for orientation in ExifTags.TAGS.keys():
		if ExifTags.TAGS[orientation] == 'Orientation':
			break
	exif_method = getattr(new_img, '_getexif', None)
	
	if exif_method is not None and callable(exif_method) and new_img._getexif() is not None:
		exif = dict(new_img._getexif().items())
		if exif is not None and orientation is not None:
			if exif[orientation] == 3:
				print('rotate image 180 degrees')
				new_img = new_img.rotate(180, expand=True)
			elif exif[orientation] == 6:
				print('rotate image 270 degrees')
				new_img = new_img.rotate(270, expand=True)
			elif exif[orientation] == 8:
				print('rotate image 90 degrees')
				new_img = new_img.rotate(90, expand=True)
	
	# Get the image dimensions.
	image_width, image_height = new_img.width, new_img.height

	# Get the ideal size given the aspect ratio of the image.
	ratio = min(window_width / image_width, window_height / image_height)

	# Resize the image to fit.
	width, height = math.floor(image_width * ratio), math.floor(image_height * ratio)
	new_img = new_img.resize((width, height), Image.ANTIALIAS)

	# Determine the best background color.
	# https://zeevgilovitz.com/detecting-dominant-colours-in-python
	pixels = new_img.getcolors(width * height)
	most_frequent_pixel = pixels[0]
	for count, color in pixels:
		if count > most_frequent_pixel[0]:
			most_frequent_pixel = (count, color)
	average_color = most_frequent_pixel[1]
	# Some of the tuples may have 4 values. One for alpha. Convert to 3.
	bg_color = "#{:02x}{:02x}{:02x}".format(
		average_color[0],
		average_color[1],
		average_color[2],
	)

	print('window:', window_width, window_height)
	print('original:', image_width, image_height)
	print('scaled:', width, height)
	print('ratio:', ratio)

	# Update the image.
	tk_img = ImageTk.PhotoImage(new_img)
	label.configure(image=tk_img)
	label.image=tk_img
	window['bg'] = bg_color

# https://stackoverflow.com/questions/5048082/how-to-run-a-function-in-the-background-of-tkinter
def image_update_worker():
	image_path = random_line(image_db_path)
	print('image:', image_path)
	while update_image(image_path) is False:
		image_update_worker()
	label.after(seconds_to_wait * 1000, image_update_worker)

def display_info(e):
	print('info')

label = tk.Label(window, image=None)
label.bind("<Button-1>", display_info)
label.grid(column=0, row=0)
window.columnconfigure(0, weight=1)
window.rowconfigure(0, weight=1)
image_update_worker()
window.mainloop()

