import cv2
import numpy as np
import json
import random   

# Conversion between the Lego color names and its RGB values as defined in: 
# [http://ryanhowerter.net/colors.php]
colors_dictionary = {'White':[244,244,244],
                    'Bright Yellow':[250,200,10], 
                    'Bright Yellowish Green':[165,202,24],
                    'Sand Green':[112,142,124],
                    'Medium Blue':[62,149,182],
                    'Bright Blue':[30,90,168],
                    'Medium Azur':[104,195,226],
                    'Earth Blue':[25,50,90],
                    'Bright Bluish Green':[6,157,159],
                    'Bright Orange':[214,121,35],
                    'Reddish Brown':[95,49,9],
                    'Medium Nougat':[170,125,85],
                    'Brick Yellow':[204,185,141],
                    'Black':[0,0,0],
                    'Bright Reddish Violet':[144,31,118],
                    'Light Purple':[255,158,205],
                    'Bright Red':[180,0,0],
                    'New Dark Red':[114,0,18],
                    'Dark Stone Grey':[100,100,100],
                    'Medium Stone Grey':[150,150,150],
                    'Medium Lilac':[68,26,145],
                    'Dark Green':[0,133,43],
                    'Dark Azur':[70,155,195],
                    'Earth Green':[0,69,26],
                    'Flame Yellowish Orange':[252,172,0],
                    'Medium Lavender':[160,110,185],
                    'Sand Yellow':[137,125,98],
                    'Bright Purple':[200,80,155],
                    'Cool Yellow':[255,236,108]}

