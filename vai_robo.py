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
GRAVITY, JUMP, MAX_FALL, P_SPEED, E_BOUNCE = 0.5, -10, 10, 7, -5  # P_SPEED, E_BOUNCE not fully used yet
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


# --- Base Animated Class ---
class AnimActor:
    def __init__(self, pos, anims, speed=0.1):
        self.anims = {k: v for k, v in anims.items() if v}
        self.state = 'idle' if 'idle' in self.anims else next(iter(self.anims.keys()))
        self.f_idx, self.a_timer, self.a_speed = 0, 0.0, speed
        self.img = self.anims.get(self.state, ['default_image'])[0]
        try:
            self.actor = Actor(self.img, pos)
        except Exception as e:
            print(f"Error loading {self.img}: {e}. Using 'default_image'.")
            try:
                self.actor = Actor('default_image', pos)
            except Exception as fe:
                print(f"FATAL DefaultImg: {fe}"); sys.exit()
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
                print(f"Error loading frame {frames[self.f_idx]}: {e}"); self.actor.image = 'default_image'

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
                print(f"Error setting state img {img_name}: {e}"); self.actor.image = 'default_image'

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
        anims = {'idle': ['robot_idle_0', 'robot_idle_1'], 'run': ['robot_run_0', 'robot_run_1', 'robot_run_2'],
                 'jump': ['robot_jump_0'], 'fall': ['robot_fall_0'], 'hurt': ['robot_hurt_0']}
        super().__init__(pos, anims, speed=0.1)
        self.vx, self.vy, self.on_ground = 0, 0, False
        self.health, self.invul_timer = HERO_HEALTH, 0.0

    def update(self, dt, current_platforms, enemies_list):  # enemies_list now passed
        # Invulnerability & Hurt State (Basic visual, full logic later)
        if self.invul_timer > 0: self.invul_timer -= dt
        self.actor.opacity = 0.5 if self.invul_timer > 0 and int(self.invul_timer * 10) % 2 == 0 else 1.0

        if self.state == 'hurt':
            # Simple hurt: play animation, then recover. More complex interaction later.
            self.vy = min(self.vy + GRAVITY, MAX_FALL)  # Still affected by gravity
            self.y += self.vy
            # Check for landing after being hurt/knocked up
            colliding_platforms = [p for p in current_platforms if self.rect.colliderect(p)]
            self.on_ground = any(self.actor.bottom <= p.top + self.vy + 1 for p in colliding_platforms)
            if self.on_ground:
                # Adjust position to be on top of the platform
                self.actor.bottom = min(p.top for p in colliding_platforms if
                                        self.rect.colliderect(p) and self.actor.bottom <= p.top + self.vy + 1)
                self.vy = 0
            if self.on_ground and self.a_timer >= self.a_speed * len(self.anims['hurt']):
                self.set_state('idle')
            self.update_anim(dt);
            return

        # Movement Input
        prev_vx = self.vx
        if keyboard.left:
            self.vx, self.facing_right = -HERO_SPEED, False
        elif keyboard.right:
            self.vx, self.facing_right = HERO_SPEED, True
        else:
            self.vx = 0
        if self.on_ground: self.set_state('run' if self.vx != 0 else 'idle')

        # Vertical Movement & Jump
        self.vy = min(self.vy + GRAVITY, MAX_FALL)
        if keyboard.space and self.on_ground: self.vy, self.on_ground, _ = JUMP, False, play_sound(
            'jump'); self.set_state('jump')
        if not self.on_ground: self.set_state('jump' if self.vy < 0 else 'fall')

        # Apply Movement & Collisions
        self.x += self.vx
        for p in current_platforms:
            if self.rect.colliderect(p):
                if self.vx > 0:
                    self.actor.right = p.left
                elif self.vx < 0:
                    self.actor.left = p.right
                self.vx = 0;
                break

        self.y += self.vy
        self.on_ground = False
        for p in current_platforms:
            if self.rect.colliderect(p):
                if self.vy > 0 and self.actor.bottom <= p.top + self.vy + 1:
                    self.actor.bottom, self.vy, self.on_ground = p.top, 0, True
                    self.set_state('idle' if self.vx == 0 else 'run')
                elif self.vy < 0 and self.actor.top >= p.bottom + self.vy - 1:
                    self.actor.top, self.vy = p.bottom, 0
                break

        # Enemy Collision (Basic - Hero takes damage, no stomp yet)
        if self.invul_timer <= 0:
            for e in enemies_list:
                if self.rect.colliderect(e.rect):
                    # Simple damage taking for now. Stomping/bouncing later.
                    self.take_damage(1)
                    # Basic knockback (will be refined)
                    self.vx = -3 if e.x < self.x else 3  # Knock away from enemy
                    self.vy = -2  # Slight pop up
                    self.on_ground = False
                    break  # Only interact with one enemy per frame

        # Screen Bounds & Fall Death
        self.actor.left = max(0, self.actor.left);
        self.actor.right = min(WIDTH, self.actor.right)
        if self.actor.top > HEIGHT + 50: self.take_damage(999)  # Instant death if falls
        self.update_anim(dt)

    def take_damage(self, amount):
        if self.invul_timer <= 0 and self.health > 0:
            self.health -= amount;
            play_sound('hero_hurt')
            if self.health <= 0:
                self.die()
            else:
                self.set_state('hurt');
                self.invul_timer = 1.5  # Invulnerability time
                self.vy = -3  # Knockback up
                self.on_ground = False

    def die(self):
        global game_state
        game_state = 'game_over';
        stop_background_music();
        play_sound('game_over')


