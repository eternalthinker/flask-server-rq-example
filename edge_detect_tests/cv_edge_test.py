import os
import cv2
import numpy as np
from matplotlib import pyplot as plt


def detect_all():
	srcdir = "images"
	i = 0
	for f in os.listdir(srcdir):
		if f.endswith(".jpg"):
			i += 1
			print "Processing:", i, f
			detect_object(srcdir, f)
	print "END"


def detect_object(srcdir, imgname):
	imgpath = srcdir + os.sep + imgname
	img = cv2.imread(imgpath, 1)
	edges = cv2.Canny(img, 250, 250)

	cnts, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	# Process all contours for accurate bounding of object. The individual bounding rects are mostly scattered all over the
	# actual content, bounding only smaller parts
	# Uncomment rectangle() call in below loop to see the rects
	cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

	# Find extreme coordinates bounding all detected rects
	print "Processing countours. Count:", len(cnts)
	xmin, ymin, xmax, ymax = img.shape[1], img.shape[0], 0, 0
	for c in cnts:
		x, y, w, h = cv2.boundingRect(c)
		#cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 1)  # Draw all processed contour rects
		if x < xmin:
			xmin = x
		if x + w > xmax:
			xmax = x + w
		if y < ymin:
			ymin = y
		if y + h > ymax:
			ymax = y + h

	x, y, w, h = xmin, ymin, xmax - xmin, ymax - ymin
	crop = img[y:y+h, x:x+w]
	cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 1)

	plt.subplot(121),plt.imshow(img, cmap = 'gray')
	plt.title('Original Image'), plt.xticks([]), plt.yticks([])
	plt.subplot(122),plt.imshow(crop, cmap = 'gray')
	plt.title('Edge Cropped Image'), plt.xticks([]), plt.yticks([])
	destdir = "cropped_edges/"
	plt.savefig(destdir + imgname)

	plt.show()


if __name__ == "__main__":
	#detect_all
	detect_object('images', 'test.jpg')
	#detect_object('.', 'egg.jpg')
