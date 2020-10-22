import json

import cv2
import numpy as np

from utils import canvas

def selectCroppingRefPoints(event, x, y, flags, param):
    # grab references to the global variables
    global refPt, cropPt

    # Record the mouse position when the left mouse button is clicked
    if event == cv2.EVENT_LBUTTONDOWN:
        # Add mouse position to the reference points
        if refPt is None:
            refPt = [(x, y)]
        else:
            refPt.append((x, y))

    # Record the mouse position when the left mouse button is released
    elif event == cv2.EVENT_LBUTTONUP:   
        # Add mouse position to the reference points
        refPt.append((x, y))
        # Get bounding box given the current reference points, the BB is defined by the smalles 
        # box that encapsulates all the reference points
        reference_points = np.asarray(refPt)
        cropPt = [(np.min(reference_points[:,0]), np.min(reference_points[:,1]))]
        cropPt.append((np.max(reference_points[:,0]), np.max(reference_points[:,1])))
        # Draw a rectangle in yellow showing the last selected area and a rectangle in green 
        # showing the area that will be cropped
        cv2.rectangle(image, cropPt[0], cropPt[1], (0, 255, 0), 2)
        cv2.rectangle(image, refPt[len(refPt)-1], refPt[len(refPt)-2], (0, 255, 255), 2)
        # Show the current status of the crop design
        cv2.imshow("Crop design", image)

# Global containers for the reference points for the cropping task.
# ToDo: Find out if its is possible to avoid the use of global variables in selectCroppingRefPoints()
refPt = []
cropPt = []
def cropImage(image):
    # grab references to the global variables
    global refPt, cropPt

    clone = image.copy()
    cv2.namedWindow("Crop design", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Crop design", selectCroppingRefPoints)
    # keep looping until the 'q' key is pressed
    while True:
        # display the image and wait for a keypress
        cv2.imshow("Crop design", image)
        key = cv2.waitKey(1) & 0xFF
        # if the 'r' key is pressed, reset the cropping region
        if key == ord("r"):
            return None

        elif key == ord("s"):
            # if there are two reference points, then crop the region of interest
            # from teh image and display it
            if len(cropPt) == 2:
                roi = clone[cropPt[0][1]:cropPt[1][1], cropPt[0][0]:cropPt[1][0]]
                return roi
            break
        # if the 'c' key is pressed, break from the loop
        elif key == ord("c"):
            break

# Load the configuration file:
with open('./conf.json', 'r') as myfile:
    # load data
    data = myfile.read()
    loaded_json = json.loads(data)

# Initialize the canvas that we will use for our design
canvas_data = loaded_json['canvas_config']
mosaic = canvas((canvas_data['blocks_per_row'], canvas_data['blocks_per_col']), canvas_data["valid_pieces"])
mosaic.visualizeColorPalette()


# Get the data regarding the pixel-art designs that we want to add to the canvas
designs_data = loaded_json['designs']
for element in designs_data:
    # Load the data regarding the current design:
    size = (designs_data[element]['size'][0], designs_data[element]['size'][1])
    pos_x = designs_data[element]['position'][0]
    pos_y = designs_data[element]['position'][1]

    # When the reset button is pressed, cropImage will return None and we load the image again. 
    # ToDo: originally I wanted to do the reset process inside the cropping function, however, it didn't work. 
    # The image was reset but then I was unable to draw the reference rectangles. It would be nice to do it inside 
    # the function and avoid the wjile loop
    roi = None
    while roi is None:
        image = cv2.imread(designs_data[element]['path'])
        # get the region of interest
        roi = cropImage(image)
        # Reset the containers
        refPt.clear()
        cropPt.clear()
    # Extract the design from the roi
    design = mosaic.parseDesign(roi, size)
    # Add design to canvas and visualize the result
    mosaic.addDesign((pos_x,pos_y), design)
    mosaic.visualize()

mosaic.fill()
mosaic.visualize()
mosaic.save()
# close all open windows
cv2.destroyAllWindows()
