import cv2
import numpy as np

class canvas(object):
    def  __init__(self, size: tuple):
        piece_size = 30 # size of the piece in pixels        
        width = piece_size * (size[0]+1)
        height = piece_size * (size[1]+1)

        # Initiliaze the canvas
        self.img = np.zeros((height,width,3), np.uint8)
        self.img[:,:, :] = [200, 255, 255]
        
        # Initialize container to save the anchor points for the canvas. 
        self.anch_pos = np.zeros(shape=(size[0], size[1], 2))

        # Define the x and y positions of the anchor points 
        anch_x = np.arange(piece_size/2, width, piece_size)
        anch_y = np.arange(piece_size/2, height, piece_size)
        for _x in range(size[0]):
            for _y in range(size[1]):
                self.anch_pos[_x, _y] = np.asarray([anch_x[_x], anch_y[_y]])
                cv2.circle(self.img, (int(anch_x[_x]),int(anch_y[_y])), 1, (0,0,255), -1) 

        self.piece_size = piece_size

    def visualize(self):
        cv2.namedWindow('Canvas',cv2.WINDOW_NORMAL)
        cv2.imshow("Canvas", self.img)
        cv2.waitKey(0)     

    def addDesign(self, offset, design):
        [num_rows, num_cols, _] = design.shape

        for _x in range(num_rows):
                for _y in range(num_cols):

                    corner1 = np.asarray(self.anch_pos[offset[0]+_x, offset[1]+_y]).astype(int)
                    corner1 = (int(corner1[0]), int(corner1[1]))
                    corner2 = np.asarray([corner1[0] + self.piece_size, corner1[1] + self.piece_size]).astype(int)
                    corner2 = (int(corner2[0]), int(corner2[1]))

                    piece_color = np.asarray(design[_x, _y]).astype(int)
                    piece_color = (int(piece_color[0]), int(piece_color[1]), int(piece_color[2]))
                       
                    cv2.rectangle(self.img, corner1, corner2, piece_color, -1)
                    cv2.rectangle(self.img, corner1, corner2, (0,0,0), 1)
    
    def parseDesign(self, roi, blocks_per_row, blocks_per_col):
        # Once the design has been selected, we need to select a number of anchor points used for extracting the color of each block
        [height, width, _] = roi.shape
        # Get the position increments between each anchor point
        inc_x = width/blocks_per_row
        inc_y = height/blocks_per_col
        # Define the x and y positions of the anchor points 
        anch_x = np.arange(inc_x/2, width, inc_x)
        anch_y = np.arange(inc_y/2, height, inc_y)

        # Initialize container to save the design 
        design = np.zeros(shape=(blocks_per_row, blocks_per_col, 3))
        clone = roi.copy()

        # Go through all the anchor points and get the color of the pixel at its position. 
        # For visualization, add a circle on top.
        for _x in range(blocks_per_row):
            for _y in range(blocks_per_col):
                design[_x, _y] = np.asarray(clone[int(anch_y[_y]), int(anch_x[_x]), :])
                cv2.circle(roi, (int(anch_x[_x]),int(anch_y[_y])), 1, (0,0,255), -1) 

        cv2.namedWindow('Design and anchor points',cv2.WINDOW_NORMAL)
        cv2.imshow("Design and anchor points", roi)
        cv2.waitKey(0)
        
        return design