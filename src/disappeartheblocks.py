import pyglet
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
PAUSE_KEY = pyglet.window.key.P
RESTART_KEY = pyglet.window.key.SPACE

pause_overlay_html = '''
<center>
<b><h1>game paused</h1></b><br>
<h2>p to unpause<br>
space for new game</h2>
</center>
'''
game_over_overlay_html = '''
<center>
<b><h1>game over!</h1></b><br>
<h2>space for new game</h2>
</center>
'''

# Utility functions
def calc_tick_dt(level):
    """
    Calculates the fall velocity of pieces given a level
    """
    time = 0.5 - level*.06
    if time < .05:
        time = .05
    return time

def calc_points(level, rows):
    """
    Calculates the points that are gained when
    `rows` are cleared on `level`.

    Not the Tetris scoring, but rather completely
    made up.
    """ 
    return ((level+1)**2)*(rows**2)*10

def game_active_only(fn)
    """
    Decorator that allows a function to be run only if the
    game is active (not paused or over).  The function is
    assumed to be a member of a DisappearTheBlocks object.
    """
    def safe(self, *args, **kwargs):
        if self.paused or self.over:
            return
        return fn(self, *args, **kwargs)
    return safe

# Game implementation
class DisappearTheBlocks(object):
    """
    Implements a game of te... DisappearTheBlocks
    """
    blocks = {}
    last_action = 0 # time of last action
    score = 0
    level = 0
    rows_cleared = 0
    paused = True
    over = False

    def __init__(self):
        self.current_piece = random_piece(GRID_WIDTH//2,
                                          GRID_HEIGHT + 1)
        self.next_piece = random_piece(0,0)

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
        if self.over:
            return
        self.paused = False
        pyglet.clock.schedule_interval(self.tick, calc_tick_dt(self.level))
        
    def stop(self):
        self.paused = True
        pyglet.clock.unschedule(self.tick)

    def restart(self):
        if not (self.paused or self.over):
            return

        self.blocks = {}
        self._score = 0
        self.level = 0
        self.rows_cleared = 0
        self.current_piece = random_piece(GRID_WIDTH//2,
                                          GRID_HEIGHT + 1)
        self.next_piece = random_piece(0,0)
        self.over = False
        self.start()

    def toggle_pause(self):
        if self.paused:
            self.start()
        else:
            self.stop()

    def valid(self):
        """
        Checks to see if the piece is on the board and not on top of existing blocks
        """
        if self.current_piece.y < 0 or self.current_piece.left_edge < 0 \
                or (self.current_piece.right_edge >= GRID_WIDTH):
            return False

        return not (set(self.current_piece.blocks).intersection(set(self.blocks)))

    def update_score(self, rows):
        self.score += calc_points(self.level, rows)
    
    def update_level(self, rows):
        self.rows_cleared += rows
        if self.level < self.rows_cleared//20:
            self.level += 1
            pyglet.clock.unschedule(self.tick)
            pyglet.clock.schedule_interval(self.tick, calc_tick_dt(self.level))

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

        rows_cleared = 0
        shift = lambda ((x,y), index): ((x, y - rows_cleared),
                                        index)
        for (y, row) in rows:
            row = list(row)
            if len(row) == GRID_WIDTH:
                rows_cleared += 1
                continue
            if rows_cleared:
                blocks.update((shift(v) for v in row))
            else:
                blocks.update(row)

        self.blocks = blocks
        return rows_cleared

    def finish_fall(self):
        self.blocks.update(self.current_piece.blocks)
        rows = self.make_consistent()
        self.update_level(rows)
        self.update_score(rows)
        
        # if any part of the block is frozen outside the game board, that's game over
        if self.current_piece.y + self.current_piece.height >= GRID_HEIGHT:
            self.over = True
            self.stop()

        self.current_piece = self.next_piece
        self.current_piece.x = GRID_WIDTH//2
        self.current_piece.y = GRID_HEIGHT + 1
        self.next_piece = random_piece(0, 0)

    def tick(self, dt):
        now = pyglet.clock.get_default().time()
        self.current_piece.y -= 1
        if not self.valid():
            self.current_piece.y += 1
            if now - self.last_action > FREEZE_DELAY:
                self.finish_fall()

    @game_active_only
    def move_piece(self, direction):
        direction = 1 if direction > 0 else -1
        self.current_piece.x += direction
        if not self.valid():
            self.current_piece.x -= direction
        else:
            self.last_action = pyglet.clock.get_default().time()

    @game_active_only
    def rotate_piece(self, direction):
        direction = 1 if direction > 0 else -1
        self.current_piece.rotate(direction)
        if not self.valid():
            if not self.wiggle_piece():
                self.current_piece.rotate(-direction)
                return
        self.last_action = pyglet.clock.get_default().time()

    @game_active_only
    def drop_piece(self):
        while self.valid():
            self.current_piece.y -= 1
        self.current_piece.y += 1

    def wiggle_piece(self):
        """
        If a rotation isn't successful, try to make it fit by moving
        it left and right.

        Returns true if the piece was made to fit, false if it didn't.
        """
        for d in [-1, 1, -2, -3]:
            self.current_piece.x += d
            if self.valid():
                return True
            self.current_piece.x -= d
        
        return False

