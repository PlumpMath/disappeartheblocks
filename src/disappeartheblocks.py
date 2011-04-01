import pyglet
from random import randint
from functools import wraps
from itertools import repeat, groupby
from operator import itemgetter

from pieces import Piece, pieces

GRID_WIDTH = 10
GRID_HEIGHT = 22
GRID_HIDDEN_ROWS = 2
# don't let a piece freeze until this many seconds have
# passed after taking an action
FREEZE_DELAY = 0.3 

MOVE_LEFT_KEY = pyglet.window.key.LEFT
MOVE_RIGHT_KEY = pyglet.window.key.RIGHT
ROTATE_CW_KEY = pyglet.window.key.UP
DROP_KEY = pyglet.window.key.DOWN

def random_piece():
    index = randint(0, len(pieces) - 1)
    shape = pieces[index]['shape']
    x = GRID_WIDTH//2 - len(shape[0])//2
    y = GRID_HEIGHT - len(shape)
    return Piece(x, y, index)

class DisappearTheBlocks(object):
    """
    Implements a game of te... DisappearTheBlocks
    """
    blocks = {}
    last_action = 0 # time of last action
    current_piece = random_piece()
    _score = 0

    @property
    def score(self):
        return self._score

    @property
    def state(self):
        """
        Returns a dictionary representing the state of game, which is the
        conjunction of the blocks on the board and the blocks of the current
        piece
        """
        d = {}
        d.update(self.blocks, **self.current_piece.blocks)
        return d

    def start(self):
        pyglet.clock.schedule_interval(self.tick, 0.2)

    def valid(self):
        """
        Checks to see if the piece is on the board and not on top of existing blocks
        """
        if self.current_piece.y < 0 or self.current_piece.x < 0 \
                or (self.current_piece.x + self.current_piece.width > GRID_WIDTH):
            return False

        return not (set(self.current_piece.blocks).intersection(set(self.blocks)))

    def finish_fall(self):
        self.blocks.update(self.current_piece.blocks)
        self.make_consistent()
        self.current_piece = random_piece()

    def make_consistent(self):
        # keys are (x,y) coordinates, so we sort by the y coordinate,
        # group, and filter out groups that aren't full
        blocks = {}
        y_getter = lambda value: value[0][1]
        rows = groupby(sorted(self.blocks.iteritems(), key=y_getter),
                       y_getter)

        shift_count = 0
        def shift(dict_value):
            return ((dict_value[0][0], dict_value[0][1] - shift_count),
                    dict_value[1])

        for (y, row) in rows:
            row = list(row)
            if len(row) == GRID_WIDTH:
                shift_count += 1
                continue
            if shift_count:
                blocks.update((shift(v) for v in row))
            else:
                blocks.update(row)

        self.blocks = blocks

    def tick(self, dt):
        now = pyglet.clock.get_default().time()
        self.current_piece.y -= 1
        if not self.valid():
            self.current_piece.y += 1
            if now - self.last_action > FREEZE_DELAY:
                self.finish_fall()

    def move_piece(self, direction):
        direction = 1 if direction > 0 else -1
        self.current_piece.x += direction
        if not self.valid():
            self.current_piece.x -= direction
        else:
            self.last_action = pyglet.clock.get_default().time()


    def rotate_piece(self, direction):
        direction = 1 if direction > 0 else -1
        self.current_piece.rotate(direction)
        if not self.valid():
            self.current_piece.rotate(-direction)
        else:
            self.last_action = pyglet.clock.get_default().time()

    def drop_piece(self):
        while self.valid():
            self.current_piece.y -= 1
        self.current_piece.y += 1

    def _wiggle(self):
        return True

class DisappearTheBlocksView(object):
    """
    """

    def __init__(self, game, x, y, block_img):
        self.game = game
        self.last_state = set()
        self.batch = pyglet.graphics.Batch()
        
    
        width = block_img.width

        self.score_label = pyglet.text.Label("score", font_size=20,
                                             anchor_x="center",
                                             x=x + width*GRID_WIDTH + 100,
                                             y=400, batch=self.batch)
        self.score_label.bold = True
        self.score = pyglet.text.Label(str(game.score), font_size=16,
                                       anchor_x="center",
                                       x=x + width*GRID_WIDTH + 100,
                                       y=360, batch=self.batch)

        self.bb_coords = (x-1, y-1,
                          x + width*GRID_WIDTH, y-1,
                          x + width*GRID_WIDTH, y + width*(GRID_HEIGHT-GRID_HIDDEN_ROWS),
                          x-1, y + width*(GRID_HEIGHT-GRID_HIDDEN_ROWS))

        self.block_grid = {}
        for i in range(GRID_WIDTH):
            for j in range(GRID_HEIGHT):
                self.block_grid[(i,j)] = pyglet.sprite.Sprite(block_img,
                                                              batch=self.batch,
                                                              x=x + i*width,
                                                              y=y + j*width)
                self.block_grid[(i,j)].visible = False

    def update(self):
        state = game.state
        s1 = set(self.last_state) 
        s2 = set(state)
        self.last_state = state

        now_empty = s1.difference(s2)
        new_blocks = s2.difference(s1)
        delta = []
        delta.extend(zip(now_empty, repeat(-1)))
        delta.extend( ((pos, state[pos]) for pos in new_blocks) )
        for (pos, index) in delta:
            if pos[1] >= GRID_HEIGHT-GRID_HIDDEN_ROWS:
                continue
            sprite = self.block_grid[pos]
            if index == -1:
                sprite.visible = False
            else:
                sprite.visible = True
                sprite.color = pieces[index]['color']

    def draw(self):
        pyglet.gl.glColor3f(1.0, 1.0, 1.0)
        pyglet.graphics.draw(4, pyglet.gl.GL_LINE_LOOP,
                             ('v2i', self.bb_coords))
        self.batch.draw()


class DisappearTheBlocksKeyboardController(object):

    def __init__(self, move_fn, rotate_fn, drop_fn):
        self.mapping = {MOVE_LEFT_KEY: lambda: move_fn(-1),
                        MOVE_RIGHT_KEY: lambda:move_fn(1),
                        ROTATE_CW_KEY: lambda: rotate_fn(1),
                        DROP_KEY: lambda: drop_fn()}

    def on_key_press(self, symbol, modifiers):
        if symbol in self.mapping:
            self.mapping[symbol]()

if __name__ == '__main__':
    window = pyglet.window.Window(800, 600)
    img = pyglet.image.load('block.png')
    print 'loaded'
    game = DisappearTheBlocks()
    view = DisappearTheBlocksView(game, 400-125, 20, img)
    controller = DisappearTheBlocksKeyboardController(game.move_piece,
                                                      game.rotate_piece,
                                                      game.drop_piece)

    @window.event
    def on_draw():
        window.clear()
        view.update()
        view.draw()

    window.push_handlers(controller)
    game.start()
    print "running"
    pyglet.app.run()
