import pyglet
from functools import wraps
from itertools import repeat, groupby

from pieces import *

GRID_WIDTH = 10
GRID_HEIGHT = 22
# don't let a piece freeze until this many seconds have
# passed after taking an action
FREEZE_DELAY = 0.3 

MOVE_LEFT_KEY = pyglet.window.key.LEFT
MOVE_RIGHT_KEY = pyglet.window.key.RIGHT
ROTATE_CW_KEY = pyglet.window.key.UP
DROP_KEY = pyglet.window.key.DOWN

class DisappearTheBlocks(object):
    """
    Implements a game of te... DisappearTheBlocks
    """
    blocks = {}
    last_action = 0 # time of last action
    _score = 0
    level = 0
    rows_cleared = 0

    def __init__(self):
        self.current_piece = random_piece(GRID_WIDTH//2,
                                          GRID_HEIGHT + 1)
        self.next_piece = random_piece(0,0)

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
        pyglet.clock.schedule_interval(self.tick, 0.5)
    def end(self):
        pyglet.clock.unschedule(self.tick)

    def valid(self):
        """
        Checks to see if the piece is on the board and not on top of existing blocks
        """
        if self.current_piece.y < 0 or self.current_piece.left_edge < 0 \
                or (self.current_piece.right_edge >= GRID_WIDTH):
            return False

        return not (set(self.current_piece.blocks).intersection(set(self.blocks)))

    def update_score(self, rows):
        self._score += ((self.level+1)**2)*(rows**2)*10
    
    def update_level(self, rows):
        self.rows_cleared += rows
        if self.level < self.rows_cleared//20:
            self.level += 1
            time = 0.5 - self.level*.06
            if time < .05:
                time = .05
            pyglet.clock.unschedule(self.tick)
            pyglet.clock.schedule_interval(self.tick, time)

    def finish_fall(self):
        self.blocks.update(self.current_piece.blocks)
        rows = self.make_consistent()
        self.update_score(rows)
        self.update_level(rows)
        self.current_piece = self.next_piece
        self.current_piece.x = GRID_WIDTH//2
        self.current_piece.y = GRID_HEIGHT + 1
        self.next_piece = random_piece(0,
                                       0)
        if not self.valid():
            game.end()

    def make_consistent(self):
        """
        Called after a piece is frozen, make_consistent() clears full rows
        and shifts down rows appropriately.  Returns the number of rows cleared
        """
        blocks = {}
        # function to get the y coordinate from an element of dict.iteritems()
        y_getter = lambda ((x, y), index): y
        rows = groupby(sorted(self.blocks.iteritems(), key=y_getter),
                       y_getter)

        shift_count = 0
        shift = lambda ((x,y), idx): ((x, y - shift_count),
                                     idx)
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
        return shift_count

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
            if not self.wiggle_piece():
                self.current_piece.rotate(-direction)
        else:
            self.last_action = pyglet.clock.get_default().time()

    def drop_piece(self):
        while self.valid():
            self.current_piece.y -= 1
        self.current_piece.y += 1

    def wiggle_piece(self):
        """
        If a rotation isn't successful, try to wiggle it around
        a bit to make it fit
        """
        for d in [-1, 1, -2, -3]:
            self.current_piece.x += d
            if self.valid():
                return True
            self.current_piece.x -= d
        
        return False

class DisappearTheBlocksView(object):
    """
    """

    def __init__(self, game, x, y, block_img):
        self.game = game
        self.x = x
        self.y = y
        self.block_img = block_img
        self.last_state = set()
        self.batch = pyglet.graphics.Batch()
        self.next_piece_blocks = []
        self.next_piece = None
        
        width = block_img.width
        self.next_piece_anchor = (x + width*GRID_WIDTH + 125,
                                  450)

        self.build_grid()
        self.build_labels()

        self.bb_coords = (x-1, y-1,
                          x + width*GRID_WIDTH, y-1,
                          x + width*GRID_WIDTH, y + width*GRID_HEIGHT,
                          x-1, y + width*GRID_HEIGHT)

    def build_grid(self):
        self.block_grid = {}
        width = self.block_img.width
        for i in range(GRID_WIDTH):
            for j in range(GRID_HEIGHT):
                self.block_grid[(i,j)] = pyglet.sprite.Sprite(self.block_img,
                                                              batch=self.batch,
                                                              x=self.x + i*width,
                                                              y=self.y + j*width)
                self.block_grid[(i,j)].visible = False

    def build_labels(self):
        width = self.block_img.width
        self.next_piece_label = pyglet.text.Label("next piece", font_size=20,
                                                  anchor_x="center",
                                                  x=self.x + width*GRID_WIDTH + 125,
                                                  y=560, batch=self.batch)
        self.next_piece_label.bold = True
        self.score_label = pyglet.text.Label("score", font_size=20,
                                             anchor_x="center",
                                             x=self.x + width*GRID_WIDTH + 125,
                                             y=400, batch=self.batch)
        self.score_label.bold = True
        self.score = pyglet.text.Label(str(self.game.score), font_size=16,
                                       anchor_x="center",
                                       x=self.x + width*GRID_WIDTH + 125,
                                       y=380, batch=self.batch)

        self.level_label = pyglet.text.Label("level", font_size=20,
                                             anchor_x="center",
                                             x=self.x + width*GRID_WIDTH + 125,
                                             y=340, batch=self.batch)
        self.level_label.bold = True
        self.level = pyglet.text.Label(str(self.game.level), font_size=16,
                                       anchor_x="center",
                                       x=self.x + width*GRID_WIDTH + 125,
                                       y=320, batch=self.batch)

        self.rows_cleared_label = pyglet.text.Label("rows cleared", font_size=20,
                                             anchor_x="center",
                                             x=self.x + width*GRID_WIDTH + 125,
                                             y=280, batch=self.batch)
        self.rows_cleared_label.bold = True
        self.rows_cleared = pyglet.text.Label(str(self.game.rows_cleared), font_size=16,
                                       anchor_x="center",
                                       x=self.x + width*GRID_WIDTH + 125,
                                       y=260, batch=self.batch)

    def build_next_piece(self):
        del self.next_piece_blocks
        self.next_piece_blocks = []

        ax, ay = self.next_piece_anchor
        width = self.block_img.width
        for (pos, index) in self.next_piece.blocks.iteritems():
            sprite = pyglet.sprite.Sprite(self.block_img,
                                          batch=self.batch,
                                          x=ax+pos[0]*width,
                                          y=ay+pos[1]*width)
            sprite.color = pieces[index]['color']
            self.next_piece_blocks.append(sprite)
            
    def update_next_piece(self):
        if self.next_piece is self.game.next_piece:
            return
        self.next_piece = game.next_piece
        self.build_next_piece()

    def update(self):
        self.score.text = str(game.score)
        self.level.text = str(game.level)
        self.rows_cleared.text = str(game.rows_cleared)
        self.update_next_piece()

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
            # pieces can be outside the viewable area, so check for this
            if pos[1] >= GRID_HEIGHT:
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
