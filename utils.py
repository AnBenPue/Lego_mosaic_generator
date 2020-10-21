import cv2
import numpy as np
import json
import random   

class canvas(object):
    def  __init__(self, size: tuple, valid_pieces):
        piece_size = 30 # size of the piece in pixels        
        self.width = piece_size * (size[0]+1)
        self.height = piece_size * (size[1]+1)

        # Initiliaze the canvas
        self.img = np.zeros((self.height,self.width,3), np.uint8)
        self.img[:,:, :] = [200, 255, 255]
        self.clone = self.img.copy()
        
        # Initialize container to save the anchor points for the canvas. 
        self.anch_pos = np.zeros(shape=(size[0], size[1], 2))
        self.anch_state = np.zeros(shape=(size[0], size[1]))

        # Define the x and y positions of the anchor points 
        anch_x = np.arange(piece_size/2, self.width, piece_size)
        anch_y = np.arange(piece_size/2, self.height, piece_size)
        for _x in range(size[0]):
            for _y in range(size[1]):
                self.anch_pos[_x, _y] = np.asarray([anch_x[_x], anch_y[_y]])
                cv2.circle(self.img, (int(anch_x[_x]),int(anch_y[_y])), 1, (0,0,255), -1) 
        
        # In order to keep track of the amount of each different pieces, we will create a nested dictionary. 
        # The first level covers the different types of pieces and the second level covers the different colors for each piece
        self.pieces_counter  = dict.fromkeys(valid_pieces)
        for e in self.pieces_counter:
            valid_colors  = dict.fromkeys(valid_pieces[e]['colors'])
            for c in valid_colors:
                valid_colors.update({c: 0}) 
            self.pieces_counter.update({e: valid_colors}) 
        
        # Save global variables for later use
        self.valid_pieces = valid_pieces
        self.size = size
        self.piece_size = piece_size

    def incrementCounter(self, key, color_key):
        """
        Increment the counter for a specific piece and color. 
                
        Parameters
        ----------
        key: str
            Type of piece
        color_key: str
            Color of the piece
        """ 
        value = self.pieces_counter[key][color_key]
        value = value + 1
        self.pieces_counter[key].update({color_key: value})

    def addPieceToCanvas(self, pos, size, color):
        """
        Draw a new piece in the canvas.
                
        Parameters
        ----------
        pos: tuple
            Position of the top-left corner of the piece.
        size: tuple
            Number of rows and columns for the piece
        color: tuple
            Color of the piece
        """
        corner1 = np.asarray(self.anch_pos[pos[0], pos[1]])
        corner1 = (int(corner1[0]), int(corner1[1]))
        corner2 = np.asarray([corner1[0] + (self.piece_size*size[1]), corner1[1] + (self.piece_size*size[0])])
        corner2 = (int(corner2[0]), int(corner2[1]))              
            
        cv2.rectangle(self.img, corner1, corner2, color, -1)
        cv2.rectangle(self.img, corner1, corner2, (0,0,0), 1)

    def checkIfFits(self, pos, size):
        """
        Check if a new piece of the specified size would fit in the canvas.
                
        Parameters
        ----------
        pos: tuple
            Position of the top-left corner of the piece.
        size: tuple
            Number of rows and columns for the piece

        Returns
        ----------
        bool
            True if the piece fits, False otherwise
        """
        if (pos[0] + size[1]) <= (self.size[0]) and (pos[1] + size[0]) <= (self.size[1]):
            for _r in range(size[0]):
                for _c in range(size[1]):
                    if self.anch_state[pos[0] + _c, pos[1] + _r] == 1:
                        return False
            return True

    def getPieceColor(self, key):
        valid_colors = self.valid_pieces[key]['colors']
        color_key = random.choice(list(valid_colors.keys()))     
        selected_color = valid_colors[color_key]
        return (selected_color[0],selected_color[1],selected_color[2]), color_key   

    def addPiece(self, pos):
        """
        Find the piece that fits at a given position of the canvas
                
        Parameters
        ----------
        pos: tuple
            Position of the top-left corner of the piece.
        """
        # List of all the possible sizes that can be used in the canvas. 
        # The order is important, whenever a piece fits, the search will stop. 
        possible_keys = ['2x4','2x3','2x2','1x4','1x3','1x2','1x1']
        
        for key in possible_keys: 
            if key in self.pieces_counter.keys():             

                size = (int(key[0]), int(key[2]))
                if self.checkIfFits(pos, size):
                    # Update the anchors state: 1 means that the anchor is being used
                    self.anch_state[pos[0]:(pos[0]+size[1]), pos[1]:(pos[1]+size[0])] = 1 
                    # Get the piece color
                    piece_color, color_key = self.getPieceColor(key) 
                    # Add the piece to the visualization of the canvas and update counter       
                    self.addPieceToCanvas(pos, size, piece_color) 
                    self.incrementCounter(key, color_key) 
                    return True
        return False
     
  
    def fill(self):
        """
        Fill all the blank spaces of the canvas with pieces.
        """
        # Loop through all the anchors in the canvas
        for _x in range(self.size[0]):
            for _y in range(self.size[1]):
                # If the anchor is free, find a piece that fits on the available space
                if self.anch_state[_x,_y] == 0:
                    self.addPiece((_x,_y))

    
    def save(self):
        """
        Save the data regarding the canvas: Number of pices of each case
        """
        with open('summary.json', 'w') as outfile:
            json.dump(self.pieces_counter, outfile, indent=4)
                        
    def visualize(self):
        """
        Visualize the current state of the canvas
        """
        cv2.namedWindow('Canvas',cv2.WINDOW_NORMAL)
        cv2.imshow("Canvas", self.img)
        cv2.waitKey(0)           

    def parseDesign(self, image, size):
        """
        Given and image with a pixel art design and its size (number of blocks per roww and column).
         Parse the design in order to convert it to bricks.
                
        Parameters
        ----------
        image: numpy.ndarray
            image with the design
        design: numpy.ndarray
            Matrix with the colors for each block of the design

        Returns
        ----------
        design: numpy.ndarray
            Matrix with the colors for each block of the design
        """
        # Once the design has been selected, we need to select a number of anchor points used for extracting the color of each block
        [height, width, _] = image.shape
        # Get the position increments between each anchor point
        inc_x = width/size[0]
        inc_y = height/size[1]
        # Define the x and y positions of the anchor points 
        anch_x = np.arange(inc_x/2, width, inc_x)
        anch_y = np.arange(inc_y/2, height, inc_y)

        # Initialize container to save the design 
        design = np.zeros(shape=(size[0], size[1], 3))
        clone = image.copy()

        # Go through all the anchor points and get the color of the pixel at its position. 
        # For visualization, add a circle on top.
        for _x in range(size[0]):
            for _y in range(size[1]):
                design[_x, _y] = np.asarray(clone[int(anch_y[_y]), int(anch_x[_x]), :])
                cv2.circle(image, (int(anch_x[_x]),int(anch_y[_y])), 1, (0,0,255), -1) 
        # Visualize the original image with the anchor points on top. Each anchor should align with the center of the block.
        cv2.namedWindow('Design and anchor points',cv2.WINDOW_NORMAL)
        cv2.imshow("Design and anchor points", image)
        cv2.waitKey(0)
        
        return design

    def addDesign(self, pos, design):
        """
        Add a pixel art design to the canvas
                
        Parameters
        ----------
        pos: tuple
            Position of the top-left corner of the design
        design: numpy.ndarray
            Matrix with the colors for each block of the design
        """
        # Get the size of the design
        size = design.shape

        # Loop through all the blocks of the design
        for _x in range(size[0]):
                for _y in range(size[1]):
                    piece_color = np.asarray(design[_x, _y])
                    piece_color = (int(piece_color[0]), int(piece_color[1]), int(piece_color[2]))  
                    self.addPieceToCanvas((pos[0]+_x, pos[1]+_y), (1,1), piece_color)
        # Update the state of the anchors used by the design 
        self.anch_state[pos[0]:(pos[0]+size[0]), pos[1]:(pos[1]+size[1])] = 1

    def visualizeAnchorsState(self):
        temp = self.clone.copy()

        for _x in range(self.size[0]):
            for _y in range(self.size[1]):

                pos = (int(self.anch_pos[_x, _y][0]), int(self.anch_pos[_x, _y][1]))
                if self.anch_state[_x, _y] == 0:
                    color = (255,0,0)
                else:
                    color = (0,255,0)
                cv2.circle(temp, pos, 4, color, -1) 
        
        cv2.namedWindow('Anchors state',cv2.WINDOW_NORMAL)
        cv2.imshow("Anchors state", temp)
        cv2.waitKey(0)