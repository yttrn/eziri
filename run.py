import os
import sys
import numpy as np
import math
import matplotlib.pyplot as plt
from scipy.ndimage import distance_transform_edt, label
from skimage import color, filters, io, exposure, morphology, transform, measure, restoration, feature, segmentation

##quick display function
def display(*images):
	square = len(images)
	side = math.ceil(math.sqrt(square))

	try:
		fig, axes = plt.subplots(side, side, figsize=(8, 8))
		for r, ax in enumerate(axes.flat):
			if r < square:
				ax.imshow(images[r], aspect='auto')
			ax.axis('off')
	except:
		fig, ax = plt.subplots(side,side,figsize=(8,8))
		ax.imshow(images[0], aspect='auto')
		ax.axis('off')

	plt.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0.02, hspace=0.02)
	plt.show()

def preprocess(grayscale_image):

	#blur preserving edges
	blurred_image = restoration.denoise_bilateral(grayscale_image,win_size=7,sigma_color=3,sigma_spatial=25)
	#adaptive histogram equalization
	adapteq = exposure.equalize_adapthist(blurred_image, kernel_size=55, clip_limit=0.3)
	#unsharp mask
	masked_image = filters.unsharp_mask(adapteq, radius=15, amount = 2)
	#local thresholding
	block_size = 55
	threshold = filters.threshold_local(masked_image, block_size, offset=0.01)
	binary_image = masked_image > threshold
	#opening
	opened_image = morphology.opening(binary_image, footprint=morphology.disk(4))

	"""uncomment to see what the intermediate images look like,
	this is helpful for tweaking and debugging"""
	#display(blurred_image,adapteq,masked_image,opened_image)

	return opened_image

def find_centers(binary_image):
	
	distance_transform = distance_transform_edt(binary_image)
	distance_transform = restoration.denoise_bilateral(distance_transform,win_size=5,sigma_color=5,sigma_spatial=15)

	#estimate blob centers by local maxima
	max_coords = feature.peak_local_max(
		distance_transform, footprint=np.ones((11, 11)), labels=binary_image,
		exclude_border=False, min_distance = 17
		)
	local_maxima = np.zeros(distance_transform.shape, dtype=bool)
	local_maxima[tuple(max_coords.T)] = True
	centers = measure.label(local_maxima)
	centers = segmentation.expand_labels(centers, distance = 5)
	
	"""like above, the next 3 lines plot and shows all of the crystal centers it detects.
	uncomment for debugging"""
	#plt.imshow(raw_image)
	#plt.scatter(max_coords[:, 1], max_coords[:, 0], s=1, c='r')
	#plt.show()

	return centers
	
def find_edges(binary_image):

	closed_image = morphology.closing(binary_image, footprint=morphology.disk(2))
	#turn estimations into labels
	labels = measure.label(closed_image, 0, connectivity = 2)
	labels = segmentation.expand_labels(labels, distance = 3)
	mask = labels > 0
	#find borders from labels, then enhance
	borders = segmentation.find_boundaries(labels, connectivity=2, mode='inner', background = 0)
	borders = morphology.dilation(borders, footprint=morphology.disk(2))

	return borders, mask

def measure_crystals(binary_image, watershed_labels, image_width, image_height):

	#scale watershed labels acording to real-life image dimensions
	transform.resize(watershed_labels, (image_width, image_height)).shape

	#find crystal characteristics
	crystals = []
	for crystal in measure.regionprops(watershed_labels):
		crystal = {
			"area": crystal.area,
			"perimeter": crystal.perimeter,
			"eccentricity": crystal.eccentricity
			}
		crystals.append(crystal)
	
	return crystals

if __name__ == '__main__':
#error handling
	try:
		filename = os.getcwd() +'/'+ sys.argv[1]
		raw_image = io.imread(filename, as_gray=True)
	except:
		try:
			print(f'Could not load file: {sys.argv[1]}')
		except:
			print('Enter file to analyze')
		sys.exit(2)

	try:
		width_nm = float(sys.argv[2])
		height_nm = float(sys.argv[3])
	except:
		try:
			width_nm + height_nm
			print('Invalid image dimensions')
		except:
			print('Enter image dimensions')
		sys.exit(1)

#create black mask
	threshold = 12/255
	black_mask = raw_image < threshold

#preprocess to enhance crystal definition
	print('preprocessing image...')
	binary_image = preprocess(raw_image)
	binary_image[black_mask] = 0

#identify crystal centers for watershed seedpoint
	print('finding crystal centers...')
	crystal_centers = find_centers(binary_image)

#identify crystal edges for watershed flood boundaries
	print('finding crystal edges...')
	crystal_borders, mask = find_edges(binary_image)

#run watershed algorithm
	print('running watershed algorithm...')
	ws_labels = segmentation.watershed(crystal_borders, crystal_centers, mask=mask)

#detect ice crystals from watershed image
	print('measuring crystals...')
	crystal_properties = measure_crystals(binary_image, ws_labels, width_nm, height_nm)

#write all collected stats to a csv file
	with open(filename+'-measured.csv','a') as out:
		out.write('area,perimeter,eccentricity\n')
		for crystal in crystal_properties:
			out.write(f'{crystal["area"]},{crystal["perimeter"]},{crystal["eccentricity"]}\n')

"""this shows, as an image, the final crystals it detects and what they look like.
	left is the output, right is the original image"""
	#ws_img = color.label2rgb(ws_labels,image=raw_image, kind='avg', bg_label=0, colors=plt.cm.tab20.colors)
	#ws_img = color.rgb2gray(ws_img)
	#display(ws_img,raw_image)
