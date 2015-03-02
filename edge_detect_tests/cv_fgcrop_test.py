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
	grayimg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	#grayimg = cv2.Canny(img, 250, 250)
	_, thresh = cv2.threshold(grayimg, 250, 255, cv2.THRESH_BINARY_INV)

	contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	# Only a few rects need to be processed; the whole content is mostly within these rects
	# For example, in case of earrings, two separate large rects might be detected. So processing just the 
	# largest 2 rects should give the bounding box of whole content.
	# Uncomment rectangle() call in below loop to see the rects
	contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]  

	print "Processing countours. Count:", len(contours)
	xmin, ymin, xmax, ymax = img.shape[1], img.shape[0], 0, 0
	for c in contours:
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

	plt.subplot(121), plt.imshow(img, cmap = 'gray')
	plt.title('Original Image'), plt.xticks([]), plt.yticks([])
	plt.subplot(122), plt.imshow(crop, cmap = 'gray')
	plt.title('Threshold Cropped Image'), plt.xticks([]), plt.yticks([])
	destdir = "cropped_threshold/"
	plt.savefig(destdir + imgname)

	plt.show()


if __name__ == "__main__":
	#detect_all
	detect_object('images', 'test.jpg')
	#detect_object('.', 'egg.jpg')
