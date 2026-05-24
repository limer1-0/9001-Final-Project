import pygame
import sys
import json
import random

pygame.init()

FONT = pygame.font.SysFont("consolas", 18, bold=False)
TEXT_FONT = pygame.font.SysFont("consolas", 24, bold=True)
CELL_W = FONT.size("M")[0]
CELL_H = FONT.get_linesize() #get the pixel size of fonts
COLS = 168
ROWS = 42
WIDTH = COLS * CELL_W #game screen
HEIGHT = ROWS * CELL_H

FPS = 60

GRAVITY = 0.7
MOVE_SPEED = 5
JUMP_SPEED = -13
TEXT_SPEED = 35
LEVEL3_START_FREEZE_MS = 1000
FIRST_D_REGEN_DIALOG_PARTS_BEFORE_REGEN = 2

Armin_COLOR = (255, 90, 90)#TODO: put these in the class(or not)
BLACK = (0, 0, 0)
WHITE = (245, 245, 245)
BLUE = (0, 0, 245)
RED =  (245, 0, 0)
PURPLE = (173, 3, 222)
BOX = (15, 15, 30)
BOX_BORDER = (230, 230, 230)

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Seven(minus 4) Labors of Armin")
CLOCK = pygame.time.Clock()

GROUND = set()
BACKGROUND = pygame.Surface((WIDTH, HEIGHT))
CHAR_CACHE = {}
LEVEL_COLORS = {}
LEVEL_FILES = ["level1.json", "level2.json", "level3.json"]
CURRENT_LEVEL_INDEX = 0
CURRENT_LEVEL = None

TEXT_DATA = {}
PLAYED_LEVEL3 = False
LEVEL3_FIRST_ENTRY_ACTIVE = False
PLAYED_D_DIALOG = False

START_MENU_BG = None