# --- Enemy Class ---
class Enemy(AnimActor):
    def __init__(self, pos, limits):
        anims = {
            'idle': ['enemy_idle_0', 'enemy_idle_1'],  # Ensure images exist
            'walk': ['enemy_walk_0', 'enemy_walk_1'],
            'shoot': ['enemy_shoot_0'],  # For later
            'hurt': ['enemy_hurt_0'],
            'die': ['enemy_die_0', 'enemy_die_1']
        }
        super().__init__(pos, anims, speed=random.uniform(0.12, 0.18))
        self.limits = limits  # Tuple (min_x, max_x) for patrol
        self.speed = random.uniform(1.0, 2.0)  # Pixels per frame effectively (scaled by dt later)
        self.vx = self.speed if random.choice([True, False]) else -self.speed
        self.facing_right = self.vx > 0
        # self.shoot_cd, self.shoot_int = random.uniform(1.5, 3.5), random.uniform(2.5, 4.5) # For later
        # self.detect_range = 300 # For later
        self.health = ENEMY_HEALTH
        self.dying = False  # If true, plays die animation then removed
        self.death_timer = 0.5  # Time for die animation to play out

        self.set_state('walk' if 'walk' in self.anims else 'idle')

    def update(self, dt, hero_actor):  # hero_actor not used for shooting yet
        if self.dying:
            self.set_state('die')
            self.update_anim(dt)
            self.death_timer -= dt
            return self.death_timer > 0  # Returns False when ready to be removed

        if self.state == 'hurt':
            # If hurt animation finished, go back to walking/idling
            if self.a_timer >= self.a_speed * len(self.anims.get('hurt', [])):
                self.set_state('walk')  # Or idle if preferred
                self.vx = self.speed if self.facing_right else -self.speed  # Resume movement
            self.update_anim(dt)
            return True  # Still alive

        # Patrol Logic
        self.x += self.vx * dt * 60  # Scale speed by dt for frame-rate independence

        if (self.vx > 0 and self.actor.right >= self.limits[1]) or \
                (self.vx < 0 and self.actor.left <= self.limits[0]):
            self.vx *= -1  # Reverse direction
            self.facing_right = self.vx > 0
            self.set_state('walk')  # Ensure walk animation plays in new direction
            # Clamp position to prevent going out of bounds slightly
            self.actor.right = min(self.actor.right, self.limits[1])
            self.actor.left = max(self.actor.left, self.limits[0])

        # Shooting logic will be added in the next commit
        # For now, just patrol and animate
        # if self.state not in ['walk', 'hurt', 'die']: # If somehow not walking
        #     self.set_state('walk')
        #     self.vx = self.speed if self.facing_right else -self.speed

        self.update_anim(dt)
        return True  # Still alive

    def take_damage(self, amount):  # Called by hero stomp or projectile later
        if not self.dying and self.health > 0:
            self.health -= amount
            play_sound('enemy_hurt')  # Assuming 'enemy_hurt.wav'
            self.set_state('hurt')
            self.vx = 0  # Stop moving when hurt
            if self.health <= 0:
                self.die()

    def die(self):
        if not self.dying:  # Prevent multiple calls
            self.dying = True
            self.set_state('die')
            self.vx = 0  # Stop all movement
            play_sound('enemy_die')  # Assuming 'enemy_die.wav'


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
            music.play("background"); music.set_volume(0.3)
        except Exception as e:
            print(f"Error music: {e}. Check music/background.ogg/wav")
    else:
        stop_background_music()


