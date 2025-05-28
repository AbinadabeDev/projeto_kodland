import pgzrun
import sys
import random
from pygame import Rect

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pgzero.builtins import Actor, keyboard, sounds, music, screen, mouse

    def draw(): pass

    def update(dt): pass

WIDTH = 800
HEIGHT = 600
TITLE = "Coletor Minimalista"

COLORS = {
    'bg': (30, 30, 50),
    'btn': (70, 70, 90),
    'btn_hover': (100, 100, 120),
    'text': (200, 200, 220),
    'title': (150, 150, 255),
    'score_text': (220, 220, 100),
    'over': (50, 0, 0),
    'over_text': (255, 100, 100)
}

HERO_SPEED = 200.0
ENEMY_SPEED = 100.0
CRYSTAL_ANIM_SPEED = 0.2
DEFAULT_ANIM_SPEED = 0.15

game_state = 'menu'
music_on = True
mouse_pos = (0, 0)

hero = None
enemies = []
crystal = None
score = 0

btn_w, btn_h, btn_s = 200, 50, 20
c_x = WIDTH // 2
s_y = HEIGHT // 2 - btn_h // 2
start_btn = Rect(c_x - btn_w // 2, s_y - btn_h - btn_s // 2, btn_w, btn_h)
music_btn = Rect(c_x - btn_w // 2, s_y, btn_w, btn_h)
exit_btn = Rect(c_x - btn_w // 2, s_y + btn_h + btn_s // 2, btn_w, btn_h)

class AnimActor:
    def __init__(self, pos, anims, anim_speed=DEFAULT_ANIM_SPEED):
        self.anims = {k: v for k, v in anims.items() if v}
        if not self.anims:
            self.anims = {'active': ['default_image']}
            self.current_anim_state = 'active'
        else:
            self.current_anim_state = next(iter(self.anims.keys()))
            if 'active' in self.anims:
                self.current_anim_state = 'active'

        self.f_idx = 0
        self.a_timer = 0.0
        self.a_speed = anim_speed

        if self.current_anim_state not in self.anims or not self.anims[self.current_anim_state]:
            valid_fallback_state = None
            for state_name, frames in self.anims.items():
                if frames:
                    valid_fallback_state = state_name
                    break
            if valid_fallback_state:
                self.current_anim_state = valid_fallback_state
            else:
                self.anims['active'] = ['default_image']
                self.current_anim_state = 'active'

        self.img = self.anims[self.current_anim_state][0]

        try:
            self.actor = Actor(self.img, pos)
        except Exception as e:
            try:
                self.actor = Actor('default_image', pos)
            except Exception as e_fallback:
                print(f"ERRO FATAL: Falha ao carregar 'default_image'. Verifique a pasta 'images'. {e_fallback}")
                sys.exit()

    def update_anim(self, dt):
        frames = self.anims.get(self.current_anim_state, [])
        if not frames:
            return
        self.a_timer += dt
        if self.a_timer >= self.a_speed:
            self.a_timer %= self.a_speed
            self.f_idx = (self.f_idx + 1) % len(frames)
            img_name = frames[self.f_idx]
            try:
                self.actor.image = img_name
            except Exception as e:
                self.actor.image = 'default_image'

    def set_anim_state(self, new_state_name):
        if new_state_name != self.current_anim_state and new_state_name in self.anims:
            self.current_anim_state = new_state_name
            self.f_idx = 0
            self.a_timer = 0.0
            img_name = self.anims[self.current_anim_state][0]
            try:
                self.actor.image = img_name
            except Exception as e:
                self.actor.image = 'default_image'

    def draw(self):
        self.actor.draw()

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

class Hero(AnimActor):
    def __init__(self, pos):
        anims = {
            'active': ['hero_anim_0', 'hero_anim_1']
        }
        super().__init__(pos, anims, anim_speed=DEFAULT_ANIM_SPEED)

    def update(self, dt):
        dx = 0
        dy = 0
        if keyboard.left:
            dx = -HERO_SPEED
        elif keyboard.right:
            dx = HERO_SPEED
        if keyboard.up:
            dy = -HERO_SPEED
        elif keyboard.down:
            dy = HERO_SPEED

        self.x += dx * dt
        self.y += dy * dt

        self.actor.left = max(0, self.actor.left)
        self.actor.right = min(WIDTH, self.actor.right)
        self.actor.top = max(0, self.actor.top)
        self.actor.bottom = min(HEIGHT, self.actor.bottom)

        self.update_anim(dt)

class Enemy(AnimActor):
    def __init__(self, pos, patrol_limit_y, patrol_bounds_x):
        anims = {
            'active': ['guard_anim_0', 'guard_anim_1']
        }
        super().__init__(pos, anims, anim_speed=DEFAULT_ANIM_SPEED)
        self.actor.y = patrol_limit_y
        self.patrol_bounds_x = patrol_bounds_x
        self.vx = ENEMY_SPEED if random.choice([True, False]) else -ENEMY_SPEED

    def update(self, dt,
               hero_actor=None):
        self.x += self.vx * dt

        if self.vx > 0 and self.actor.right >= self.patrol_bounds_x[1]:
            self.actor.right = self.patrol_bounds_x[1]
            self.vx *= -1
        elif self.vx < 0 and self.actor.left <= self.patrol_bounds_x[0]:
            self.actor.left = self.patrol_bounds_x[0]
            self.vx *= -1

        self.update_anim(dt)
        return True

class Crystal(AnimActor):
    def __init__(self, pos):
        anims = {
            'active': ['crystal_anim_0', 'crystal_anim_1']
        }
        super().__init__(pos, anims, anim_speed=CRYSTAL_ANIM_SPEED)

    def update(self, dt):
        self.update_anim(dt)

    def respawn(self):
        margin = 50
        self.actor.x = random.randint(margin, WIDTH - margin)
        self.actor.y = random.randint(margin, HEIGHT - margin)

def play_sound(sound_name):
    global music_on
    if music_on:
        try:
            sound_to_play = getattr(sounds, sound_name, None)
            if sound_to_play:
                sound_to_play.play()

        except Exception as e:
            print(f"Erro ao tocar som {sound_name}: {e}")

def stop_background_music():
    try:
        music.stop()
    except Exception as e:
        print(f"Erro ao parar música: {e}")

def play_background_music():
    global music_on
    if music_on:
        try:
            music.play("background_loop")
            music.set_volume(0.3)
        except Exception as e:
            print(f"Erro ao tocar música de fundo: {e}. Verifique 'music/background_loop.ogg' ou '.wav'.")
    else:
        stop_background_music()

def toggle_music():
    global music_on
    music_on = not music_on
    if music_on:
        play_background_music()
    else:
        stop_background_music()

def setup_game():
    global hero, enemies, crystal, score, game_state

    enemies = []
    score = 0

    try:
        hero = Hero((WIDTH // 2, HEIGHT - 50))
    except Exception as e:
        print(f"ERRO FATAL ao criar Herói: {e}. Verifique se as imagens existem! Saindo.")
        sys.exit()

    try:
        guard_y_pos = HEIGHT // 2
        patrol_x_limits = (50, WIDTH - 50)
        enemies.append(Enemy((WIDTH // 2, guard_y_pos), guard_y_pos, patrol_x_limits))
    except Exception as e:
        print(f"Erro ao criar Guarda: {e}. Verifique se as imagens existem.")

    try:
        crystal = Crystal((0, 0))
        crystal.respawn()
    except Exception as e:
        print(f"ERRO FATAL ao criar Cristal: {e}. Verifique se as imagens existem! Saindo.")
        sys.exit()

    game_state = 'playing'
    play_background_music()

def draw_text(text, pos, size=30, color_key='text', center=False):
    text_args = {'color': COLORS[color_key], 'fontsize': size}
    if center:
        text_args['center'] = pos
    else:
        text_args['topleft'] = pos
    screen.draw.text(text, **text_args)

def draw_menu():
    screen.fill(COLORS['bg'])
    draw_text("Coletor Minimalista", (c_x, HEIGHT // 4), size=50, color_key='title', center=True)
    buttons = [
        (start_btn, "Iniciar Jogo"),
        (music_btn, f"Música: {'Ligada' if music_on else 'Desligada'}"),
        (exit_btn, "Sair")
    ]
    for r, t in buttons:
        color_key = 'btn_hover' if r.collidepoint(mouse_pos) else 'btn'
        screen.draw.filled_rect(r, COLORS[color_key])
        draw_text(t, r.center, center=True, size=24)

def draw_game():
    screen.fill(COLORS['bg'])

    if crystal:
        crystal.draw()
    if hero:
        hero.draw()
    for e in enemies:
        e.draw()

    draw_text(f"Cristais: {score}", (10, 10), size=30, color_key='score_text')

def draw_end_screen(message, title_color_key, bg_color_key):
    screen.fill(COLORS[bg_color_key])
    draw_text(message, (c_x, HEIGHT // 3), size=80, color_key=title_color_key, center=True)
    draw_text("Pressione ESPAÇO para voltar ao Menu", (c_x, HEIGHT * 2 / 3), size=26, center=True)

def draw():
    if game_state == 'menu':
        draw_menu()
    elif game_state == 'playing':
        draw_game()
    elif game_state == 'game_over':
        draw_end_screen("GAME OVER", 'over_text', 'over')

def update(dt):
    global game_state, score, hero, enemies, crystal

    if game_state == 'playing':
        if hero:
            hero.update(dt)

        if crystal:
            crystal.update(dt)

        for e in enemies:
            e.update(dt)

        if hero and crystal:
            if hero.rect.colliderect(crystal.rect):
                score += 1
                play_sound('collect')
                crystal.respawn()

        if hero:
            for guard in enemies:
                if hero.rect.colliderect(guard.rect):
                    play_sound('game_over_sfx')
                    stop_background_music()
                    game_state = 'game_over'
                    break

    elif game_state == 'game_over':
        if keyboard.space:
            game_state = 'menu'
            hero, enemies, crystal, score = None, [], None, 0

def on_mouse_move(pos):
    global mouse_pos
    mouse_pos = pos

def on_mouse_down(pos, button):
    global game_state
    if game_state == 'menu' and button == mouse.LEFT:
        if start_btn.collidepoint(pos):
            play_sound('button_click')
            setup_game()
        elif music_btn.collidepoint(pos):
            play_sound('button_click')
            toggle_music()
        elif exit_btn.collidepoint(pos):
            play_sound('button_click')
            sys.exit()

try:
    pgzrun.go()
except Exception as e:
    print(f"\n--- ERRO AO EXECUTAR O JOGO ---")
    print(f"{e}")
    print("Verifique se Pygame Zero está instalado ('pip install pgzero')")
    print("e se as pastas 'images', 'music', 'sounds' existem com os arquivos necessários.")
    if "Resource not found" in str(e) or "No such file or directory" in str(e):
        print("-> Isso pode ser um arquivo de imagem ou som faltando, ou a pasta não existe.")
        print("-> Certifique-se que 'images/default_image.png' existe.")
    elif "on_mouse_move() hook accepts no parameter" in str(e) or "on_mouse_down() hook accepts no parameter" in str(e):
        print(
            "-> Verifique os nomes dos parâmetros nas funções on_mouse_move (deve ser 'pos') e on_mouse_down (deve ser 'pos', 'button').")
    input("Pressione Enter para sair.")