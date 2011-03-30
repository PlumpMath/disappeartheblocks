import pyglet
from random import randint
from copy import deepcopy
from functools import wraps

GRID_WIDTH = 10
GRID_HEIGHT = 22
GRID_HIDDEN_ROWS = 2

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

    def rotate(self, direction):
        """
        Rotates the piece
        direction = 1 indicates counterclockwise rotation,
        direction = -1 is clockwisex
        """
        # one liner to compute the transpose of a matrix... not
        # efficient for larger sized matrices but for these small ones
        # it's fine
        self.shape = zip(*self.shape[::-1*direction])

    def get_coords(self):
        coords = []
        height = len(self.shape)
        for (i, row) in enumerate(self.shape):
            for (j, value) in enumerate(row):
                if value != -1:
                    coords.append((self.x + j, self.y + height - 1 - i))
        return coords

    def __repr__(self):
        return "(%d, %d): %s" % (self.x, self.y, str(self.shape))

def random_piece():
    index = randint(0, len(pieces) - 1)
    shape = pieces[index]['shape']
    x = GRID_WIDTH//2 - len(shape[0])//2
    y = GRID_HEIGHT - len(shape)
    return Piece(x, y, index)

def yield_i(i):
    while 1:
        yield i

def capture_delta(fn):
    """
    Defines a decorator for use in the DisappearTheBlocks class
    The game state is saved before calling the wrapped function,
    and compared with the state after calling the wrapped function.
    The differences are added to the delta list
    """
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        current_coords = set(self.current_piece.get_coords())
        ret = fn(self, *args, **kwargs)
        new_coords = set(self.current_piece.get_coords())
        now_empty = current_coords.difference(new_coords)
        new_blocks = new_coords.difference(current_coords)
        self.delta.extend(zip(now_empty, yield_i(-1)))
        self.delta.extend(zip(new_blocks, yield_i(self.current_piece.index)))
        return ret
    return wrapper


class DisappearTheBlocks(object):
    """
    Implements a game of te... DisappearTheBlocks
    """
    delta = []

    def __init__(self):
        self.grid = []

    def start(self):
        self.current_piece = random_piece()
        self.delta.extend(zip(self.current_piece.get_coords(),
                              yield_i(self.current_piece.index)))
        pyglet.clock.schedule_interval(self.tick, 0.5)
        pyglet.clock.schedule_interval(self.rotate_piece, 1)
    
    @capture_delta
    def tick(self, dt):
        self.current_piece.y -= 1

    @capture_delta
    def rotate_piece(self, dt):
        self.current_piece.rotate(1)

    def pop_delta(self):
        d = self.delta
        self.delta = []
        return d

    def churn_piece(self):
        # merge current piece with grid
        # set current piece to piece in queue
        # create a new queued piece
        pass

class DisappearTheBlocksView(object):
    """
    """
    def __init__(self, x, y, block_img):
        self.batch = pyglet.graphics.Batch()

        # Helper function for initializing the sprites
        def make_sprite(j, i):
            s = pyglet.sprite.Sprite(block_img,
                                     batch=self.batch,
                                     x=x + j*block_img.width,
                                     y=y + i*block_img.width)
            s.visible = False
            return s

        self.grid = [[make_sprite(j,i)
                      for j in range(GRID_WIDTH)]
                     for i in range(GRID_HEIGHT)]

    def update(self, delta):
        for ((x, y), index) in delta:
            sprite = self.grid[y][x]
            if index == -1:
                sprite.visible = False
            else:
                sprite.visible = True
                sprite.color = pieces[index]['color']

    def draw(self):
        self.batch.draw()

if __name__ == '__main__':
    window = pyglet.window.Window(800, 600)
    img = pyglet.resource.image('block.png')
    game = DisappearTheBlocks()
    view = DisappearTheBlocksView(400-125, 20, img)

    @window.event
    def on_draw():
        global game
        window.clear()
        view.update(game.pop_delta())
        view.draw()

    game.start()
    pyglet.app.run()