class D:
    active = False

    W = CELL_W * 13
    H = CELL_H * 3
    rect = pygame.Rect(18 * CELL_W, 5 * CELL_H, W, H)

    ANIM_SPEED = 140
    SPEED = 3
    MAX_HP = 256
    BASE_HP_REGEN_DURATION = 2400 #the time it takes to generate health to 100%
    HP_REGEN_DURATION_DECREASE = 300
    MIN_HP_REGEN_DURATION = 0
    COLOR = WHITE
    INIDCATOR_COLOR = RED
    LASER_COLOR = PURPLE

    vy = 0
    on_ground = False
    direction = -1
    state = "idle"
    frame = 0
    
    hp = MAX_HP
    
    HP_REGEN_DURATION = BASE_HP_REGEN_DURATION
    
    hp_regenerating = False
    hp_zero_count = 0
    has_regenerated_hp = False

    dialog_pending = False
    HIT_DAMAGE = 1 
    HIT_PUSH_OFFSET = CELL_W * 2
    
    LASER_DURATION = 700
    LASER_CHARGE_DURATION = 500
    BASE_LASER_COOLDOWN = 2400
    MIN_LASER_COOLDOWN = 500
    LASER_COOLDOWN = BASE_LASER_COOLDOWN
    LASER_COOLDOWN_DECREASE = 100
    LASER_RANGE = WIDTH // 3
    LASER_DAMAGE = 10
    LASER_DAMAGE_INTERVAL = 300

    laser_active = False
    laser_charging = False
    laser_timer = LASER_DURATION
    laser_charge_timer = 0
    laser_cooldown_timer = 0
    laser_damage_timer = 0

    AI_JUMP_FAIL_X_TOLERANCE = CELL_W
    ai_blocked_state = None
    ai_blocked_dir = 0
    ai_jump_state = None
    ai_jump_dir = 0
    ai_jump_start_x = 0
    ai_jump_moved = False
    ai_airborne = False

    D_RIGHT = {
        "idle": [["  õ",
                  " (═╦══───━",
                  " / \\"]],
        "walk": [["  õ",
                  " (═╦══───━",
                  " / \\"] ,
                ["  õ",
                 " (═╦══───━",
                 "  >\\"],
                ["  õ",
                 " (═╦══───━",
                 "  |\\"],
                 ["  õ",
                  " (═╦══───━",
                  "  |>"]],
        "jump": [["  õ",
                  " (═╦══───━",
                  "  |>"]],
        "charing":[[
                  " õ",
                  "<═╦══───━",
                  "/ \\"
        ]],
        "shoot": [
                [" õ",
                 "<═╦══───━҉",
                 "/ \\"]],
    }

    D_LEFT = {
        "idle": [["       õ",
                  "━───══╦═)",
                  "      / \\"]],
        "walk": [["       õ",
                  "━───══╦═)",
                  "      / \\"] ,
                  ["       õ",
                   "━───══╦═)",
                   "      /<"],
                   ["       õ",
                    "━───══╦═)",
                    "      /|"],
                    ["       õ",
                     "━───══╦═)",
                     "      <|"]],
        "jump": [["       õ",
                  "━───══╦═)",
                  "      <|"]],
        "charing":[[
                   "       õ",
                    "━───══╦═>",
                    "      / \\"
        ]],
        "shoot": [
                   ["        õ",
                    "҉━───══╦═>",
                    "       / \\"]],
    }

    @staticmethod
    def reset(active=False, x=None, y=None):
        D.active = active
        D.rect = pygame.Rect(18 * CELL_W if x is None else int(x), 5 * CELL_H if y is None else int(y), D.W, D.H)
        D.vy = 0
        D.on_ground = False
        D.direction = -1
        D.state = "idle"
        D.frame = 0
        D.hp_zero_count = 0
        D.has_regenerated_hp = False
        D.dialog_pending = False
        D.apply_difficulty()
        D.hp = D.MAX_HP
        D.hp_regenerating = False
        D.ai_blocked_state = None
        D.ai_blocked_dir = 0
        D.ai_jump_state = None
        D.ai_jump_dir = 0
        D.ai_jump_start_x = D.rect.x
        D.ai_jump_moved = False
        D.ai_airborne = False

    # @staticmethod
    # def spawn(level):
    #     d_spawn = level.get("d_spawn") or level.get("D_spawn")
    #     if d_spawn:
    #         D.reset(active=True, x=spawn_x(d_spawn, 18), y=spawn_y(d_spawn, 5))
    #         return

    #     spots = open_spawn_spots(D.W, D.H, min_player_distance=CELL_W * 16)
    #     if spots:
    #         x, y = random.choice(spots)
    #         D.reset(active=True, x=x, y=y)
    #     else:
    #         D.reset(active=True)

    @staticmethod
    def spawn(level): #spawn in the middle of the screen
        d_spawn = level.get("d_spawn") or level.get("D_spawn")
        if d_spawn:
            D.reset(active=True, x=WIDTH // 2 - D.W // 2, y=spawn_y(d_spawn, 5))
            return

        spots = open_spawn_spots(D.W, D.H)
        if spots:
            _, x, y = min((abs(x + D.W // 2 - WIDTH // 2), x, y) for x, y in spots)
            D.reset(active=True, x=x, y=y)
        else:
            D.reset(active=True, x=WIDTH // 2 - D.W // 2)

    @staticmethod
    def apply_difficulty(): #increase difficulty as hp_zero_count(#times hp reaches 0) increases
        D.LASER_COOLDOWN = max(D.MIN_LASER_COOLDOWN, D.BASE_LASER_COOLDOWN - D.hp_zero_count * D.LASER_COOLDOWN_DECREASE)
        D.HP_REGEN_DURATION = max(D.MIN_HP_REGEN_DURATION, D.BASE_HP_REGEN_DURATION - D.hp_zero_count * D.HP_REGEN_DURATION_DECREASE)
        Level3ZombieSpawner.apply_difficulty(D.hp_zero_count)

    @staticmethod
    def increase_difficulty():#increase difficulty as hp_zero_count(#times hp reaches 0) increases
        D.hp_zero_count += 1
        D.apply_difficulty()


    @staticmethod
    def start_hp_regeneration():
        D.hp = max(0, D.hp)
        D.has_regenerated_hp = True
        D.dialog_pending = False

        D.increase_difficulty()

        if D.HP_REGEN_DURATION <= 0:
            D.hp = D.MAX_HP
            D.hp_regenerating = False
            return
        
        D.hp_regenerating = True

    @staticmethod
    def complete_first_dialog_regeneration():
        D.has_regenerated_hp = True
        D.dialog_pending = False
        D.increase_difficulty()
        D.hp = D.MAX_HP
        D.hp_regenerating = False
        #D.start_hp_regeneration()

    @staticmethod
    def update_hp_regeneration(dt): #regenerate some health 
        if not D.hp_regenerating:
            return
        if D.HP_REGEN_DURATION <= 0:
            D.hp = D.MAX_HP
            D.hp_regenerating = False
            return
        
        regen_amount = D.MAX_HP * dt / D.HP_REGEN_DURATION
        D.hp = min(D.MAX_HP, D.hp + regen_amount)

        if D.hp >= D.MAX_HP:
            D.hp = D.MAX_HP
            D.hp_regenerating = False

    @staticmethod
    def current_frame():
        frames = D.D_RIGHT[D.state] if D.direction == 1 else D.D_LEFT[D.state]
        D.frame = (pygame.time.get_ticks() // D.ANIM_SPEED) % len(frames)
        return frames[D.frame]

    @staticmethod
    def apply_gravity():
        D.vy += GRAVITY
        D.rect.y += D.vy
        if D.vy >= 0 and grounded_enough(D.rect):
            while grounded_enough(D.rect):
                D.rect.y -= 1
            D.rect.y += 1
            D.vy = 0
            D.on_ground = True
            if D.state == "jump":
                D.state = "idle"
        else:
            D.on_ground = False

    @staticmethod
    def player_in_laser_range(): #in range if at the same y and x distance within an interval
        if D.rect.bottom // CELL_H != Armin.rect.bottom // CELL_H:
            return False
        return abs(Armin.rect.centerx - D.rect.centerx) <= D.LASER_RANGE

    @staticmethod
    def move_horizontal(dx):
        if dx == 0:
            return 0
        old_x = D.rect.x
        D.rect.x += dx
        # front_x = (D.rect.right if dx > 0 else D.rect.left - 1) // CELL_W
        # floor_y = D.rect.bottom // CELL_H
        if hits_ground_side(D.rect, dx):# or (D.on_ground  and (front_x, floor_y) not in GROUND):
            D.rect.x = old_x
            return 0
        D.rect.x = clamp(D.rect.x, 0, WIDTH - D.rect.width)
        return D.rect.x - old_x

    @staticmethod
    def wall_in_front(move_dir):
        if move_dir == 0:
            return False
        probe = D.rect.copy()
        probe.x += move_dir * D.SPEED
        return hits_ground_side(probe, move_dir)

    @staticmethod
    def reset_block_state(state, desired_dir): 
    #if there's a wall too high and the boss can't reach the player(blocked), it waits there(not that I would make the level that complicated); if the player move to the
    #other side of the wall, the boss is not blocked
        if D.ai_blocked_state == state and D.ai_blocked_dir != desired_dir:
            D.ai_blocked_state = None
            D.ai_blocked_dir = 0

    @staticmethod
    def jump(state, move_dir):
        if not D.on_ground or move_dir == 0:
            return
        D.vy = JUMP_SPEED
        D.on_ground = False
        D.state = "jump"
        D.ai_jump_state = state
        D.ai_jump_dir = move_dir
        D.ai_jump_start_x = D.rect.x
        D.ai_jump_moved = False
        D.ai_airborne = True

    @staticmethod
    def finish_jump_if_landed():
        if not D.ai_airborne or not D.on_ground:
            return
        if abs(D.rect.x - D.ai_jump_start_x) <= D.AI_JUMP_FAIL_X_TOLERANCE:
            D.ai_blocked_state = D.ai_jump_state
            D.ai_blocked_dir = D.ai_jump_dir
        D.ai_jump_state = None
        D.ai_jump_dir = 0
        D.ai_jump_start_x = D.rect.x
        D.ai_jump_moved = False
        D.ai_airborne = False

    @staticmethod
    def move(state, move_dir): 
        if move_dir == 0:
            return 0
        D.reset_block_state(state, move_dir)
        if D.ai_blocked_state == state and D.ai_blocked_dir == move_dir:
            if D.wall_in_front(move_dir):
                return 0
            D.ai_blocked_state = None
            D.ai_blocked_dir = 0
        dx = D.move_horizontal(move_dir * D.SPEED)
        if dx != 0:
            if D.ai_airborne and D.ai_jump_dir == move_dir:
                D.ai_jump_moved = True
            return dx
        if D.on_ground and D.wall_in_front(move_dir):
            D.jump(state, move_dir)
            return D.move_horizontal(move_dir * D.SPEED)
        return 0

    @staticmethod
    def move_to_player():
        distance = Armin.rect.centerx - D.rect.centerx
        move_dir = 1 if distance >= 0 else -1
        D.direction = move_dir
        if D.player_in_laser_range():
            D.reset_block_state("attack", move_dir)
            return 0
        return D.move("attack", move_dir)

    @staticmethod
    def move_out_of_bullet_range():
        distance = Armin.rect.centerx - D.rect.centerx
        player_dir = 1 if distance >= 0 else -1
        D.direction = player_dir
        if abs(distance) >= Bullet.RANGE:
            D.reset_block_state("cooldown", -player_dir)
            return 0
        return D.move("cooldown", -player_dir)

    @staticmethod
    def laser_rect():
        y = D.rect.y + CELL_H
        if D.direction == 1:
            x = D.rect.right - CELL_W * 3
            return pygame.Rect(x, y, D.LASER_RANGE, CELL_H)
        x = max(0, D.rect.left - D.LASER_RANGE)
        return pygame.Rect(x, y, D.rect.left - x, CELL_H)

    @staticmethod
    def laser_hits_player():
        return D.laser_active and D.rect.bottom // CELL_H == Armin.rect.bottom // CELL_H and D.laser_rect().colliderect(Armin.rect)

    @staticmethod
    def update_laser(dt): #laser needs to charge before actually firing and the char for it is -----; this process is a part of the firing. when firing, it's =====; needs to cooldown after firing
        if D.laser_cooldown_timer > 0:
            D.laser_cooldown_timer = max(0, D.laser_cooldown_timer - dt)
            if D.laser_cooldown_timer == 0:
                D.laser_timer = D.LASER_DURATION

        if D.laser_active:
            D.state = "shoot"
            D.laser_timer -= dt
            D.laser_damage_timer -= dt

            if D.laser_hits_player() and D.laser_damage_timer <= 0:
                Armin.take_damage(D.LASER_DAMAGE)
                push_rect(Armin.rect, D.direction, Armin.LASER_HIT_PUSH_OFFSET)
                D.laser_damage_timer = D.LASER_DAMAGE_INTERVAL

            if D.laser_timer <= 0:
                D.laser_timer = 0
                D.laser_active = False
                D.laser_cooldown_timer = D.LASER_COOLDOWN
                D.laser_damage_timer = 0
            return True
        
        if D.laser_charging:
            D.state = "charing"
            D.laser_charge_timer -= dt

            if D.laser_charge_timer <= 0 and D.on_ground:
                D.laser_charging = False
                D.laser_active = True
                D.laser_timer = D.LASER_DURATION
                D.laser_damage_timer = 0
                D.state = "shoot"
            return True
        
        if D.on_ground and D.laser_cooldown_timer == 0 and D.laser_timer > 0 and D.player_in_laser_range():
            D.laser_charging = True
            D.laser_charge_timer = D.LASER_CHARGE_DURATION
            D.laser_damage_timer = 0
            D.state = "charing"
            return True
        return False

    @staticmethod
    def update():
        if not D.active:
            return
        dt = CLOCK.get_time()
        D.update_hp_regeneration(dt)
        if not D.laser_active and not D.laser_charging:
            D.direction = 1 if Armin.rect.centerx >= D.rect.centerx else -1
        D.apply_gravity()
        D.finish_jump_if_landed()
        if D.update_laser(dt):
            return
        dx = D.move_out_of_bullet_range() if D.laser_cooldown_timer > 0 else D.move_to_player()
        if D.on_ground:
            D.state = "walk" if dx else "idle"

    @staticmethod
    def take_hit(bullet_dir):
        if not D.active:
            return
        was_above_zero = D.hp > 0
        D.hp = max(0, D.hp - D.HIT_DAMAGE)
        if was_above_zero and D.hp <= 0:
            global PLAYED_D_DIALOG
            if D.hp_zero_count == 0 and not PLAYED_D_DIALOG:
                PLAYED_D_DIALOG = True
                D.hp = 0
                D.dialog_pending = True #display a dialog
                D.hp_regenerating = False
            else:
                D.start_hp_regeneration()
        push_rect(D.rect, bullet_dir, D.HIT_PUSH_OFFSET)

    @staticmethod
    def draw_laser():
        if not D.active or (not D.laser_active and not D.laser_charging):
            return
        if D.laser_active:
            laser_char = cached_char("=", D.LASER_COLOR)
        else:
            laser_char = cached_char("-", D.INIDCATOR_COLOR)
        
        y = D.rect.y + CELL_H
        if D.direction == 1:
            start_col = D.rect.right // CELL_W - 3
            end_col = min(COLS, start_col + D.LASER_RANGE // CELL_W)
            for col in range(start_col, end_col):
                SCREEN.blit(laser_char, (col * CELL_W, y))
        else:
            start_col = D.rect.left // CELL_W - 1
            end_col = max(-1, start_col - D.LASER_RANGE // CELL_W)
            for col in range(start_col, end_col, -1):
                SCREEN.blit(laser_char, (col * CELL_W, y))

    @staticmethod
    def draw_boss_ui():
        if not D.active:
            return
        bar_w = WIDTH - CELL_W * 8
        bar_h = CELL_H
        x = CELL_W * 4
        hp_y = CELL_H
        cooldown_y = CELL_H * 2 + 4
        pygame.draw.rect(SCREEN, BOX_BORDER, (x, hp_y, bar_w, bar_h), 1)
        hp_fill = int(bar_w * (D.hp / D.MAX_HP))
        pygame.draw.rect(SCREEN, D.COLOR, (x, hp_y, hp_fill, bar_h))
        SCREEN.blit(TEXT_FONT.render("HP", True, WHITE), (CELL_W, hp_y - 4))
        pygame.draw.rect(SCREEN, BOX_BORDER, (x, cooldown_y, bar_w, bar_h), 1)
        if D.laser_active:
            meter = D.laser_timer / D.LASER_DURATION
        elif D.laser_charging:
            meter = 1 - (D.laser_charge_timer / D.LASER_CHARGE_DURATION)
        elif D.laser_cooldown_timer > 0:
            meter = 1 - (D.laser_cooldown_timer / D.LASER_COOLDOWN)
        else:
            meter = 1
        pygame.draw.rect(SCREEN, (245,0,0), (x, cooldown_y, int(bar_w * max(0, min(1, meter))), bar_h))
        SCREEN.blit(TEXT_FONT.render("LASER", True, WHITE), (CELL_W, cooldown_y - 4))


    @staticmethod
    def draw():
        if not D.active:
            return
        for row_i, line in enumerate(D.current_frame()):
            for col_i, ch in enumerate(line):
                if ch != " ":
                    SCREEN.blit(cached_char(ch, D.COLOR), (D.rect.x + col_i * CELL_W, D.rect.y + row_i * CELL_H))
        D.draw_laser()


class Moose:
    MAX = 8
    W = CELL_W * 7
    H = CELL_H * 5
    COLOR = (245, 245, 143)
    SPEED = 2
    RANDOM_WALK_TIME_MIN = 900
    RANDOM_WALK_TIME_MAX = 2400
    MAX_HP = 3
    HIT_DAMAGE = 1
    HIT_PUSH_OFFSET = CELL_W * 3

    active = [False] * MAX #global(sort of) array for tracking moose
    rect = [pygame.Rect(0, 0, CELL_W * 7, CELL_H * 5) for _ in range(MAX)]
    vy = [0] * MAX
    direction = [1] * MAX
    move_direction = [0] * MAX
    state = ["idle"] * MAX
    random_walk_timer = [0] * MAX
    hp = [MAX_HP] * MAX

    MOOSE_RIGHT = {
        "idle": [["  $   $", 
                  "   \\_/", 
                  "\\__/''.", 
                  "(__ )", 
                  "|| ||"]], 
        "walk": [["  $   $", 
                  "   \\_/", 
                  "\\__/''.", 
                  "(__ )", 
                  "|> |>"], 
                  ["  $   $", 
                   "   \\_/", 
                   "\\__/''.", 
                   "(__ )", 
                   ">| >|"]]}
    MOOSE_LEFT = {
        "idle": [["$   $", 
                  " \\_/ ", 
                  ".''\\__/", 
                  "  (__ )", 
                  "  || ||"]], 
        "walk": [["$   $", 
                  " \\_/ ", 
                  ".''\\__/", 
                  "  (__ )", 
                  "  <| <|"], 
                  ["$   $", 
                   " \\_/ ", 
                   ".''\\__/", 
                   "  (__ )", 
                   "  |< |<"]]}

    @staticmethod
    def reset_all():
        for i in range(Moose.MAX):
            Moose.active[i] = False
            Moose.rect[i] = pygame.Rect(0, 0, Moose.W, Moose.H)
            Moose.vy[i] = 0
            Moose.direction[i] = 1
            Moose.move_direction[i] = 0
            Moose.state[i] = "idle"
            Moose.random_walk_timer[i] = 0
            Moose.hp[i] = Moose.MAX_HP

    @staticmethod
    def initialize(x, y):
        for i in range(Moose.MAX):
            if not Moose.active[i]:
                Moose.active[i] = True
                Moose.rect[i] = pygame.Rect(x, y, Moose.W, Moose.H)
                Moose.vy[i] = 0
                Moose.direction[i] = random.choice([-1, 1])
                Moose.move_direction[i] = 0
                Moose.state[i] = "idle"
                Moose.random_walk_timer[i] = random.randint(Moose.RANDOM_WALK_TIME_MIN, Moose.RANDOM_WALK_TIME_MAX)
                Moose.hp[i] = Moose.MAX_HP
                return True
        return False

    @staticmethod
    def spawn(count):
        spots = open_spawn_spots(Moose.W, Moose.H, min_player_distance=CELL_W * 12)
        random.shuffle(spots)
        for x, y in spots[:count]:
            Moose.initialize(x, y)

    @staticmethod
    def apply_gravity(i):
        Moose.vy[i] += GRAVITY
        Moose.rect[i].y += Moose.vy[i]
        if Moose.vy[i] >= 0 and grounded_enough(Moose.rect[i]):
            while grounded_enough(Moose.rect[i]):
                Moose.rect[i].y -= 1
            Moose.rect[i].y += 1
            Moose.vy[i] = 0

    @staticmethod
    def random_walk(i, dt):
        Moose.random_walk_timer[i] -= dt
        if Moose.random_walk_timer[i] <= 0:
            Moose.random_walk_timer[i] = random.randint(Moose.RANDOM_WALK_TIME_MIN, Moose.RANDOM_WALK_TIME_MAX)
            Moose.move_direction[i] = random.choice([-1, 0, 0, 0, 1])
            if Moose.move_direction[i] != 0:
                Moose.direction[i] = Moose.move_direction[i]
        return Moose.move_direction[i] * Moose.SPEED

    @staticmethod
    def move(i, dx):
        if dx == 0:
            Moose.state[i] = "idle"
            return
        old_x = Moose.rect[i].x
        Moose.rect[i].x += dx
        Moose.direction[i] = 1 if dx > 0 else -1
        front_x = (Moose.rect[i].right if dx > 0 else Moose.rect[i].left - 1) // CELL_W
        floor_y = Moose.rect[i].bottom // CELL_H
        if hits_ground_side(Moose.rect[i], dx) or (front_x, floor_y) not in GROUND:
            Moose.rect[i].x = old_x
            Moose.direction[i] *= -1
            Moose.move_direction[i] = 0
            Moose.state[i] = "idle"
        else:
            Moose.state[i] = "walk"
        Moose.rect[i].x = clamp(Moose.rect[i].x, 0, WIDTH - Moose.rect[i].width)

    @staticmethod
    def update():
        dt = CLOCK.get_time()
        for i in range(Moose.MAX):
            if Moose.active[i]:
                Moose.apply_gravity(i)
                Moose.move(i, Moose.random_walk(i, dt))

    @staticmethod
    def current_frame(i):
        frame_set = Moose.MOOSE_RIGHT if Moose.direction[i] == 1 else Moose.MOOSE_LEFT
        frames = frame_set[Moose.state[i]]
        return frames[(pygame.time.get_ticks() // 220) % len(frames)]

    @staticmethod
    def take_hit(i, bullet_dir):
        Moose.hp[i] -= Moose.HIT_DAMAGE
        if Moose.hp[i] <= 0:
            Moose.active[i] = False
            Armin.drop_sanity(Armin.MOOSE_DEATH_SANITY_DROP)
            return
        push_rect(Moose.rect[i], bullet_dir, Moose.HIT_PUSH_OFFSET)

    @staticmethod
    def draw():
        for i in range(Moose.MAX):
            if not Moose.active[i]:
                continue
            for row_i, line in enumerate(Moose.current_frame(i)):
                for col_i, ch in enumerate(line):
                    if ch != " ":
                        SCREEN.blit(cached_char(ch, Moose.COLOR), (Moose.rect[i].x + col_i * CELL_W, Moose.rect[i].y + row_i * CELL_H))


class Armin:
    W = CELL_W * 5
    H = CELL_H * 3
    rect = pygame.Rect(5 * CELL_W, 5 * CELL_H, W, H)
    vy = 0
    on_ground = False
    direction = 1
    state = "idle"
    frame = 0
    ANIM_SPEED = 140
    FIRE_INTERVAL = 160
    fire_timer = 0
    MAX_HEALTH = 100
    health = MAX_HEALTH
    MAX_SANITY = 100
    sanity = MAX_SANITY
    MOOSE_DEATH_SANITY_DROP = 34
    LASER_HIT_PUSH_OFFSET = CELL_W * 2

    ART_RIGHT = {
        "idle": [["  õ", 
                  " (╦╤─", 
                  " / \\"]], 
        "walk": [["  õ", 
                  " (╦╤─", 
                  " / \\"], 
                  ["  õ", 
                   " (╦╤─", 
                   "  >\\"], 
                   ["  õ", 
                    " (╦╤─", 
                    "  |\\"], 
                    ["  õ", 
                     " (╦╤─", 
                     "  |>"]], 
        "jump": [["  õ", 
                  " (╦╤─", 
                  "  |>"]], 
        "shoot": [[" õ", 
                   "<╦╤─", 
                   "/ \\"], 
                   [" õ", 
                    "<╦╤─҉", 
                    "/ \\"]]}
    ART_LEFT = {
        "idle": [["  õ", 
                  "─╤╦)", 
                  " / \\"]], 
        "walk": [["  õ", 
                  "─╤╦)", 
                  " / \\"], 
                  ["  õ", 
                   "─╤╦)", 
                   " /<"], 
                   ["  õ", 
                    "─╤╦)", 
                    " /|"], 
                    ["  õ", 
                     "─╤╦)", 
                     " <|"]], 
        "jump": [["  õ", 
                  "─╤╦)", 
                  " <|"]], 
        "shoot": [["   õ", 
                   " ─╤╦>", 
                   "  / \\"], 
                   ["   õ", 
                    "҉─╤╦>", 
                    "  / \\"]]}

    @staticmethod
    def reset():
        Armin.rect = pygame.Rect(5 * CELL_W, HEIGHT - 6 * CELL_H, Armin.W, Armin.H)
        Armin.vy = 0
        Armin.on_ground = False
        Armin.direction = 1
        Armin.state = "idle"
        Armin.frame = 0
        Armin.fire_timer = 0
        Armin.health = Armin.MAX_HEALTH
        Armin.sanity = Armin.MAX_SANITY

    @staticmethod
    def current_frame():
        frames = Armin.ART_RIGHT[Armin.state] if Armin.direction == 1 else Armin.ART_LEFT[Armin.state]
        Armin.frame = (pygame.time.get_ticks() // Armin.ANIM_SPEED) % len(frames)
        return frames[Armin.frame]

    @staticmethod
    def apply_gravity():
        Armin.vy += GRAVITY
        Armin.rect.y += Armin.vy
        if Armin.vy >= 0 and grounded_enough(Armin.rect): 
            while grounded_enough(Armin.rect):#this test makes sure not to fall into ground
                Armin.rect.y -= 1
            Armin.rect.y += 1
            Armin.vy = 0
            Armin.on_ground = True
            if Armin.state == "jump":
                Armin.state = "idle"
        else:
            Armin.on_ground = False

    @staticmethod
    def update():
        keys = pygame.key.get_pressed()
        dt = CLOCK.get_time()
        dx = 0
        if Armin.state != "shoot":
            if keys[pygame.K_a]:
                dx -= MOVE_SPEED
                Armin.direction = -1
            if keys[pygame.K_d]:
                dx += MOVE_SPEED
                Armin.direction = 1
            if keys[pygame.K_w] and Armin.on_ground:
                Armin.vy = JUMP_SPEED
                Armin.on_ground = False
                Armin.state = "jump"
            Armin.rect.x += dx
            if hits_ground_side(Armin.rect, dx):
                Armin.rect.x -= dx
            Armin.rect.x = clamp(Armin.rect.x, 0, WIDTH - Armin.rect.width)
        Armin.apply_gravity()
        if keys[pygame.K_j]:
            Armin.state = "shoot"
            Armin.fire_timer -= dt
            if Armin.fire_timer <= 0:
                Bullet.spawn()
                Armin.fire_timer = Armin.FIRE_INTERVAL
        else:
            Armin.fire_timer = 0
            if Armin.on_ground:
                Armin.state = "walk" if dx else "idle"

    @staticmethod
    def take_damage(amount):
        Armin.health = max(0, Armin.health - amount)

    @staticmethod
    def drop_sanity(amount):
        Armin.sanity = max(0, Armin.sanity - amount)

    @staticmethod
    def draw():
        for row_i, line in enumerate(Armin.current_frame()):
            for col_i, ch in enumerate(line):
                if ch != " ":
                    SCREEN.blit(cached_char(ch, Armin_COLOR), (Armin.rect.x + col_i * CELL_W, Armin.rect.y + row_i * CELL_H))

    @staticmethod
    def draw_health():
        SCREEN.blit(TEXT_FONT.render(f"HP: {Armin.health}", True, RED), (CELL_W, HEIGHT - CELL_H * 3))
        SCREEN.blit(TEXT_FONT.render(f"Sanity: {Armin.sanity}", True, RED), (CELL_W, HEIGHT - CELL_H * 2))


class Teleport:
    X = WIDTH - CELL_W * 3
    Y = CELL_H * 37
    W = CELL_W * 3
    H = CELL_H
    ARROW = "==>"
    COLOR = RED

    @staticmethod
    def set_y(y):
        Teleport.Y = clamp(y, 0, HEIGHT - Teleport.H)

    @staticmethod
    def rect():
        return pygame.Rect(Teleport.X, Teleport.Y, Teleport.W, Teleport.H)

    @staticmethod
    def available():
        return not any(Zombie.active) and not D.active

    @staticmethod
    def touched_by_player():
        return Teleport.available() and Armin.rect.colliderect(Teleport.rect())

    @staticmethod
    def draw():
        if not Teleport.available():
            return
        for i, ch in enumerate(Teleport.ARROW):
            if ch != " ":
                SCREEN.blit(cached_char(ch, Teleport.COLOR), (Teleport.X + i * CELL_W, Teleport.Y))


class Zombie:
    MAX = 20
    W = CELL_W * 4
    H = CELL_H * 4
    COLOR = (120, 220, 120)
    SPEED = 2
    RANDOM_WALK_TIME_MIN = 700
    RANDOM_WALK_TIME_MAX = 1800
    SPOT_RANGE = CELL_W * 28
    ATTACK_RANGE = CELL_W * 3
    ATTACK_INTERVAL = 1200
    ATTACK_DAMAGE = 5
    MAX_HP = 10
    HIT_DAMAGE = 2
    HIT_PUSH_OFFSET = CELL_W * 3

    active = [False] * MAX
    rect = [pygame.Rect(0, 0, CELL_W * 4, CELL_H * 4) for _ in range(MAX)]
    vy = [0] * MAX
    direction = [1] * MAX
    state = ["idle"] * MAX
    random_walk_timer = [0] * MAX
    attack_timer = [0] * MAX
    hp = [MAX_HP] * MAX
    hit_alerted = [False] * MAX

    ZOMBIE_RIGHT = {
        "idle": [["  ", 
                  " Ø", 
                  "( ¯`", 
                  ")) "]],
        "walk": [["  ", 
                  " Ø", 
                  "( ¯`", 
                  "V) "], 
                  ["  ", 
                  " Ø", 
                  "( ¯`", 
                  "|> "], 
                  ["  ", 
                  " Ø", 
                  "( ¯`", 
                  ")\\ "]],
        "attack": [["   .", 
                    " Ø/", 
                    "( ¯`", 
                    "|\\ "], 
                    [" .", 
                    "Ø__", 
                    "\\  ", 
                    "|\\ "], 
                   [ ".", 
                    "Ø/`", 
                    "\\  ", 
                    "|\\ "], 
                    [".,", 
                    "Ø)", 
                    "\\  ", 
                    "|\\ "], 
                    [" _", 
                    " Ø \\ ", 
                    "( \\) ", 
                    "|\\'"], 
                    [" ", 
                    " Ø ", 
                    "( \\ ", 
                    "|\\ '"], 
                    ["  ", 
                    " Ø", 
                    "( ¯`", 
                    ")) "]]
    }
    ZOMBIE_LEFT = {
        "idle": [["  ", 
                  "  Ø", 
                  "´¯ )", 
                  "  (( "]],
        "walk": [["  ", 
                  "  Ø", 
                  "´¯ )", 
                  "  (V "], 
                  ["  ", 
                  "  Ø", 
                  "´¯ )", 
                  "  <|"], 
                  ["  ", 
                  "  Ø", 
                  "´¯ )", 
                  "  /("]],
        "attack": [[" .", 
                    "  \\Ø", 
                    " ´¯ )", 
                    "   /| "], 
                    ["   .", 
                    "  __Ø", 
                    "    /  ", 
                    "   /| "], 
                    ["    .", 
                    "   `\\Ø", 
                    "    /  ", 
                    "   /| "], 
                    ["    ,.", 
                    "    (Ø", 
                    "    / ", 
                    "   /| "], 
                    ["  _", 
                    " / Ø ", 
                    "( / ) ", 
                    "  '/|"], 
                    ["  ", 
                    "   Ø ", 
                    "  / ) ", 
                    "  '/|"], 
                    ["   ", 
                    "   Ø", 
                    " ´¯ )", 
                    "   (( "]]
    }

    @staticmethod
    def reset_all():
        for i in range(Zombie.MAX):
            Zombie.active[i] = False
            Zombie.rect[i] = pygame.Rect(0, 0, Zombie.W, Zombie.H)
            Zombie.vy[i] = 0
            Zombie.direction[i] = 1
            Zombie.state[i] = "idle"
            Zombie.random_walk_timer[i] = 0
            Zombie.attack_timer[i] = 0
            Zombie.hp[i] = Zombie.MAX_HP
            Zombie.hit_alerted[i] = False

    @staticmethod
    def initialize(x, y):
        for i in range(Zombie.MAX):
            if not Zombie.active[i]:
                Zombie.active[i] = True
                Zombie.rect[i] = pygame.Rect(x, y, Zombie.W, Zombie.H)
                Zombie.vy[i] = 0
                Zombie.direction[i] = random.choice([-1, 1])
                Zombie.state[i] = "idle"
                Zombie.random_walk_timer[i] = random.randint(Zombie.RANDOM_WALK_TIME_MIN, Zombie.RANDOM_WALK_TIME_MAX)
                Zombie.attack_timer[i] = 0
                Zombie.hp[i] = Zombie.MAX_HP
                Zombie.hit_alerted[i] = False
                return True
        return False

    @staticmethod
    def spawn(count):
        spots = open_spawn_spots(Zombie.W, Zombie.H, min_player_distance=CELL_W * 12)
        random.shuffle(spots)
        spawned = 0
        for x, y in spots:
            if spawned >= count:
                break
            spawned += 1 if Zombie.initialize(x, y) else 0
        return spawned

    @staticmethod
    def apply_gravity(i):
        Zombie.vy[i] += GRAVITY
        Zombie.rect[i].y += Zombie.vy[i]
        if Zombie.vy[i] >= 0 and grounded_enough(Zombie.rect[i]):
            while grounded_enough(Zombie.rect[i]):
                Zombie.rect[i].y -= 1
            Zombie.rect[i].y += 1
            Zombie.vy[i] = 0

    @staticmethod
    def same_level_as_player(i):
        return Zombie.rect[i].bottom // CELL_H == Armin.rect.bottom // CELL_H

    @staticmethod
    def clear_path_to_player(i):
        zrect = Zombie.rect[i]
        start = min(zrect.centerx, Armin.rect.centerx) // CELL_W
        end = max(zrect.centerx, Armin.rect.centerx) // CELL_W
        top = min(zrect.top, Armin.rect.top) // CELL_H
        bottom = max(zrect.bottom, Armin.rect.bottom) // CELL_H
        floor_y = zrect.bottom // CELL_H
        for x in range(start, end + 1):
            for y in range(top, bottom):
                if (x, y) in GROUND:
                    return False
            if (x, floor_y) not in GROUND:
                return False
        return True

    @staticmethod
    def can_see_player(i): #can only see player if the zombie can reach the player by moving horizontally and within range; ignores the range if hit by bullet
        if not Zombie.hit_alerted[i] and abs(Armin.rect.centerx - Zombie.rect[i].centerx) > Zombie.SPOT_RANGE:
            return False
        if not Zombie.same_level_as_player(i):
            return False
        return Zombie.clear_path_to_player(i)

    @staticmethod
    def random_walk(i, dt):
        Zombie.random_walk_timer[i] -= dt
        if Zombie.random_walk_timer[i] <= 0:
            Zombie.random_walk_timer[i] = random.randint(Zombie.RANDOM_WALK_TIME_MIN, Zombie.RANDOM_WALK_TIME_MAX)
            Zombie.direction[i] = random.choice([-1, 0, 1])
        return Zombie.direction[i] * Zombie.SPEED

    @staticmethod
    def move(i, dx):
        if dx == 0:
            Zombie.state[i] = "idle"
            return
        old_x = Zombie.rect[i].x
        Zombie.rect[i].x += dx
        Zombie.direction[i] = 1 if dx > 0 else -1
        front_x = (Zombie.rect[i].right if dx > 0 else Zombie.rect[i].left - 1) // CELL_W
        floor_y = Zombie.rect[i].bottom // CELL_H
        if hits_ground_side(Zombie.rect[i], dx) or (front_x, floor_y) not in GROUND:
            Zombie.rect[i].x = old_x
            Zombie.direction[i] *= -1
            Zombie.state[i] = "idle"
        else:
            Zombie.state[i] = "walk"
        Zombie.rect[i].x = clamp(Zombie.rect[i].x, 0, WIDTH - Zombie.rect[i].width)

    @staticmethod
    def attack(i, dt):
        Zombie.state[i] = "attack"
        Zombie.attack_timer[i] -= dt
        if Zombie.attack_timer[i] <= 0:
            Armin.take_damage(Zombie.ATTACK_DAMAGE)
            Zombie.attack_timer[i] = Zombie.ATTACK_INTERVAL

    @staticmethod
    def update():
        dt = CLOCK.get_time()
        for i in range(Zombie.MAX):
            if not Zombie.active[i]:
                continue
            
            Zombie.apply_gravity(i)

            if Zombie.can_see_player(i):
                distance = Armin.rect.centerx - Zombie.rect[i].centerx
                Zombie.direction[i] = 1 if distance > 0 else -1
                if abs(distance) <= Zombie.ATTACK_RANGE:
                    Zombie.attack(i, dt)
                else:
                    Zombie.move(i, Zombie.direction[i] * Zombie.SPEED)
            else:
                Zombie.move(i, Zombie.random_walk(i, dt))

    @staticmethod
    def current_frame(i):
        # frame_set= Zombie.ZOMBIE_RIGHT if Zombie.direction[i] == 1 else Zombie.ZOMBIE_LEFT
        # packed = frame_set[Zombie.state[i]][0]
        # frame_h = Zombie.H // CELL_H
        # frame_count = len(packed) // frame_h

        # if frame_count <= 1:
        #     return packed
        # speed = Zombie.ATTACK_INTERVAL // frame_count if Zombie.state[i] == "attack" else 180
        # frame = (pygame.time.get_ticks() // speed) % frame_count
        # return packed[frame * frame_h:frame * frame_h + frame_h]
        art = Zombie.ZOMBIE_RIGHT if Zombie.direction[i] == 1 else Zombie.ZOMBIE_LEFT
        frames = art[Zombie.state[i]]
        frame = (pygame.time.get_ticks() // 180) % len(frames)
        return frames[frame]

        

    @staticmethod
    def take_hit(i, bullet_dir):
        Zombie.hit_alerted[i] = True
        Zombie.hp[i] -= Zombie.HIT_DAMAGE
        
        if Zombie.hp[i] <= 0:
            Zombie.active[i] = False
            return
        push_rect(Zombie.rect[i], bullet_dir, Zombie.HIT_PUSH_OFFSET)

    @staticmethod
    def draw():
        for i in range(Zombie.MAX):
            if not Zombie.active[i]:
                continue
            for row_i, line in enumerate(Zombie.current_frame(i)):
                for col_i, ch in enumerate(line):
                    if ch != " ":
                        SCREEN.blit(cached_char(ch, Zombie.COLOR), (Zombie.rect[i].x + col_i * CELL_W, Zombie.rect[i].y + row_i * CELL_H))


class Level3ZombieSpawner: 
    BASE_INTERVAL = 2200
    INTERVAL_RANDOM_DELTA = 900
    SPAWN_COUNT_MIN = 1
    BASE_SPAWN_COUNT_MAX = 3
    SPAWN_COUNT_MAX = BASE_SPAWN_COUNT_MAX
    BASE_MAX_TOTAL_ZOMBIES = 5
    MAX_TOTAL_ZOMBIES = BASE_MAX_TOTAL_ZOMBIES
    MAX_TOTAL_ZOMBIES_UPPER_BOUND = 20

    enabled = False
    timer = 0
    spawned_total = 0

    @staticmethod
    def reset(enabled=False):
        Level3ZombieSpawner.enabled = enabled
        Level3ZombieSpawner.spawned_total = 0
        Level3ZombieSpawner.apply_difficulty(D.hp_zero_count)
        Level3ZombieSpawner.schedule_next()

    @staticmethod
    def apply_difficulty(d_hp_zero_count):
        Level3ZombieSpawner.SPAWN_COUNT_MAX = min(
            Level3ZombieSpawner.MAX_TOTAL_ZOMBIES_UPPER_BOUND,
            Level3ZombieSpawner.BASE_SPAWN_COUNT_MAX + d_hp_zero_count,
        )
        Level3ZombieSpawner.MAX_TOTAL_ZOMBIES = min(
            Level3ZombieSpawner.MAX_TOTAL_ZOMBIES_UPPER_BOUND,
            Level3ZombieSpawner.BASE_MAX_TOTAL_ZOMBIES + d_hp_zero_count * 3,
        )

    @staticmethod
    def schedule_next():
        delta = random.randint(-Level3ZombieSpawner.INTERVAL_RANDOM_DELTA, Level3ZombieSpawner.INTERVAL_RANDOM_DELTA)
        Level3ZombieSpawner.timer = max(300, Level3ZombieSpawner.BASE_INTERVAL + delta)

    @staticmethod
    def update():
        if not Level3ZombieSpawner.enabled:
            return

        remaining = Level3ZombieSpawner.MAX_TOTAL_ZOMBIES - Level3ZombieSpawner.spawned_total
        if remaining <= 0:
            return

        Level3ZombieSpawner.timer -= CLOCK.get_time()
        if Level3ZombieSpawner.timer > 0:
            return

        count = random.randint(Level3ZombieSpawner.SPAWN_COUNT_MIN, Level3ZombieSpawner.SPAWN_COUNT_MAX)
        count = min(count, remaining)
        Level3ZombieSpawner.spawned_total += Zombie.spawn(count)
        Level3ZombieSpawner.schedule_next()


class Bullet:
    MAX = 64
    SPEED = 12
    RANGE = WIDTH // 6
    active = [False] * MAX
    x = [0] * MAX
    y = [0] * MAX
    vx = [0] * MAX
    start_x = [0] * MAX

    @staticmethod
    def reset():
        for i in range(Bullet.MAX):
            Bullet.active[i] = False
            Bullet.x[i] = 0
            Bullet.y[i] = 0
            Bullet.vx[i] = 0
            Bullet.start_x[i] = 0

    @staticmethod
    def spawn(shooter=None):
        if shooter is None:
            shooter = Armin
        for i in range(Bullet.MAX):
            if not Bullet.active[i]:
                Bullet.active[i] = True
                if shooter.direction == 1:
                    Bullet.x[i] = shooter.rect.right
                    Bullet.vx[i] = Bullet.SPEED
                else:
                    Bullet.x[i] = shooter.rect.left - CELL_W
                    Bullet.vx[i] = -Bullet.SPEED
                Bullet.start_x[i] = Bullet.x[i]
                Bullet.y[i] = shooter.rect.y + CELL_H
                return

    @staticmethod
    def update():
        for i in range(Bullet.MAX):
            if not Bullet.active[i]:
                continue
            Bullet.x[i] += Bullet.vx[i]
            col = Bullet.x[i] // CELL_W
            row = Bullet.y[i] // CELL_H
            if Bullet.x[i] < 0 or Bullet.x[i] >= WIDTH or abs(Bullet.x[i] - Bullet.start_x[i]) > Bullet.RANGE or (col, row) in GROUND:
                Bullet.active[i] = False
                continue
            bullet_rect = pygame.Rect(Bullet.x[i], Bullet.y[i], CELL_W, CELL_H)
            bullet_dir = 1 if Bullet.vx[i] > 0 else -1
            for z in range(Zombie.MAX):
                if Zombie.active[z] and bullet_rect.colliderect(Zombie.rect[z]):
                    Bullet.active[i] = False
                    Zombie.take_hit(z, bullet_dir)
                    break
            if not Bullet.active[i]:
                continue
            for m in range(Moose.MAX):
                if Moose.active[m] and bullet_rect.colliderect(Moose.rect[m]):
                    Bullet.active[i] = False
                    Moose.take_hit(m, bullet_dir)
                    break
            if not Bullet.active[i]:
                continue
            if D.active and bullet_rect.colliderect(D.rect):
                Bullet.active[i] = False
                D.take_hit(bullet_dir)

    @staticmethod
    def draw():
        bullet_char = cached_char("-", WHITE)
        for i in range(Bullet.MAX):
            if Bullet.active[i]:
                SCREEN.blit(bullet_char, (Bullet.x[i], Bullet.y[i]))


def load_json(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def cached_char(ch, color):
    key = (ch, color)
    surf = CHAR_CACHE.get(key)
    if surf is None:
        surf = FONT.render(ch, True, color)
        CHAR_CACHE[key] = surf
    return surf


def color_from_key(key):
    return tuple(LEVEL_COLORS.get(key, [255, 255, 255]))


def build_background(level):
    BACKGROUND.fill(tuple(level.get("clear_color", [0, 0, 0])))
    bg = level["background"]
    bgc = level["background_colors"]
    for y in range(min(ROWS, len(bg))):
        for x in range(min(COLS, len(bg[y]))):
            ch = bg[y][x]
            if ch != " ":
                BACKGROUND.blit(cached_char(ch, color_from_key(bgc[y][x])), (x * CELL_W, y * CELL_H))


def build_ground(level):
    GROUND.clear()
    for y, row in enumerate(level["ground"][:ROWS]):
        for x, ch in enumerate(row[:COLS]):
            if ch == "#":
                GROUND.add((x, y))


def grounded_enough(rect): #see if there is enough ground to support the character
    tile_y = rect.bottom // CELL_H
    start_x = rect.left // CELL_W
    end_x = (rect.right - 1) // CELL_W
    count = 0
    needed = max(1, (end_x - start_x + 1) // 2) #half the character's width is needed to support the character
    for tile_x in range(start_x, end_x + 1):
        if (tile_x, tile_y) in GROUND:
            count += 1
            if count >= needed:
                return True
    return False


def hits_ground_side(rect, dx):
    top = rect.top // CELL_H
    bottom = (rect.bottom - 1) // CELL_H
    if dx > 0:
        x = (rect.right - 1) // CELL_W
    elif dx < 0:
        x = rect.left // CELL_W
    else:
        return False
    for y in range(top, bottom + 1):
        if (x, y) in GROUND:
            return True
    return False



def clamp(value, low, high):
    return max(low, min(high, value))


def spawn_x(data, default_col):
    return int(data.get("x", data.get("col", default_col) * CELL_W))


def spawn_y(data, default_row):
    return int(data.get("y", data.get("row", default_row) * CELL_H))


def rect_hits_ground(rect):
    left = rect.left // CELL_W
    right = (rect.right - 1) // CELL_W
    top = rect.top // CELL_H
    bottom = (rect.bottom - 1) // CELL_H
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            if (x, y) in GROUND:
                return True
    return False


def open_spawn_spots(width, height, min_player_distance=0):#finds coordinates where a character can be spawned on
    spots = []
    for x, y in sorted(GROUND):
        rect = pygame.Rect(x * CELL_W, y * CELL_H - height, width, height)
        if rect.top < 0:
            continue
        if min_player_distance and abs(rect.centerx - Armin.rect.centerx) < min_player_distance:
            continue
        if grounded_enough(rect) and not rect_hits_ground(rect):
            spots.append((rect.x, rect.y))
    return spots


def push_rect(rect, direction, distance): #move a rect(character) for a certain amount to simulate being impact by bullet or laser
    old_x = rect.x
    rect.x = clamp(rect.x + direction * distance, 0, WIDTH - rect.width)
    if hits_ground_side(rect, direction):
        rect.x = old_x


def draw_ground():
    ground_char = cached_char("#", color_from_key("g"))
    for x, y in GROUND:
        SCREEN.blit(ground_char, (x * CELL_W, y * CELL_H))


def wrap_words(text, max_width):
    words, lines, line = text.split(), [], ""
    for word in words:
        test = word if not line else line + " " + word
        if TEXT_FONT.size(test)[0] <= max_width:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


# def draw_paragraph(text, x, y, max_width, color):
#     for i, line in enumerate(wrap_words(text, max_width)):
#         SCREEN.blit(TEXT_FONT.render(line, True, color), (x, y + i * 32))
def draw_paragraph(text, x, y, max_width, color):
    lines = []
    for part in text.split("\n"):
        lines.extend(wrap_words(part, max_width))

    for i, line in enumerate(lines):
        SCREEN.blit(TEXT_FONT.render(line, True, color), (x, y + i * 32))


def run_text_sequence(sequence):
    for entry in sequence:
        full_text, visible, done = entry["text"], 0, False
        while True:
            dt = CLOCK.tick(FPS)
            go_next = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    if done:
                        go_next = True
                    else:
                        visible = len(full_text)
                        done = True
            if go_next:
                break
            if not done:
                visible += TEXT_SPEED * dt / 1000
                if visible >= len(full_text):
                    visible = len(full_text)
                    done = True
            text = full_text[:int(visible)]
            if entry["mode"] == "black":
                SCREEN.fill(BLACK)
                draw_paragraph(text, 40, HEIGHT//2 - 100, WIDTH - 80, WHITE)
                if done:
                    SCREEN.blit(TEXT_FONT.render("Press Enter", True, WHITE), (40, HEIGHT - 80))
            elif entry["mode"] == "box":
                draw_frame()
                box_rect = pygame.Rect(20, HEIGHT - 150, WIDTH - 40, 120)
                pygame.draw.rect(SCREEN, BOX, box_rect)
                pygame.draw.rect(SCREEN, BOX_BORDER, box_rect, 3)
                speaker = entry.get("speaker", "")
                if speaker:
                    SCREEN.blit(TEXT_FONT.render(speaker, True, WHITE), (40, HEIGHT - 135))
                draw_paragraph(text, 40, HEIGHT - 95, WIDTH - 80, WHITE)
                if done:
                    SCREEN.blit(TEXT_FONT.render("Enter", True, WHITE), (WIDTH - 120, HEIGHT - 55))
            pygame.display.flip()


def run_level3_intro():
    elapsed = 0
    while elapsed < LEVEL3_START_FREEZE_MS:
        dt = CLOCK.tick(FPS)
        elapsed += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        draw_frame(CURRENT_LEVEL_INDEX)
        pygame.display.flip()

    run_text_sequence(TEXT_DATA.get("level3_intro", []))


def run_level3_dialog():
    sequence = TEXT_DATA.get("box", [])
    split_at = min(FIRST_D_REGEN_DIALOG_PARTS_BEFORE_REGEN, len(sequence))
    if split_at > 0:
        run_text_sequence(sequence[:split_at])
    D.complete_first_dialog_regeneration()
    if split_at < len(sequence):
        run_text_sequence(sequence[split_at:])


def draw_level3_game_over_screen(selection): 
    SCREEN.fill(BLACK)
    title = TEXT_FONT.render("GAME OVER", True, WHITE)
    SCREEN.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - CELL_H * 5)))
    entries = TEXT_DATA.get("special_game_over", [])
    sentence = entries[0]["text"]
    draw_paragraph(sentence, WIDTH // 4 + 120, HEIGHT // 2 - CELL_H * 3, WIDTH // 2, WHITE)
    for i, option in enumerate(["Restart", "Quit"]):
        prefix = "> " if i == selection else "  "
        color = Armin_COLOR if i == selection else WHITE
        text = TEXT_FONT.render(prefix + option, True, color)
        SCREEN.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + i * CELL_H * 2)))
    hint = TEXT_FONT.render("Use Up/Down and Enter", True, WHITE)
    SCREEN.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + CELL_H * 5)))


def level_teleport_y(level):
    if "teleport_y" in level:
        return int(level["teleport_y"])
    if "teleport_row" in level:
        return int(level["teleport_row"]) * CELL_H
    return Teleport.Y


def load_level(index):
    global CURRENT_LEVEL, CURRENT_LEVEL_INDEX, LEVEL_COLORS
    CURRENT_LEVEL_INDEX = index
    CURRENT_LEVEL = load_json(LEVEL_FILES[index])
    LEVEL_COLORS = {k: tuple(v) for k, v in CURRENT_LEVEL["colors"].items()}
    return CURRENT_LEVEL


def reset_current_level(preserve_player_y=None, preserve_player_stats=False):
    level = CURRENT_LEVEL
    preserved_health = Armin.health
    preserved_sanity = Armin.sanity

    build_background(level)
    build_ground(level)
    Teleport.set_y(level_teleport_y(level))
    Armin.reset()
    D.reset(active=False)
    Bullet.reset()
    Zombie.reset_all()
    Moose.reset_all()

    if preserve_player_stats:
        Armin.health = preserved_health
        Armin.sanity = preserved_sanity
    if preserve_player_y is not None:
        Armin.rect.y = clamp(int(preserve_player_y), 0, HEIGHT - Armin.rect.height)
        Armin.vy = 0
        Armin.on_ground = grounded_enough(Armin.rect)

    if CURRENT_LEVEL_INDEX == 2:
        Level3ZombieSpawner.reset(True)
        D.spawn(level)
    else:
        Level3ZombieSpawner.reset(False)
        Zombie.spawn(level.get("zombie_count", 5))
    Moose.spawn(level.get("moose_count", 3))


def advance_level():
    player_y = Armin.rect.y
    next_index = CURRENT_LEVEL_INDEX + 1

    if next_index >= len(LEVEL_FILES):
        return False
    
    load_level(next_index)
    reset_current_level(preserve_player_y=player_y, preserve_player_stats=True)
    return True

def draw_health_game_over_screen(selection):
    SCREEN.fill(BLACK)
    title = TEXT_FONT.render("GAME OVER", True, WHITE)
    SCREEN.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - CELL_H * 4)))

    prompt = TEXT_FONT.render("Armin has been caught, and is asked whether he wishes to be thrown to the sea or mountain", True, WHITE)
    SCREEN.blit(prompt, prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 - CELL_H * 2)))

    for i, option in enumerate(["Mountain", "Sea"]):
        prefix = "> " if i == selection else "  "
        color = Armin_COLOR if i == selection else WHITE
        text = TEXT_FONT.render(prefix + option, True, color)
        SCREEN.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + i * CELL_H * 2)))

    hint = TEXT_FONT.render("Use Up/Down and Enter", True, WHITE)
    SCREEN.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + CELL_H * 5)))


