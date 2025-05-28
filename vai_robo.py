# robot_platformer_optimized.py
import sys, math, random
import pgzero
import pgzero.runner
# Inicializa o Pygame Zero
pgzero.runner.prepare_mod(sys.modules[__name__])
from pygame import Rect

# --- Constants & Config ---
import pygame
WIDTH, HEIGHT = 800, 600
SCREEN_RECT = pygame.Rect(0, 0, WIDTH, HEIGHT)
TITLE = "Robô Plataformer Sci-Fi (Otimizado)"
COLORS = {
    'bg': (30, 30, 50), 'btn': (70, 70, 90), 'btn_hover': (100, 100, 120),
    'text': (200, 200, 220), 'title': (150, 150, 255), 'platform': (100, 150, 100),
    'victory': (100, 255, 100), 'over': (50, 0, 0), 'over_text': (255, 100, 100)
}
GRAVITY, JUMP, MAX_FALL, P_SPEED, E_BOUNCE = 0.5, -10, 10, 7, -5  # E_BOUNCE, P_SPEED not used yet
HERO_SPEED, HERO_HEALTH = 5, 3
ENEMY_HEALTH = 1  # Not used yet

# --- Global State ---
game_state = 'menu'
music_on = True
mouse_pos = (0, 0)
hero, enemies, platforms, projectiles = None, [], [], []

