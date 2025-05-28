import pgzrun
import sys
import random
from pygame import Rect

WIDTH = 800
HEIGHT = 600
TITLE = "Robô Plataformer (Requisitos Estritos)"

COLORS = {
    'bg': (30, 30, 50),
    'btn': (70, 70, 90),
    'btn_hover': (100, 100, 120),
    'text': (200, 200, 220),
    'title': (150, 150, 255),
    'platform': (100, 150, 100),
    'victory': (100, 255, 100),
    'over': (50, 0, 0),
    'over_text': (255, 100, 100)
}

GRAVITY = 1000.0
JUMP_STRENGTH = -500.0
MAX_FALL_SPEED = 600.0
HERO_SPEED = 250.0
PROJECTILE_SPEED = 400.0
ENEMY_BASE_SPEED = 100.0
ENEMY_STOMP_BOUNCE = -250.0

HERO_HEALTH = 3
ENEMY_HEALTH = 1
DEFAULT_ANIM_SPEED = 0.1

game_state = 'menu'
music_on = True
mouse_pos = (0, 0)
hero = None
enemies = []
platforms = []
projectiles = []

btn_w, btn_h, btn_s = 200, 50, 20
c_x = WIDTH // 2
s_y = HEIGHT // 2 - btn_h // 2
start_btn = Rect(c_x - btn_w // 2, s_y - btn_h - btn_s // 2, btn_w, btn_h)
music_btn = Rect(c_x - btn_w // 2, s_y, btn_w, btn_h)
exit_btn = Rect(c_x - btn_w // 2, s_y + btn_h + btn_s // 2, btn_w, btn_h)

class AnimActor:
    def __init__(self, pos, anims, speed=DEFAULT_ANIM_SPEED):
        self.anims = {k: v for k, v in anims.items() if v}
        if not self.anims:
            print("Aviso: Nenhuma animação válida fornecida. Usando 'default_image'.")
            self.anims = {'idle': ['default_image']}
            self.state = 'idle'
        elif 'idle' in self.anims:
            self.state = 'idle'
        else:
            self.state = next(iter(self.anims.keys()))

        self.f_idx = 0
        self.a_timer = 0.0
        self.a_speed = speed
        self.img = self.anims[self.state][0]
        try:
            # Assume que 'default_image.png' existe se self.img falhar
            self.actor = Actor(self.img, pos)
        except Exception as e:
            print(f"Erro ao carregar imagem inicial {self.img}: {e}. Usando 'default_image'.")
            try:
                self.actor = Actor('default_image', pos)
            except Exception as e_fallback:
                print(f"ERRO FATAL: Falha ao carregar 'default_image'. Verifique a pasta 'images'. {e_fallback}")
                sys.exit()
        self.facing_right = True

    def update_anim(self, dt):
        frames = self.anims.get(self.state, [])
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
                print(f"Erro ao carregar frame {img_name}: {e}. Usando 'default_image'.")
                self.actor.image = 'default_image'

    def set_state(self, new_state):
        eff_state = new_state
        if new_state in ['run', 'walk'] and not self.facing_right:
            left_state = new_state + '_left'
            if left_state in self.anims:
                eff_state = left_state

        if eff_state != self.state and eff_state in self.anims:
            self.state = eff_state
            self.f_idx = 0
            self.a_timer = 0.0
            img_name = self.anims[self.state][0]
            try:
                self.actor.image = img_name
            except Exception as e:
                print(f"Erro ao definir imagem do estado {img_name}: {e}. Usando 'default_image'.")
                self.actor.image = 'default_image'

    def draw(self):
        self.actor.draw()

    @property
    def x(self): return self.actor.x
    @x.setter
    def x(self, v): self.actor.x = v
    @property
    def y(self): return self.actor.y
    @y.setter
    def y(self, v): self.actor.y = v
    @property
    def rect(self): return self.actor.rect
    @property
    def height(self): return self.actor.height

class Hero(AnimActor):
    def __init__(self, pos):
        anims = {
            'idle': ['robot_idle_0', 'robot_idle_1'],
            'run': ['robot_run_0', 'robot_run_1', 'robot_run_2'],
            'jump': ['robot_jump_0'],
            'fall': ['robot_fall_0'],
            'hurt': ['robot_hurt_0']
        }
        super().__init__(pos, anims, speed=DEFAULT_ANIM_SPEED)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.health = HERO_HEALTH
        self.invul_timer = 0.0

    def update(self, dt, platforms, enemies_list):
        if self.invul_timer > 0:
            self.invul_timer -= dt
        opacity_factor = 0.5 if self.invul_timer > 0 and int(self.invul_timer * 10) % 2 == 0 else 1.0
        self.actor.opacity = opacity_factor

        if self.state == 'hurt':
            self.vy = min(self.vy + GRAVITY * dt, MAX_FALL_SPEED)
            self.y += self.vy * dt
            coll_plats = [p for p in platforms if self.rect.colliderect(p)]
            self.on_ground = any(self.actor.bottom <= p.top + abs(self.vy * dt) + 1 for p in coll_plats)
            if self.on_ground:
                self.actor.bottom = min(p.top for p in coll_plats)
                self.vy = 0
            anim_len = len(self.anims.get('hurt', []))
            if self.on_ground and self.a_timer >= self.a_speed * anim_len:
                self.set_state('idle')
            self.update_anim(dt)
            return

        if keyboard.left:
            self.vx = -HERO_SPEED
            self.facing_right = False
        elif keyboard.right:
            self.vx = HERO_SPEED
            self.facing_right = True
        else:
            self.vx = 0.0

        self.vy = min(self.vy + GRAVITY * dt, MAX_FALL_SPEED)
        if keyboard.space and self.on_ground:
            self.vy = JUMP_STRENGTH
            self.on_ground = False
            play_sound('jump')
            self.set_state('jump')

        if self.on_ground:
            self.set_state('run' if self.vx != 0 else 'idle')
        else:
            self.set_state('jump' if self.vy < 0 else 'fall')

        self.x += self.vx * dt
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vx > 0:
                    self.actor.right = p.left
                elif self.vx < 0:
                    self.actor.left = p.right
                self.vx = 0.0
                break

        self.y += self.vy * dt
        self.on_ground = False
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vy > 0 and self.actor.bottom <= p.top + abs(self.vy * dt) + 1:
                    self.actor.bottom = p.top
                    self.vy = 0.0
                    self.on_ground = True
                elif self.vy < 0 and self.actor.top >= p.bottom + self.vy * dt - 1:
                    self.actor.top = p.bottom
                    self.vy = 0.0
                break

        if self.invul_timer <= 0:
            for e in enemies_list:
                if self.rect.colliderect(e.rect):
                    is_stomp = self.vy > 0 and self.actor.bottom < e.actor.centery + 5
                    if is_stomp:
                        e.take_damage(1)
                        self.vy = ENEMY_STOMP_BOUNCE
                        self.on_ground = False
                        play_sound('stomp')
                    else:
                        self.take_damage(1)
                        break

        self.actor.left = max(0, self.actor.left)
        self.actor.right = min(WIDTH, self.actor.right)
        if self.actor.top > HEIGHT + 50:
            self.take_damage(999)

        self.update_anim(dt)

    def take_damage(self, amount):
        if self.invul_timer <= 0 and self.health > 0:
            self.health -= amount
            play_sound('hero_hurt')
            if self.health <= 0:
                self.die()
            else:
                self.set_state('hurt')
                self.invul_timer = 1.5
                self.vy = -150
                self.on_ground = False

    def die(self):
        global game_state
        if game_state != 'game_over':
            game_state = 'game_over'
            stop_background_music()
            play_sound('game_over')

class Enemy(AnimActor):
    def __init__(self, pos, limits):
        anims = {
            'idle': ['enemy_idle_0', 'enemy_idle_1'],
            'walk': ['enemy_walk_0', 'enemy_walk_1'],
            'shoot': ['enemy_shoot_0'],
            'hurt': ['enemy_hurt_0'],
            'die': ['enemy_die_0', 'enemy_die_1']
        }
        super().__init__(pos, anims, speed=random.uniform(0.1, 0.15))
        self.limits = limits
        self.speed = ENEMY_BASE_SPEED * random.uniform(0.8, 1.2)
        self.vx = self.speed if random.choice([True, False]) else -self.speed
        self.facing_right = self.vx > 0
        self.shoot_cd = random.uniform(1.5, 3.5)
        self.shoot_int = random.uniform(2.5, 4.5)
        self.detect_range = 300
        self.health = ENEMY_HEALTH
        self.dying = False
        self.death_timer = 0.5
        self.set_state('walk')

    def update(self, dt, hero_actor):
        if self.dying:
            self.set_state('die')
            self.update_anim(dt)
            self.death_timer -= dt
            return self.death_timer > 0

        if self.state == 'hurt':
            anim_len = len(self.anims.get('hurt', []))
            if self.a_timer >= self.a_speed * anim_len:
                self.set_state('walk')
                self.vx = self.speed if self.facing_right else -self.speed
            self.update_anim(dt)
            return True

        self.x += self.vx * dt
        if (self.vx > 0 and self.actor.right >= self.limits[1]) or \
           (self.vx < 0 and self.actor.left <= self.limits[0]):
            self.vx *= -1
            self.facing_right = self.vx > 0
            self.actor.right = min(self.actor.right, self.limits[1])
            self.actor.left = max(self.actor.left, self.limits[0])

        self.shoot_cd -= dt
        can_shoot = False
        if hero_actor and self.state != 'shoot':
            dx = hero_actor.x - self.x
            dy = abs(hero_actor.y - self.y)
            in_range = abs(dx) < self.detect_range and dy < self.height * 1.5
            facing_hero = (self.facing_right and dx > 0) or (not self.facing_right and dx < 0)
            if in_range and facing_hero:
                can_shoot = True

        if can_shoot and self.shoot_cd <= 0:
            self.shoot()
            self.shoot_cd = self.shoot_int
            self.set_state('shoot')
            self.vx = 0
        elif self.state == 'shoot':
            anim_len = len(self.anims.get('shoot', []))
            if self.a_timer >= self.a_speed * anim_len:
                self.vx = self.speed if self.facing_right else -self.speed

        if self.state not in ['shoot', 'hurt', 'die']:
            can_idle = 'idle' in self.anims
            if self.vx == 0 and can_idle:
                self.set_state('idle')
            elif self.vx != 0:
                self.set_state('walk')

        self.update_anim(dt)
        return True

    def shoot(self):
        play_sound('enemy_shoot')
        proj_vx = PROJECTILE_SPEED if self.facing_right else -PROJECTILE_SPEED
        start_x = self.actor.right if self.facing_right else self.actor.left
        start_y = self.actor.centery
        projectiles.append(Projectile((start_x, start_y), proj_vx))

    def take_damage(self, amount):
        if not self.dying:
            self.health -= amount
            play_sound('enemy_hurt')
            if self.health <= 0:
                self.die()
            else:
                self.set_state('hurt')
                self.vx = 0

    def die(self):
        if not self.dying:
            self.dying = True
            self.set_state('die')
            self.vx = 0
            play_sound('enemy_die')

class Projectile(Actor):
    def __init__(self, pos, vx):
        try:
            super().__init__('water_projectile', pos)
        except Exception as e:
            print(f"Erro ao carregar water_projectile: {e}. Usando 'default_image'.")
            super().__init__('default_image', pos)
        self.vx = vx
        self.life = 3.0

    def update(self, dt, platforms):
        self.x += self.vx * dt
        self.life -= dt
        collided_platform = any(self.colliderect(p) for p in platforms)
        return self.life > 0 and not collided_platform

def play_sound(name):
    if music_on:
        try:
            sound = getattr(sounds, name, None)
            if sound:
                sound.play()
        except Exception as e:
            print(f"Erro ao tocar som {name}: {e}")

def stop_background_music():
    try:
        music.stop()
    except Exception as e:
        print(f"Erro ao parar música: {e}")

def play_background_music():
    if music_on:
        try:
            music.play("background")
            music.set_volume(0.3)
        except Exception as e:
            print(f"Erro ao tocar música: {e}. Verifique se 'music/background.ogg' ou '.wav' existe.")
    else:
        stop_background_music()

def toggle_music():
    global music_on
    music_on = not music_on
    play_background_music()

def setup_game():
    global hero, enemies, platforms, projectiles, game_state
    enemies = []
    projectiles = []
    try:
        hero = Hero((WIDTH // 4, HEIGHT - 80))
    except Exception as e:
        print(f"ERRO FATAL ao criar Herói: {e}. Verifique se as imagens existem! Saindo.")
        sys.exit()

    platforms = [
        Rect(0, HEIGHT - 40, WIDTH, 40),
        Rect(200, HEIGHT - 150, 150, 20),
        Rect(450, HEIGHT - 250, 100, 20),
        Rect(WIDTH - 300, HEIGHT - 120, 150, 20),
        Rect(50, HEIGHT - 350, 100, 20)
    ]
    enemy_configs = [
        ((300, HEIGHT - 80), (220, 380)),
        ((WIDTH - 150, HEIGHT - 160), (WIDTH - 300, WIDTH - 50)),
        ((100, HEIGHT - 400), (50, 150))
    ]
    for pos, limits in enemy_configs:
        try:
            enemies.append(Enemy(pos, limits))
        except Exception as e:
            print(f"Erro ao criar inimigo em {pos}: {e}. Verifique se as imagens existem.")

    game_state = 'playing'
    play_background_music()

def draw_text(text, pos, size=30, color_key='text', center=False):
    args = {'fontsize': size, 'color': COLORS[color_key], 'fontname': "dejavusans"}
    args['center' if center else 'topleft'] = pos
    screen.draw.text(text, **args)

def draw_menu():
    screen.fill(COLORS['bg'])
    draw_text(TITLE, (c_x, HEIGHT // 4), size=60, color_key='title', center=True)
    buttons = [
        (start_btn, "Iniciar Jogo"),
        (music_btn, f"Música: {'Ligada' if music_on else 'Desligada'}"),
        (exit_btn, "Sair")
    ]
    for r, t in buttons:
        color_key = 'btn_hover' if r.collidepoint(mouse_pos) else 'btn'
        screen.draw.filled_rect(r, COLORS[color_key])
        draw_text(t, r.center, center=True)

def draw_game():
    screen.fill(COLORS['bg'])
    for p in platforms:
        screen.draw.filled_rect(p, COLORS['platform'])
    if hero:
        hero.draw()
    for e in enemies:
        e.draw()
    for p in projectiles:
        p.draw()
    if hero:
        draw_text(f"Vida: {hero.health}", (10, 10))
    draw_text(f"Inimigos: {len(enemies)}", (WIDTH - 150, 10))

def draw_end_screen(message, title_color_key, bg_color_key):
    screen.fill(COLORS[bg_color_key])
    draw_text(message, (c_x, HEIGHT // 3), size=80, color_key=title_color_key, center=True)
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

def update(dt):
    global projectiles, enemies, game_state

    if game_state == 'playing':
        if hero:
            hero.update(dt, platforms, enemies)

        enemies_alive = []
        hero_actor = hero.actor if hero else None
        for e in enemies:
            if e.update(dt, hero_actor):
                enemies_alive.append(e)
        enemies = enemies_alive

        projectiles_to_keep = []
        for p in projectiles:
            if p.update(dt, platforms):
                collided_hero = False
                if hero and hero.invul_timer <= 0 and p.colliderect(hero.rect):
                    hero.take_damage(1)
                    collided_hero = True
                    play_sound('water_hit')
                if not collided_hero:
                    projectiles_to_keep.append(p)
        projectiles = projectiles_to_keep

        if not enemies and hero and hero.health > 0:
            game_state = 'victory'
            stop_background_music()
            play_sound('victory')

    elif game_state in ['game_over', 'victory'] and keyboard.space:
        game_state = 'menu'
        hero, enemies, projectiles = None, [], []

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
    input("Pressione Enter para sair.")