def draw_sanity_game_over_screen():
    SCREEN.fill(BLACK)
    title = TEXT_FONT.render("GAME OVER", True, WHITE)
    SCREEN.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - CELL_H * 4)))

    prompt = TEXT_FONT.render("Armin has lost sanity for killing too many MØØSE. The game is over.", True, WHITE)
    SCREEN.blit(prompt, prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 - CELL_H * 2)))

    text = TEXT_FONT.render("> Quit", True, Armin_COLOR)
    SCREEN.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

    hint = TEXT_FONT.render("Press Enter or Q", True, WHITE)
    SCREEN.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + CELL_H * 4)))


def draw_win_screen():
    SCREEN.fill(BLACK)
    title = TEXT_FONT.render("YOU HAVE WON!", True, WHITE)
    SCREEN.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - CELL_H)))

    hint = TEXT_FONT.render("Press Q to quit", True, WHITE)
    SCREEN.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + CELL_H * 2)))


def draw_tutorial():
    messages = [
        "Use WAD to move and J to attack",
        "Game is over if health or sanity is 0",
    ]
    for i, message in enumerate(messages):
        SCREEN.blit(TEXT_FONT.render(message, True, BLUE), (WIDTH//3,  HEIGHT//2 + i * CELL_H * 2))


def load_start_menu_background(filename="bg.png"): 
    try:
        image = pygame.image.load(filename).convert()
    except pygame.error:
        return None

    img_w, img_h = image.get_size()
    scale = max(WIDTH / img_w, HEIGHT / img_h)

    new_w = int(img_w * scale)
    new_h = int(img_h * scale)

    image = pygame.transform.smoothscale(image, (new_w, new_h))

    x = (WIDTH - new_w) // 2
    y = (HEIGHT - new_h) // 2

    final_bg = pygame.Surface((WIDTH, HEIGHT))
    final_bg.blit(image, (x, y))
    return final_bg

def draw_start_menu(selection):
    if START_MENU_BG:
        SCREEN.blit(START_MENU_BG, (0, 0))
    else:
        SCREEN.fill(BLACK)

    title = TEXT_FONT.render("The Seven(minus 4) Labors of Armin", True, RED)
    SCREEN.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - CELL_H * 5)))

    for i, option in enumerate(["Start", "Quit"]):
        prefix = "> " if i == selection else "  "
        color = Armin_COLOR if i == selection else WHITE
        text = TEXT_FONT.render(prefix + option, True, color)
        SCREEN.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + i * CELL_H * 2)))

    hint = TEXT_FONT.render("\"please ignore the background\"", True, WHITE)
    SCREEN.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + CELL_H * 5)))