def toggle_music():
    global music_on;
    music_on = not music_on;
    play_sound('button_click')
    play_background_music() if music_on else stop_background_music()


# --- Game Setup ---
def setup_game():
    global hero, enemies, platforms, projectiles, game_state
    enemies, projectiles = [], []
    try:
        hero = Hero((WIDTH // 4, HEIGHT - 80))
    except Exception as e:
        print(f"FATAL Hero Error: {e}. Check images! Exiting."); sys.exit()

    platforms = [
        Rect(0, HEIGHT - 40, WIDTH, 40), Rect(200, HEIGHT - 150, 150, 20),
        Rect(450, HEIGHT - 250, 100, 20), Rect(WIDTH - 300, HEIGHT - 120, 150, 20),
        Rect(50, HEIGHT - 350, 100, 20)
    ]
    try:
        # Ensure enemy images like 'enemy_idle_0.png', 'enemy_walk_0.png' exist
        enemies.append(Enemy((300, HEIGHT - 80 - 10), (220, 380)))  # -10 to avoid initial ground collision issues
        enemies.append(Enemy((WIDTH - 150, HEIGHT - 160 - 10), (WIDTH - 300, WIDTH - 50)))
        enemies.append(Enemy((100, HEIGHT - 400 - 10), (50, 150)))
    except Exception as e:
        print(f"Enemy Creation Error: {e}. Check enemy images.")

    game_state = 'playing';
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
        screen.draw.text(text, **args)


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
    for e in enemies: e.draw()
    # for p in projectiles: p.draw() # For next commit
    if hero: draw_text(f"Vida: {hero.health}", (10, 10))
    draw_text(f"Inimigos: {len(enemies)}", (WIDTH - 150, 10))


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
        draw_end_screen("VITÓRIA!", 'victory', 'bg')  # Victory condition next commit


# --- Update Function ---
def update(dt):
    global projectiles, enemies, game_state  # projectiles for later
    if game_state == 'playing':
        if hero: hero.update(dt, platforms, enemies)

        enemies_alive = []
        for e in enemies:
            if e.update(dt, hero.actor if hero else None):  # Pass hero for potential future targeting
                enemies_alive.append(e)
        enemies = enemies_alive

        # projectiles = [p for p in projectiles if p.update(dt, platforms)] # For next commit

        # Basic win condition (no enemies) - will be refined
        if not enemies and hero and hero.health > 0:  # Ensure hero is alive
            # game_state = 'victory' # Enable this in the next commit after combat is complete
            # stop_background_music()
            # play_sound('victory')
            pass  # Victory logic will be in the final commit

    elif game_state in ['game_over', 'victory'] and keyboard.space:
        game_state = 'menu'
        # setup_game() # Optionally reset game immediately or let menu handle it


# --- Input Handlers ---
def on_mouse_move(pos): global mouse_pos; mouse_pos = pos


def on_mouse_down(pos, button):
    global game_state
    if game_state == 'menu' and button == mouse.LEFT:
        if start_btn.collidepoint(pos):
            play_sound('button_click'); setup_game()
        elif music_btn.collidepoint(pos):
            toggle_music()
        elif exit_btn.collidepoint(pos):
            play_sound('button_click'); sys.exit()


# --- Run ---
# print("Instructions: Ensure images/sounds folders are populated. Enemy images needed.")
pgzrun.go()