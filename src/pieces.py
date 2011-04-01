from copy import deepcopy

# define the DisappearTheBlocks pieces
# spaces are interpreted as empty areas,
# any other character as a solid tile of 
# the piece
pieces = [{'color': (255,0,0),
            'shape': ['|',
                      '|',
                      '|',
                      '|']},
          {'color': (0,255,0),
           'shape': [' __',
                     '_| ']},
          {'color': (0,0,255),
           'shape': ['__ ',
                     ' |_']},
          {'color': (255,255,0),
           'shape': [' |',
                     ' |',
                     '_|']},
          {'color': (255,0,255),
           'shape': ['| ',
                     '| ',
                     '|_']},
          {'color': (0,255,255),
           'shape': ['__',
                     '__']},
          {'color': (64, 100, 135),
           'shape': [' | ',
                     '___']}]

def normalize_pieces(pieces):
    """
    Creates a copy of `pieces`, then normalizes the shape.
    For each piece:
    - Empty tiles (represented by spaces) are normalized as -1.
    - Tiles where the piece is solid are set to the value of
     their index in `pieces`
    """
    p_norm = deepcopy(pieces)
    for idx, piece in enumerate(p_norm):
        piece['shape'] = [[c == ' ' and -1 or idx for c in row]
                          for row in piece['shape']]
    return p_norm

pieces = normalize_pieces(pieces)

class Piece(object):
    """
    Pieces are represented by their lower-left (x,y) coordinate in grid-space
    and their shape (see the defintion of pieces)
    """
    def __init__(self, x, y, index):
        self.x, self.y = (x,y)
        self.index = index
        self.shape = pieces[index]['shape']
        self.width = len(self.shape[0])

    def rotate(self, direction):
        """
        Rotates the piece
        direction = 1 indicates counterclockwise rotation,
        direction = -1 is clockwisex
        """
        # one liner to compute the transpose of a matrix... not
        # efficient for larger sized matrices but for these small ones
        # it's fine
        self.shape = zip(*self.shape[::-1*direction])[::1*direction]
        self.width = len(self.shape[0])

    @property
    def blocks(self):
        blocks = {}
        height = len(self.shape)
        for (i, row) in enumerate(self.shape):
            for (j, value) in enumerate(row):
                if value != -1:
                    blocks[(self.x + j, self.y + height - (i + 1))] = self.index
        return blocks

    def __repr__(self):
        return "(%d, %d): %s" % (self.x, self.y, str(self.shape))