def run_start_menu():
    selection = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    selection = (selection - 1) % 2
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    selection = (selection + 1) % 2
                elif event.key == pygame.K_RETURN:
                    if selection == 0:
                        return
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
        draw_start_menu(selection)
        pygame.display.flip()
        CLOCK.tick(FPS)


def draw_frame(level_index=None):
    SCREEN.blit(BACKGROUND, (0, 0))
    draw_ground()
    Teleport.draw()
    Armin.draw()
    D.draw()
    Bullet.draw()
    Zombie.draw()
    Moose.draw()
    Armin.draw_health()
    D.draw_boss_ui()
    if level_index == 0:
        draw_tutorial()


def main():
    global CURRENT_LEVEL_INDEX, CURRENT_LEVEL, TEXT_DATA, PLAYED_LEVEL3, LEVEL3_FIRST_ENTRY_ACTIVE, PLAYED_D_DIALOG, START_MENU_BG
    CURRENT_LEVEL_INDEX = 0
    PLAYED_LEVEL3 = False
    LEVEL3_FIRST_ENTRY_ACTIVE = False
    PLAYED_D_DIALOG = False

    load_level(CURRENT_LEVEL_INDEX)
    TEXT_DATA = load_json("text.json")
    reset_current_level()

    START_MENU_BG = load_start_menu_background("bg.png")
    run_start_menu()

    run_text_sequence(TEXT_DATA.get("intro", [])) #the intro message

    game_over_mode = None
    game_over_selection = 0
    special_game_over_black_seen = False
    game_won = False

    while True: 
    #main game loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if game_over_mode in ("health", "special"):  
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        game_over_selection = (game_over_selection - 1) % 2
                    elif event.key == pygame.K_DOWN:
                        game_over_selection = (game_over_selection + 1) % 2
                    elif event.key == pygame.K_RETURN:
                        if game_over_selection == 0: #restart level
                            reset_current_level()

                            if CURRENT_LEVEL_INDEX == 2:#see if this is the first time level 3 is loaded
                                LEVEL3_FIRST_ENTRY_ACTIVE = False
                            game_over_mode = None

                        else:
                            pygame.quit()
                            sys.exit()

            elif game_over_mode == "sanity":
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_q):
                    pygame.quit()
                    sys.exit()

            elif game_won: 
                if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

        if game_over_mode == "health":
            draw_health_game_over_screen(game_over_selection)
        elif game_over_mode == "special":
            draw_level3_game_over_screen(game_over_selection)
        elif game_over_mode == "sanity":
            draw_sanity_game_over_screen()
        elif game_won:
            draw_win_screen()
        else: #game is not over
            if CURRENT_LEVEL_INDEX == 2 and not PLAYED_LEVEL3:
                run_level3_intro()
                PLAYED_LEVEL3 = True

            if D.dialog_pending: #the dialog when the boss is killed for the first time
                run_level3_dialog()

            #process everyone
            Armin.update()
            D.update()
            Bullet.update()
            Level3ZombieSpawner.update()
            Zombie.update()
            Moose.update()

            if Armin.health <= 0 or Armin.sanity <= 0: # the game is over
                if D.has_regenerated_hp:
                    if not special_game_over_black_seen: #the game over text squence is shown only once
                        special_game_over_black_seen = True
                        run_text_sequence(TEXT_DATA.get("black", []))

                    game_over_mode = "special" 
                    game_over_selection = 0
                    draw_level3_game_over_screen(game_over_selection) 

                elif Armin.health <= 0:
                    game_over_mode = "health"
                    game_over_selection = 0
                    draw_health_game_over_screen(game_over_selection)

                else:
                    game_over_mode = "sanity"
                    draw_sanity_game_over_screen()
            #all good; the game goes on
            elif Teleport.touched_by_player():
                if not advance_level(): #are there any levels left?
                    game_won = True
                    draw_win_screen()
                else:
                    if CURRENT_LEVEL_INDEX == 2:
                        PLAYED_LEVEL3 = False
                        LEVEL3_FIRST_ENTRY_ACTIVE = True
                    draw_frame(CURRENT_LEVEL_INDEX)
            else:
                draw_frame(CURRENT_LEVEL_INDEX)

        pygame.display.flip() #flip the secondary display buffer to primary display buffer to show it on the screen
        CLOCK.tick(FPS)       


if __name__ == "__main__":
    main()