class DisappearTheBlocksView(object):
    """
    Displays a game
    """

    def __init__(self, game, x, y, block_img):
        self.game = game
        self.x = x
        self.y = y
        self.block_img = block_img
        self.last_state = set()
        self.batch = pyglet.graphics.Batch()
        self.game_group = pyglet.graphics.OrderedGroup(0)
        self.overlay_group = pyglet.graphics.OrderedGroup(1)
        self.next_piece_blocks = []
        self.next_piece = None
        
        width = block_img.width
        self.next_piece_anchor = (x + width*GRID_WIDTH + 110,
                                  440)

        self.build_grid()
        self.build_labels()

        self.bounding_box_coords = (x-1, y-1,
                                    x + width*GRID_WIDTH, y-1,
                                    x + width*GRID_WIDTH, y + width*GRID_HEIGHT,
                                    x-1, y + width*GRID_HEIGHT)

    def build_grid(self):
        self.block_grid = {}
        width = self.block_img.width
        for i in range(GRID_WIDTH):
            for j in range(GRID_HEIGHT):
                self.block_grid[(i,j)] = pyglet.sprite.Sprite(self.block_img,
                                                              x=self.x + i*width,
                                                              y=self.y + j*width,
                                                              batch=self.batch,
                                                              group=self.game_group)
                self.block_grid[(i,j)].visible = False

    def build_labels(self):
        width = self.block_img.width

        self.paused_label = pyglet.text.HTMLLabel(pause_overlay_html,
                                                  anchor_x="center",
                                                  x=self.x + width*GRID_WIDTH//2,
                                                  y=450,
                                                  group=self.overlay_group,
                                                  multiline=True, width=width*GRID_WIDTH)
        self.paused_label.color = (255,255,255,255)

        self.game_over_label = pyglet.text.HTMLLabel(game_over_overlay_html,
                                                  anchor_x="center",
                                                  x=self.x + width*GRID_WIDTH//2,
                                                  y=450,
                                                  group=self.overlay_group,
                                                  multiline=True, width=width*GRID_WIDTH)
        self.game_over_label.color = (255,255,255,255)

        self.next_piece_label = pyglet.text.Label("next piece", font_size=20,
                                                  anchor_x="center",
                                                  x=self.x + width*GRID_WIDTH + 125,
                                                  y=550, batch=self.batch,
                                                  group=self.game_group)
        self.next_piece_label.bold = True
        self.score_label = pyglet.text.Label("score", font_size=20,
                                             anchor_x="center",
                                             x=self.x + width*GRID_WIDTH + 125,
                                             y=400, batch=self.batch,
                                             group=self.game_group)
        self.score_label.bold = True
        self.score = pyglet.text.Label(str(self.game.score), font_size=16,
                                       anchor_x="center",
                                       x=self.x + width*GRID_WIDTH + 125,
                                       y=380, batch=self.batch,
                                       group=self.game_group)

        self.level_label = pyglet.text.Label("level", font_size=20,
                                             anchor_x="center",
                                             x=self.x + width*GRID_WIDTH + 125,
                                             y=340, batch=self.batch,
                                             group=self.game_group)
        self.level_label.bold = True
        self.level = pyglet.text.Label(str(self.game.level), font_size=16,
                                       anchor_x="center",
                                       x=self.x + width*GRID_WIDTH + 125,
                                       y=320, batch=self.batch,
                                       group=self.game_group)

        self.rows_cleared_label = pyglet.text.Label("rows cleared", font_size=20,
                                                    anchor_x="center",
                                                    x=self.x + width*GRID_WIDTH + 125,
                                                    y=280, batch=self.batch,
                                                    group=self.game_group)
        self.rows_cleared_label.bold = True
        self.rows_cleared = pyglet.text.Label(str(self.game.rows_cleared), font_size=16,
                                              anchor_x="center",
                                              x=self.x + width*GRID_WIDTH + 125,
                                              y=260, batch=self.batch,
                                              group=self.game_group)

    def build_next_piece(self):
        del self.next_piece_blocks
        self.next_piece_blocks = []

        ax, ay = self.next_piece_anchor
        width = self.block_img.width
        for ((x,y), index) in self.next_piece.blocks.iteritems():
            sprite = pyglet.sprite.Sprite(self.block_img,
                                          x=ax+x*width,
                                          y=ay+y*width,
                                          batch=self.batch,
                                          group=self.game_group)

            sprite.color = pieces[index]['color']
            self.next_piece_blocks.append(sprite)
            
    def update_next_piece(self):
        if self.next_piece is self.game.next_piece:
            return
        self.next_piece = game.next_piece
        self.build_next_piece()

    def update_grid(self):
        state = self.game.state
        s1 = set(self.last_state) 
        s2 = set(state)
        self.last_state = state

        now_empty = s1.difference(s2)
        new_blocks = s2.difference(s1)
        delta = []
        delta.extend(zip(now_empty, repeat(-1)))
        delta.extend( ((pos, state[pos]) for pos in new_blocks) )
        for ((x, y), index) in delta:
            # pieces can be outside the viewable area, so check for this
            if y >= GRID_HEIGHT:
                continue
            sprite = self.block_grid[(x,y)]
            if index == -1:
                sprite.visible = False
            else:
                sprite.visible = True
                sprite.color = pieces[index]['color']

    def draw_overlay(self):
        if game.over:
            self.game_over_label.draw()
        elif game.paused:
            self.paused_label.draw()

    def update(self):
        self.score.text = str(game.score)
        self.level.text = str(game.level)
        self.rows_cleared.text = str(game.rows_cleared)
        self.update_next_piece()
        self.update_grid()

    def draw(self):
        pyglet.gl.glColor3f(1.0, 1.0, 1.0)
        pyglet.graphics.draw(4, pyglet.gl.GL_LINE_LOOP,
                             ('v2i', self.bounding_box_coords))
        self.batch.draw()
        self.draw_overlay()


class DisappearTheBlocksKeyboardController(object):

    def __init__(self, move_fn, rotate_fn, drop_fn, pause_fn, restart_fn):
        self.mapping = {MOVE_LEFT_KEY: lambda: move_fn(-1),
                        MOVE_RIGHT_KEY: lambda:move_fn(1),
                        ROTATE_CW_KEY: lambda: rotate_fn(1),
                        DROP_KEY: lambda: drop_fn(),
                        PAUSE_KEY: lambda: pause_fn(),
                        RESTART_KEY: lambda: restart_fn()}

    def on_key_press(self, symbol, modifiers):
        if symbol in self.mapping:
            self.mapping[symbol]()

if __name__ == '__main__':
    window = pyglet.window.Window(800, 600)
    img = pyglet.resource.image('block.png')
    game = DisappearTheBlocks()
    view = DisappearTheBlocksView(game, 400-125, 20, img)
    
    controller = DisappearTheBlocksKeyboardController(game.move_piece,
                                                      game.rotate_piece,
                                                      game.drop_piece,
                                                      game.toggle_pause,
                                                      game.restart)

    @window.event
    def on_draw():
        window.clear()
        view.update()
        view.draw()

    window.push_handlers(controller)
    pyglet.app.run()
