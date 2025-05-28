# robot_platformer_optimized.py
import pgzrun, sys, math, random
from pygame import Rect

# --- Constants & Config ---
WIDTH, HEIGHT = 800, 600
TITLE = "Robô Plataformer Sci-Fi (Otimizado)"
COLORS = {
    'bg': (30, 30, 50), 'btn': (70, 70, 90), 'btn_hover': (100, 100, 120),
    'text': (200, 200, 220), 'title': (150, 150, 255), 'platform': (100, 150, 100),
    'victory': (100, 255, 100), 'over': (50, 0, 0), 'over_text': (255, 100, 100)
}
GRAVITY, JUMP, MAX_FALL, P_SPEED, E_BOUNCE = 0.5, -10, 10, 7, -5
HERO_SPEED, HERO_HEALTH = 5, 3
ENEMY_HEALTH = 1

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

# --- Base Animated Class (Shell for now, will be fleshed out) ---
class AnimActor:
    def __init__(self, pos, anims, speed=0.1):
        # Placeholder for actual Actor creation and animation logic
        # For now, we'll simulate its position and basic drawing
        self.x, self.y = pos
        self.width, self.height = 32, 32 # Default size
        self.actor = Actor('robot_idle_0', pos) # Placeholder image

    def draw(self):
        # screen.draw.rect(Rect(self.x - self.width/2, self.y - self.height/2, self.width, self.height), (255,0,0))
        self.actor.draw() # Pygame Zero Actor's draw

    @property
    def pos(self): return self.actor.pos
    @pos.setter
    def pos(self, v): self.actor.pos = v
    @property
    def rect(self): return self.actor.rect # Pygame Zero Actor's rect


# --- Audio Functions ---
def play_sound(name):
    try:
        sound = getattr(sounds, name, None)
        if sound and music_on:
            sound.play()
    except Exception as e:
        print(f"Error playing sound {name}: {e}. Make sure '{name}.wav' or '.ogg' is in sounds folder.")

def stop_background_music():
    try:
        music.stop()
    except Exception as e:
        print(f"Error stopping music: {e}")

def play_background_music():
    if music_on:
        try:
            music.play("background") # Assumes 'background.mp3' or '.ogg' in music folder
            music.set_volume(0.3)
        except Exception as e:
            print(f"Error playing background music: {e}. Check music/background.ogg/wav")
    else:
        stop_background_music()

def toggle_music():
    global music_on
    music_on = not music_on
    play_sound('button_click') # Assuming you have a button_click sound
    if music_on:
        play_background_music()
    else:
        stop_background_music()

# --- Game Setup (Shell for now) ---
def setup_game():
    global game_state, hero, platforms, enemies, projectiles
    print("Setting up game...") # Placeholder
    # hero = ...
    # platforms = [...]
    # enemies = [...]
    projectiles = []
    game_state = 'playing'
    play_background_music()


# --- Draw Functions ---
def draw_text(text, pos, size=30, color='text', center=False):
    args = {'fontsize': size, 'color': COLORS[color]}
    if center: args['center'] = pos
    else: args['topleft'] = pos
    try:
        screen.draw.text(text, **args, fontname="dejavusans") # Using a common sans-serif font
    except Exception as e:
        screen.draw.text(text, **args) # Fallback to default font
        print(f"Font error, using default: {e}")


def draw_menu():
    screen.fill(COLORS['bg'])
    draw_text(TITLE, (c_x, HEIGHT // 4), size=60, color='title', center=True)
    buttons = [(start_btn, "Iniciar Jogo"), (music_btn, f"Música: {'Ligada' if music_on else 'Desligada'}"), (exit_btn, "Sair")]
    for r, t in buttons:
        color = COLORS['btn_hover'] if r.collidepoint(mouse_pos) else COLORS['btn']
        screen.draw.filled_rect(r, color)
        draw_text(t, r.center, size=24, center=True)

def draw_game(): # Placeholder
    screen.fill(COLORS['bg'])
    draw_text("Jogo em Andamento...", (WIDTH // 2, HEIGHT // 2), center=True)

def draw_end_screen(message, title_color, bg_color): # Placeholder
    screen.fill(COLORS[bg_color])
    draw_text(message, (c_x, HEIGHT // 3), size=80, color=title_color, center=True)
    draw_text("Pressione ESPAÇO para voltar ao Menu", (c_x, HEIGHT * 2 / 3), center=True)

def draw():
    if game_state == 'menu': draw_menu()
    elif game_state == 'playing': draw_game() # Placeholder call
    elif game_state == 'game_over': draw_end_screen("GAME OVER", 'over_text', 'over')
    elif game_state == 'victory': draw_end_screen("VITÓRIA!", 'victory', 'bg')

# --- Update Function ---
def update(dt):
    global game_state
    if game_state == 'playing':
        pass # Hero/enemy update logic will go here
    elif game_state in ['game_over', 'victory']:
        if keyboard.space:
            game_state = 'menu'
            # Potentially stop sounds from previous state if any looping
            # play_background_music() # Or wait for menu to decide

# --- Input Handlers ---
def on_mouse_move(pos):
    global mouse_pos
    mouse_pos = pos

def on_mouse_down(pos, button):
    global game_state
    if game_state == 'menu' and button == mouse.LEFT:
        if start_btn.collidepoint(pos):
            play_sound('button_click')
            setup_game() # Will transition to 'playing' state
        elif music_btn.collidepoint(pos):
            # play_sound('button_click') # toggle_music already plays it
            toggle_music()
        elif exit_btn.collidepoint(pos):
            play_sound('button_click')
            sys.exit()

# --- Run ---
# print("Instructions: Ensure images/sounds folders exist. Default image 'robot_idle_0.png' needed for AnimActor.")
# print("Sounds like 'button_click.wav' and music 'background.ogg' or '.wav' might be attempted.")
pgzrun.go()