class canvas(object):
    def  __init__(self, size: tuple, valid_pieces):
        # Calculate the size of the canvas based on the number of blocks per column/row
        piece_size = 30 # size of the piece in pixels        
        canvas_width = piece_size * (size[0]+1)
        canvas_height = piece_size * (size[1]+1)

        # Initialize the canvas
        self.img = np.zeros((canvas_height, canvas_width,3), np.uint8)
        self.img[:,:, :] = [200, 255, 255]
        self.clone = self.img.copy()
        
        # Initialize container to save the anchor points for the canvas. 
        self.anch_pos = np.zeros(shape=(size[0], size[1], 2))
        self.anch_state = np.zeros(shape=(size[0], size[1]))

        # Define the x and y positions of the anchor points 
        anch_x = np.arange(piece_size/2, canvas_width, piece_size)
        anch_y = np.arange(piece_size/2, canvas_height, piece_size)
        for _x in range(size[0]):
            for _y in range(size[1]):
                self.anch_pos[_x, _y] = np.asarray([anch_x[_x], anch_y[_y]])
                cv2.circle(self.img, (int(anch_x[_x]),int(anch_y[_y])), 1, (0,0,255), -1) 
        
        # In order to keep track of the amount of each different pieces, we will create a nested dictionary. 
        # The first level covers the different types of pieces and the second level covers the different colors for each piece
        self.pieces_counter  = dict.fromkeys(valid_pieces)
        for e in self.pieces_counter:    
            valid_colors  = dict.fromkeys(valid_pieces[e])      
            for c in valid_colors: 
                valid_colors.update({c:0}) 
            self.pieces_counter.update({e: valid_colors})
        
        # Save global variables for later use
        self.valid_pieces = valid_pieces
        self.size = size
        self.piece_size = piece_size

    def incrementCounter(self, key, color_key):
        """
        Increment the counter for a specific piece and color. This keeps track of how many pieces have been used in the canvas.
                
        Parameters
        ----------
        key: str
            Type of piece
        color_key: str
            Color of the piece
        """         
        value = self.pieces_counter[key][color_key]
        value += 1
        self.pieces_counter[key].update({color_key: value})

    def addPieceToCanvas(self, pos, size, color):
        """
        Draw a new piece in the canvas.
                
        Parameters
        ----------
        pos: tuple
            Anchor position for the top-left corner of the piece.
        size: tuple
            Number of rows and columns for the piece
        color: tuple
            Color of the piece
        """
        # Define the two diagonal corners of the piece
        corner1 = np.asarray(self.anch_pos[pos[0], pos[1]])
        corner1 = (int(corner1[0]), int(corner1[1]))
        corner2 = np.asarray([corner1[0] + (self.piece_size*size[1]), corner1[1] + (self.piece_size*size[0])])
        corner2 = (int(corner2[0]), int(corner2[1]))              
        # Draw piece in the image  
        cv2.rectangle(self.img, corner1, corner2, color, -1)
        cv2.rectangle(self.img, corner1, corner2, (0,0,0), 1)

    def checkIfFits(self, pos, size, max_pos):
        """
        Check if a new piece of the specified size would fit in the canvas.
                
        Parameters
        ----------
        pos: tuple
            Position of the top-left corner of the piece.
        size: tuple
            Number of rows and columns for the piece
        max_pos: tuple
            Maximum position that can be reached by the piece

        Returns
        ----------
        bool
            True if the piece fits, False otherwise
        """
        if (pos[0] + size[1]) <= (max_pos[0]) and (pos[1] + size[0]) <= (max_pos[1]):
            for _r in range(size[0]):
                for _c in range(size[1]):
                    if self.anch_state[pos[0] + _c, pos[1] + _r] == 1:
                        return False
            return True

    def getPieceColor(self, key):
        """
        Get a random color among the possible values.
                
        Parameters
        ----------
        key: str
            Piece type

        Returns
        ----------
        color: tuple
            RGB color code
        color_key: str
            Lego color value
        """              
        color_key = random.choice(list(self.pieces_counter[key].keys()))
        color = colors_dictionary[color_key] 
        color = (color[2], color[1], color[0])
        return color, color_key   

    def addPiece(self, pos, max_pos):
        """
        Find the piece that fits at a given position of the canvas
                
        Parameters
        ----------
        pos: tuple
            Position of the top-left corner of the piece.
        max_pos: tuple
            Maximum position that can be reached by the piece
        
        Returns
        ----------
        bool
            True if the piece was found, False otherwise
        """
        # List of all the possible sizes that can be used in the canvas. 
        # The order is important, whenever a piece fits, the search will stop. 
        possible_keys = ['2x4','2x3','2x2','1x4','1x3','1x2','1x1']
        
        for key in possible_keys: 
            if key in self.pieces_counter.keys():
                size = (int(key[0]), int(key[2]))
                if self.checkIfFits(pos, size, max_pos):
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
                    self.addPiece((_x,_y), self.size)

    def fillSection(self, pos, size):
        """
        Fill all the blank spaces of the section with pieces.
        """
        # Loop through all the anchors in the canvas
        for _x in range(size[0]):
            for _y in range(size[1]):
                # If the anchor is free, find a piece that fits on the available space
                if self.anch_state[pos[0]+_x, pos[1]+_y] == 0:
                    self.addPiece((pos[0]+_x, pos[1]+_y), (pos[0]+size[0], pos[1]+size[1]))

    def save(self):
        """
        Save the data regarding the canvas: Number of pieces of each case and price.
        """
        with open('summary.json', 'w') as outfile:
            json.dump(self.pieces_counter, outfile, indent=4)
        
        total_price = 0
        for piece_key in self.pieces_counter.keys():
            for color in self.valid_pieces[piece_key]:
                num_of_pieces = self.pieces_counter[piece_key][color]
                piece_price = self.valid_pieces[piece_key][color]
                subtotal = num_of_pieces * piece_price
                total_price +=  subtotal
        print('INFO: The total price for the mosaic is: ' + str(np.round(total_price)) + ' DKK')

        result= cv2.imwrite(r'./mosaic.png', self.img)
        if result==True:
            print('INFO: File saved successfully at: ' + './mosaic.png')
        else:
            print('ERROR: Couldn\'t save canvas image')
                        
    def visualize(self):
        """
        Visualize the current state of the canvas
        """
        cv2.namedWindow('Canvas',cv2.WINDOW_NORMAL)
        cv2.imshow("Canvas", self.img)
        cv2.waitKey(0)           

    def parseDesign(self, image, size):
        """
        Given and image with a pixel art design and its size (number of blocks per row and column).
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
        cv2.imshow('Design and anchor points', image)
        
        return design

    def addDesign(self, pos, design, keep_white):
        """
        Add a pixel art design to the canvas
                
        Parameters
        ----------
        pos: tuple
            Position of the top-left corner of the design
        design: numpy.ndarray
            Matrix with the colors for each block of the design
        keep_white: bool
            Define if the white bricks count as part of the design or only the background.
        """
        # Get the size of the design
        size = design.shape

        # Loop through all the blocks of the design
        for _x in range(size[0]):
                for _y in range(size[1]):
                    piece_color = np.asarray(design[_x, _y])
                    piece_color = (int(piece_color[2]), int(piece_color[1]), int(piece_color[0]))                      
                    if keep_white is False and self.isWhite(piece_color):
                        continue
                    else:
                        piece_key = '1x1'
                        piece_color, color_key = self.getClosestColor(piece_key, piece_color)
                        piece_color = (int(piece_color[2]), int(piece_color[1]), int(piece_color[0]))   
                        self.addPieceToCanvas((pos[0]+_x, pos[1]+_y), (1,1), piece_color)
                        # Update the state of the anchors used by the design 
                        self.anch_state[pos[0]+_x, pos[1]+_y] = 1
                        self.incrementCounter(piece_key, color_key)
        # In case that the white blocks are not considered, there may be empty spots. That's why we fill the design space.
        self.fillSection(pos, size)

    def getClosestColor(self, piece_key, color):
        """
        Since there aren't direct matches between all the RGB colors and the lego pieces. 
        We need to get the closest lego color for a given RGB value.
                
        Parameters
        ----------
        piece_key: str
            Piece type
        color: tuple
            RGB color code

        Returns
        ----------
        color_match: tuple
            RGB color code
        color_match_key: str
            Lego color value
        """ 
        d_min = np.iinfo(np.uint64).max
        color_match = None
        color_match_key = None
        for color_key in self.pieces_counter[piece_key].keys():
            color_db = colors_dictionary[color_key]
            d =   np.sqrt(((color[0]-color_db[0]))**2  + ((color[1]-color_db[1]))**2 + ((color[2]-color_db[2]))**2)
            if d < d_min:
                d_min = d
                color_match = color_db
                color_match_key = color_key
        return color_match, color_match_key

    def isWhite(self, color):
        """
        Check if a color is white.
                
        Parameters
        ----------
        color: tuple
            Color to be checked.

        Returns
        ----------
        bool
            True if color is white, False otherwise
        """
        for c in color:
            if c < 250:
                return False
        return True

    def visualizeAnchorsState(self):
        """
        Visualize the state of the anchors, blue if used, green if not.        
        """
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
        cv2.imshow('Anchors state', temp)
        cv2.waitKey(0)

    def visualizeColorPalette(self):
        """
        Visualize the available colors for each available piece.              
        """

        valid_bricks = self.pieces_counter.keys()
        valid_colors = colors_dictionary.keys()

        # Define the position of the anchor points for each rectangle (one per possible color)
        margin_x = 80
        x_init = margin_x/2
        x_end = x_init + margin_x * len(valid_bricks)
        anchors_x = np.arange(x_init, x_end, margin_x)

        margin_y = margin_x/2
        y_init = margin_y
        y_end = y_init + margin_y*len(valid_colors)
        anchors_y = np.arange(y_init, y_end, margin_y)

        height = int(margin_y * len(valid_colors) + y_init)
        width =  int(margin_x * len(valid_bricks) + x_init) + 400

        # Initialize the image
        img = np.zeros((height, width,3), np.uint8)
        img[:,:, :] = [250, 250, 255]
        
        # Add the color names
        x_count = 0
        for color_key in valid_colors:
            text_pos = int(anchors_x[len(anchors_x)-1]+margin_x), int(anchors_y[x_count]+margin_y*0.6)
            cv2.putText(img, color_key, text_pos, cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 0, 0), 2) 
            x_count += 1
 
        # Add rectangles filled with the correspondent color
        x_count = 0
        y_count = 0
        for piece_key in valid_bricks:       
            text_pos = int(anchors_x[x_count]+margin_x*0.1), int(anchors_y[y_count]-margin_y*0.2)
            cv2.putText(img, piece_key, text_pos, cv2.FONT_HERSHEY_SIMPLEX,1, (0, 0, 0, 0), 2) 

            for color_key in valid_colors:
                if color_key in self.pieces_counter[piece_key].keys(): 
                    color = colors_dictionary[color_key]
                    color = (color[2], color[1], color[0])
                    
                    corner1 = (int(anchors_x[x_count]), int(anchors_y[y_count]))
                    corner2 = (int(corner1[0]+margin_x*0.8), int(corner1[1]+margin_y*0.8))

                    cv2.rectangle(img, corner1, corner2, color, -1)
                    cv2.rectangle(img, corner1, corner2, (0,0,0), 1)

                y_count += 1
                
            x_count +=  1
            y_count = 0

        cv2.namedWindow('Color Palette',cv2.WINDOW_NORMAL)
        cv2.imshow('Color Palette', img)
        cv2.waitKey(0)
        
        




