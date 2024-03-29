import cv2
import numpy as np
import math
from scipy import ndimage
from PIL import Image, ImageEnhance, ImageFont, ImageDraw


filename='N3.png'
img=cv2.imread(filename,cv2.IMREAD_GRAYSCALE)
kernel_test_2 = np.ones((2,2),np.uint8)
print (img.shape)

#---------------------------------making function to exclude half objects-----------------------------------------------

def exclude_halves(contours, image):
    xmax = image.shape[1]-5                                                                 #5 is for tolerance of 5pxls
    ymax = image.shape[0]-5                                                                 #5 is for tolerance of 5pxls
    number_of_deleted_contours = 0;
    for some_contour in range(len(contours)):
        for some_pixel_of_contour in range(len(contours[some_contour - number_of_deleted_contours])):
            if (contours[some_contour - number_of_deleted_contours][some_pixel_of_contour][0][0] >= xmax)\
                    or (contours[some_contour - number_of_deleted_contours][some_pixel_of_contour][0][0] == 0):
                del contours[some_contour - number_of_deleted_contours]
                number_of_deleted_contours = number_of_deleted_contours + 1
                break
            elif (contours[some_contour - number_of_deleted_contours][some_pixel_of_contour][0][1] >= ymax)\
                    or (contours[some_contour - number_of_deleted_contours][some_pixel_of_contour][0][1] == 0):
                del contours[some_contour - number_of_deleted_contours]
                number_of_deleted_contours = number_of_deleted_contours + 1
                break

# -------------------------------- blurring the image-------------------------------------------------------------------

def median_filter(data, filter_size):
    temp = []
    indexer = filter_size // 2
    for i in range(len(data)):

        for j in range(len(data[0])):

            for z in range(filter_size):
                if i + z - indexer < 0 or i + z - indexer > len(data) - 1:
                    for c in range(filter_size):
                        temp.append(0)
                else:
                    if j + z - indexer < 0 or j + indexer > len(data[0]) - 1:
                        temp.append(0)
                    else:
                        for k in range(filter_size):
                            temp.append(data[i + z - indexer][j + k - indexer])

            temp.sort()
            data[i][j] = temp[len(temp) // 2]
            temp = []
    return data


img_blurred = median_filter(img,3)

# -------------------------------making the immage binary---------------------------------------------------------------

img_blurred_clean  = cv2.erode(img_blurred,kernel_test_2,iterations = 2)
img_blurred_clean = cv2.dilate(img_blurred_clean,kernel_test_2,iterations = 2)
img_blurred_clean = cv2.erode(img_blurred_clean,kernel_test_2,iterations = 3)
img_blurred_clean = cv2.dilate(img_blurred_clean,kernel_test_2,iterations = 5)
img_blurred_clean = cv2.erode(img_blurred_clean,kernel_test_2,iterations = 2)
cv2.imwrite('img_blurred_clean.png',img)

img_bw = cv2.threshold(img_blurred_clean, 71 , 255, cv2.THRESH_BINARY)[1]

# -------------------------------- filling in the holles ---------------------------------------------------------------

img_bw_filled_holes = ndimage.binary_fill_holes(img_bw).astype(int)
img_bw_filled_holes = np.asarray([[255 if pxl > 0 else 0 for pxl in pxl_col] for pxl_col in img_bw_filled_holes]).astype(np.uint8)

# -------------------------------- counting objects and their sizes ----------------------------------------------------

some_image = Image.open('img_blurred_clean.png').convert('RGBA')
d = ImageDraw.Draw(some_image)
# d.text((10,10), "Hello World", fill=(255,255,0))
# some_image.save('some_image.png')


from skimage import measure
labels = measure.label(img_bw_filled_holes)
print(labels.max())

contours,hierarchy = cv2.findContours(img_bw_filled_holes, 1, 2)
exclude_halves(contours, img_bw_filled_holes)

contours_poly = [None] * len(contours)
boundRect = [None] * len(contours)

for i, c in enumerate(contours):
    contours_poly[i] = cv2.approxPolyDP(c, 3, True)
    boundRect[i] = cv2.boundingRect(contours_poly[i])


for i in range(len(contours)):
    color = (255,0,0)                                                                                         #red color
    cv2.drawContours(img_blurred_clean, contours_poly, i, color)
    cv2.rectangle(img_blurred_clean,\
                (int(boundRect[i][0]), int(boundRect[i][1])),\
                (int(boundRect[i][0] + boundRect[i][2]),\
                int(boundRect[i][1] + boundRect[i][3])),\
                color,\
                1)

# getting coordinates of the top left corner of the objects
x_coordinates_of_cells = [lis[0] for lis in boundRect]
y_coordinates_of_cells = [lis[1] for lis in boundRect]

i = 1
for cnt in contours:
    area = cv2.contourArea(cnt)
    print('Area of contour #'+str(i) +' is: '+str(area))
    d.text((x_coordinates_of_cells[i-1],y_coordinates_of_cells[i-1]),\
           'Cell #'+str(i-1)+'\nArea:'+str(area),\
           fill=(255, 0, 0))
    some_image.save('some_image.png')
    i = i + 1

#------------------------------------shades of grey---------------------------------------------------------------------

image_of_shades = np.zeros(img.shape)
image_of_shades[0 , 0] = int(img_blurred_clean[0 , 0])
for row in range(1,807):
    image_of_shades[0 , row] = img_blurred_clean[0 , row] + image_of_shades[0 , row - 1]
for col in range(1,565):
    image_of_shades[col , 0] = img_blurred_clean[col , 0] + image_of_shades[col - 1 , 0]
    for row in range(1,807):
        image_of_shades[col , row] = img_blurred_clean[col , row] + image_of_shades[col-1 , row] + image_of_shades[col , row-1] - image_of_shades[col-1 , row-1]

meanGrey = np.zeros(len(contours))
for i in range(len(contours)):
    meanGrey[i]=image_of_shades[(int(boundRect[i][1] + boundRect[i][3]),\
                                int(boundRect[i][0] + boundRect[i][2]))] - image_of_shades[int(boundRect[i][1]),\
                                int(boundRect[i][0] + boundRect[i][2])] - image_of_shades[int(boundRect[i][1] + boundRect[i][3]),\
                                int(boundRect[i][0])] + image_of_shades[int(boundRect[i][1]),\
                                int(boundRect[i][0])]
    meanGrey[i]=meanGrey[i]/((int(boundRect[i][3])*(int(boundRect[i][2]))))
    meanGrey[i]=round(meanGrey[i],2)
    print('Mean shade of grey of bounding box #' + str(i + 1) + ' is : ' + str(meanGrey[i]))
    d.text((x_coordinates_of_cells[i - 1], y_coordinates_of_cells[i - 1]+30), \
           'Grey:' + str(meanGrey[i]), \
           fill=(255, 0, 0))
    some_image.save('final_image.png')
    final_image=cv2.imread('final_image.png',cv2.IMREAD_COLOR)
#-----------------------------------------------------------------------------------------------------------------------

cv2.imshow('img_blurred',img_blurred)
cv2.waitKey(0)
cv2.imshow('img_bw',img_bw)
cv2.waitKey(0)
cv2.imshow('img_bw_filled_holes',img_bw_filled_holes)
cv2.waitKey(0)
cv2.imshow('img_objects_pointed_out',img_blurred_clean)
cv2.waitKey(0)
cv2.imshow('final_image',final_image)
cv2.waitKey(0)
cv2.destroyAllWindows()