# --- Menu Buttons ---
btn_w, btn_h, btn_s = 200, 50, 20
c_x, s_y = WIDTH // 2, HEIGHT // 2 - btn_h // 2
start_btn = Rect(c_x - btn_w // 2, s_y - btn_h - btn_s // 2, btn_w, btn_h)
music_btn = Rect(c_x - btn_w // 2, s_y, btn_w, btn_h)
exit_btn = Rect(c_x - btn_w // 2, s_y + btn_h + btn_s // 2, btn_w, btn_h)


# --- Base Animated Class ---
class AnimActor:
    def __init__(self, pos, anims, speed=0.1):
        self.anims = {k: v for k, v in anims.items() if v}
        self.state = 'idle' if 'idle' in self.anims else next(iter(self.anims.keys()))
        self.f_idx, self.a_timer, self.a_speed = 0, 0.0, speed
        # Ensure 'default_image.png' exists or use a valid existing image
        self.img = self.anims.get(self.state, ['default_image'])[0]
        try:
            self.actor = Actor(self.img, pos)
        except Exception as e:
            print(f"Error loading image {self.img} for AnimActor: {e}. Using 'default_image'.")
            try:
                self.actor = Actor('default_image', pos)  # Fallback image
            except Exception as fallback_e:
                print(f"FATAL: Default image 'default_image.png' also missing: {fallback_e}")
                sys.exit()  # Or handle more gracefully
        self.facing_right = True

    def update_anim(self, dt):
        frames = self.anims.get(self.state, [])
        if not frames: return
        self.a_timer += dt
        if self.a_timer >= self.a_speed:
            self.a_timer = 0.0
            self.f_idx = (self.f_idx + 1) % len(frames)
            try:
                self.actor.image = frames[self.f_idx]
            except Exception as e:
                print(f"Error loading animation frame {frames[self.f_idx]}: {e}")
                self.actor.image = 'default_image'  # Fallback

    def set_state(self, new_state):
        eff_state = new_state
        if new_state in ['run', 'walk'] and not self.facing_right and new_state + '_left' in self.anims:
            eff_state = new_state + '_left'

        if eff_state != self.state and eff_state in self.anims:
            self.state = eff_state
            self.f_idx, self.a_timer = 0, 0.0
            img_name = self.anims[self.state][0]
            try:
                self.actor.image = img_name
            except Exception as e:
                print(f"Error setting state image {img_name}: {e}")
                self.actor.image = 'default_image'

    def draw(self):
        self.actor.draw()

    @property
    def pos(self):
        return self.actor.pos

    @pos.setter
    def pos(self, v):
        self.actor.pos = v

    @property
    def x(self):
        return self.actor.x

    @x.setter
    def x(self, v):
        self.actor.x = v

    @property
    def y(self):
        return self.actor.y

    @y.setter
    def y(self, v):
        self.actor.y = v

    @property
    def rect(self):
        return self.actor.rect

    @property
    def width(self):
        return self.actor.width

    @property
    def height(self):
        return self.actor.height


# --- Hero Class ---
class Hero(AnimActor):
    def __init__(self, pos):
        anims = {
            'idle': ['robot_idle_0', 'robot_idle_1'],
            'run': ['robot_run_0', 'robot_run_1', 'robot_run_2'],
            'jump': ['robot_jump_0'],
            'fall': ['robot_fall_0'],
            'hurt': ['robot_hurt_0']  # Will be used later
        }
        # Ensure these images exist in 'images' folder (e.g., 'robot_idle_0.png')
        super().__init__(pos, anims, speed=0.1)
        self.vx, self.vy, self.on_ground = 0, 0, False
        self.health, self.invul_timer = HERO_HEALTH, 0.0  # invul_timer not fully used yet

    def update(self, dt, current_platforms, current_enemies):  # enemies not used yet
        # Basic hurt state handling (will be expanded)
        if self.state == 'hurt':
            # For now, just update animation, actual hurt logic later
            self.update_anim(dt)
            # Add gravity during hurt if needed, or simple recovery timer
            if self.a_timer >= self.a_speed * len(self.anims.get('hurt', [])):
                self.set_state('idle')  # Recover after animation
            return

        # Movement Input
        if keyboard.left:
            self.vx, self.facing_right = -HERO_SPEED, False
        elif keyboard.right:
            self.vx, self.facing_right = HERO_SPEED, True
        else:
            self.vx = 0

        if self.on_ground:
            self.set_state('run' if self.vx != 0 else 'idle')

        # Vertical Movement & Jump
        self.vy = min(self.vy + GRAVITY, MAX_FALL)
        if keyboard.space and self.on_ground:
            self.vy, self.on_ground = JUMP, False
            play_sound('jump')  # Assuming 'jump.wav' or '.ogg'
            self.set_state('jump')

        if not self.on_ground:
            self.set_state('jump' if self.vy < 0 else 'fall')

        # Apply Movement & Collisions
        self.x += self.vx
        for p in current_platforms:  # Horizontal Collision
            if self.rect.colliderect(p):
                if self.vx > 0:
                    self.actor.right = p.left
                elif self.vx < 0:
                    self.actor.left = p.right
                self.vx = 0  # Stop horizontal movement on collision
                break

        self.y += self.vy
        self.on_ground = False  # Assume not on ground until collision check
        for p in current_platforms:  # Vertical Collision
            if self.rect.colliderect(p):
                if self.vy > 0 and self.actor.bottom <= p.top + self.vy + 1:  # Landing on top
                    self.actor.bottom = p.top
                    self.vy = 0
                    self.on_ground = True
                    self.set_state('idle' if self.vx == 0 else 'run')
                elif self.vy < 0 and self.actor.top >= p.bottom + self.vy - 1:  # Hitting bottom of platform
                    self.actor.top = p.bottom
                    self.vy = 0  # Stop upward movement
                # If still colliding after adjustment (e.g. stuck in side), this needs more robust resolution
                # For now, this basic check should work for typical platformer scenarios
                break  # Process one platform collision at a time vertically

        # Screen Bounds
        self.actor.left = max(0, self.actor.left)
        self.actor.right = min(WIDTH, self.actor.right)
        if self.actor.top > HEIGHT + 50:  # Fell off screen
            self.take_damage(999)  # Placeholder for instant death

        self.update_anim(dt)

    def take_damage(self, amount):  # Basic version
        global game_state
        if self.health > 0:  # Not truly invulnerable yet
            self.health -= amount
            play_sound('hero_hurt')  # Assuming 'hero_hurt.wav'
            if self.health <= 0:
                self.die()
            else:
                # A simple visual cue or temporary state change
                self.set_state('hurt')  # Animation will play
                # self.invul_timer = 1.5 # Will be used for opacity/flashing later
                # self.vy = -3 # Slight bounce
                # self.on_ground = False

    def die(self):
        global game_state
        game_state = 'game_over'
        stop_background_music()
        play_sound('game_over')  # Assuming 'game_over.wav'


# --- Audio Functions ---
def play_sound(name):
    try:
        sound = getattr(sounds, name, None)
        if sound and music_on: sound.play()
    except Exception as e:
        print(f"Error playing sound {name}: {e}")


def stop_background_music():
    try:
        music.stop()
    except Exception as e:
        print(f"Error stopping music: {e}")


def play_background_music():
    if music_on:
        try:
            music.play("background");
            music.set_volume(0.3)
        except Exception as e:
            print(f"Error music: {e}. Check music/background.ogg/wav")
    else:
        stop_background_music()


def toggle_music():
    global music_on;
    music_on = not music_on
    play_sound('button_click')
    play_background_music() if music_on else stop_background_music()


# --- Game Setup ---
def setup_game():
    global hero, enemies, platforms, projectiles, game_state
    enemies, projectiles = [], []  # Enemies will be added in next commit

    # Define image names for hero, ensure they exist in 'images/'
    # e.g., 'robot_idle_0.png', 'robot_run_0.png', etc.
    # A 'default_image.png' is also good as a fallback for AnimActor.
    try:
        hero = Hero((WIDTH // 4, HEIGHT - 80))
    except Exception as e:
        print(f"FATAL Hero Error: {e}. Check hero images and 'default_image.png'! Exiting.")
        sys.exit()

    platforms = [
        Rect(0, HEIGHT - 40, WIDTH, 40), Rect(200, HEIGHT - 150, 150, 20),
        Rect(450, HEIGHT - 250, 100, 20), Rect(WIDTH - 300, HEIGHT - 120, 150, 20),
        Rect(50, HEIGHT - 350, 100, 20)
    ]
    game_state = 'playing'
    play_background_music()


# --- Draw Functions ---
def draw_text(text, pos, size=30, color='text', center=False):
    args = {'fontsize': size, 'color': COLORS[color]}
    if center:
        args['center'] = pos
    else:
        args['topleft'] = pos
    try:
        screen.draw.text(text, **args, fontname="dejavusans")
    except:
        screen.draw.text(text, **args)  # Fallback


def draw_menu():
    screen.fill(COLORS['bg'])
    draw_text(TITLE, (c_x, HEIGHT // 4), size=60, color='title', center=True)
    buttons = [(start_btn, "Iniciar Jogo"), (music_btn, f"Música: {'Ligada' if music_on else 'Desligada'}"),
               (exit_btn, "Sair")]
    for r, t in buttons:
        color = COLORS['btn_hover'] if r.collidepoint(mouse_pos) else COLORS['btn']
        screen.draw.filled_rect(r, color)
        draw_text(t, r.center, size=24, center=True)


def draw_game():
    screen.fill(COLORS['bg'])
    for p in platforms: screen.draw.filled_rect(p, COLORS['platform'])
    if hero: hero.draw()
    # for e in enemies: e.draw() # Enemies drawn in next commit
    # for p in projectiles: p.draw() # Projectiles drawn later
    if hero: draw_text(f"Vida: {hero.health}", (10, 10))
    # draw_text(f"Inimigos: {len(enemies)}", (WIDTH - 150, 10)) # For next commit


def draw_end_screen(message, title_color, bg_color):
    screen.fill(COLORS[bg_color])
    draw_text(message, (c_x, HEIGHT // 3), size=80, color=title_color, center=True)
    draw_text("Pressione ESPAÇO para voltar ao Menu", (c_x, HEIGHT * 2 / 3), center=True)


def draw():
    if game_state == 'menu':
        draw_menu()
    elif game_state == 'playing':
        draw_game()
    elif game_state == 'game_over':
        draw_end_screen("GAME OVER", 'over_text', 'over')
    elif game_state == 'victory':
        draw_end_screen("VITÓRIA!", 'victory', 'bg')


# --- Update Function ---
def update(dt):
    global projectiles, enemies, game_state  # projectiles, enemies for later
    if game_state == 'playing':
        if hero: hero.update(dt, platforms, enemies)  # Pass empty enemies list for now
        # enemies_alive = [e for e in enemies if e.update(dt, hero.actor if hero else None)] # For next commit
        # enemies = enemies_alive
        # projectiles = [p for p in projectiles if p.update(dt, platforms)] # Projectile update later
        # Check win/lose conditions related to enemies/projectiles later
    elif game_state in ['game_over', 'victory'] and keyboard.space:
        game_state = 'menu'
        # Consider resetting hero health/pos if restarting from menu requires it
        # setup_game() # Could call setup_game again, or have a lighter menu transition


# --- Input Handlers ---
def on_mouse_move(pos): global mouse_pos; mouse_pos = pos


def on_mouse_down(pos, button):
    global game_state
    if game_state == 'menu' and button == mouse.LEFT:
        if start_btn.collidepoint(pos):
            play_sound('button_click'); setup_game()
        elif music_btn.collidepoint(pos):
            toggle_music()  # Already plays sound
        elif exit_btn.collidepoint(pos):
            play_sound('button_click'); sys.exit()


# --- Run ---
# print("Instructions: Ensure images (robot_idle_0 etc, default_image) and sounds (jump, hero_hurt etc) folders exist.")
pgzrun.go()