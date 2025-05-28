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


# --- Base Animated Class ---
class AnimActor:
    def __init__(self, pos, anims, speed=0.1):
        self.anims = {k: v for k, v in anims.items() if v}  # Filter empty anims
        self.state = 'idle' if 'idle' in self.anims else next(iter(self.anims.keys()))  # Ensure valid start state
        self.f_idx, self.a_timer, self.a_speed = 0, 0.0, speed
        self.img = self.anims.get(self.state, ['default_image'])[0]
        try:
            self.actor = Actor(self.img, pos)
        except Exception as e:
            print(f"Error loading {self.img}: {e}"); self.actor = Actor('default_image', pos)  # Fallback
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
        # Basic direction handling (assumes _left sprites exist if needed, not implemented here)
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

    def update(self, dt, current_platforms, enemies_list):
        # Invulnerability & Hurt State
        if self.invul_timer > 0: self.invul_timer -= dt
        self.actor.opacity = 0.5 if self.invul_timer > 0 and int(self.invul_timer * 10) % 2 == 0 else 1.0

        if self.state == 'hurt':
            self.vy = min(self.vy + GRAVITY, MAX_FALL)  # Affected by gravity even when hurt
            self.y += self.vy  # Apply vertical movement

            # Check for landing on a platform while hurt
            colliding_platforms = [p for p in current_platforms if self.rect.colliderect(p)]
            self.on_ground = any(self.actor.bottom <= p.top + self.vy + 1 for p in colliding_platforms if
                                 self.vy >= 0)  # Check only if moving down or still

            if self.on_ground:
                # Find the specific platform hero is landing on
                for p in colliding_platforms:
                    if self.actor.bottom <= p.top + self.vy + 1 and self.vy >= 0:
                        self.actor.bottom = p.top
                        self.vy = 0
                        break

            # Recover from hurt state after animation finishes AND on ground (or after a fixed time if preferred)
            if self.on_ground and self.a_timer >= self.a_speed * len(self.anims['hurt']):
                self.set_state('idle')
            elif not self.on_ground and self.a_timer >= self.a_speed * len(
                    self.anims['hurt']) * 1.5:  # timeout if stuck in air
                self.set_state('fall')  # Or idle, depending on desired behavior

            self.update_anim(dt);
            return

        # Movement Input
        prev_vx = self.vx  # Not used, but can be useful for state changes
        if keyboard.left:
            self.vx, self.facing_right = -HERO_SPEED, False
        elif keyboard.right:
            self.vx, self.facing_right = HERO_SPEED, True
        else:
            self.vx = 0

        if self.on_ground: self.set_state('run' if self.vx != 0 else 'idle')

        # Vertical Movement & Jump
        self.vy = min(self.vy + GRAVITY, MAX_FALL)
        if keyboard.space and self.on_ground:
            self.vy, self.on_ground = JUMP, False
            play_sound('jump');
            self.set_state('jump')

        if not self.on_ground: self.set_state('jump' if self.vy < 0 else 'fall')

        # Apply Movement & Collisions
        self.x += self.vx
        for p in current_platforms:  # Horizontal Collision
            if self.rect.colliderect(p):
                if self.vx > 0:
                    self.actor.right = p.left
                elif self.vx < 0:
                    self.actor.left = p.right
                self.vx = 0;
                break

        self.y += self.vy
        self.on_ground = False  # Assume not on ground, prove otherwise
        for p in current_platforms:  # Vertical Collision
            if self.rect.colliderect(p):
                if self.vy > 0 and self.actor.bottom <= p.top + self.vy + 1:  # Landing
                    self.actor.bottom, self.vy, self.on_ground = p.top, 0, True
                    self.set_state('idle' if self.vx == 0 else 'run')
                elif self.vy < 0 and self.actor.top >= p.bottom + self.vy - 1:  # Hitting head
                    self.actor.top, self.vy = p.bottom, 0
                break  # Process one vertical collision

        # Enemy Collision
        if self.invul_timer <= 0:  # Can only interact with enemies if not invulnerable
            for e in enemies_list:
                if not e.dying and self.rect.colliderect(e.rect):  # Check enemy is not already dying
                    # Stomp: if hero is falling and lands on top of enemy
                    if self.vy > 0 and self.actor.bottom < e.actor.centery + 5:  # Small tolerance for centery
                        e.take_damage(1)
                        self.vy, self.on_ground = E_BOUNCE, False  # Bounce off enemy
                        play_sound('stomp')  # Assuming 'stomp.wav' or '.ogg'
                    else:  # Otherwise, hero takes damage
                        self.take_damage(1)
                        self.vx = -HERO_SPEED / 1.5 if e.x < self.x else HERO_SPEED / 1.5  # Knockback from enemy
                        # self.vy = -2 # Slight pop up already handled by take_damage
                    break  # Interact with one enemy per frame

        # Screen Bounds & Fall Death
        self.actor.left = max(0, self.actor.left);
        self.actor.right = min(WIDTH, self.actor.right)
        if self.actor.top > HEIGHT + 50: self.take_damage(999)  # Instant death if falls
        self.update_anim(dt)

    def take_damage(self, amount):
        if self.invul_timer <= 0 and self.health > 0:  # Can only take damage if not invulnerable and alive
            self.health -= amount;
            play_sound('hero_hurt')
            if self.health <= 0:
                self.die()
            else:
                self.set_state('hurt');
                self.invul_timer = 1.5  # Set invulnerability timer
                self.vy = -3  # Knockback effect (upwards)
                self.on_ground = False  # Character is airborne due to knockback

    def die(self):
        global game_state
        # This check prevents die() from being called multiple times if health is already <= 0
        if game_state != 'game_over':
            game_state = 'game_over';
            stop_background_music();
            play_sound('game_over')


# --- Enemy Class ---
class Enemy(AnimActor):
    def __init__(self, pos, limits):
        anims = {'idle': ['enemy_idle_0', 'enemy_idle_1'], 'walk': ['enemy_walk_0', 'enemy_walk_1'],
                 'shoot': ['enemy_shoot_0'], 'hurt': ['enemy_hurt_0'], 'die': ['enemy_die_0', 'enemy_die_1']}
        super().__init__(pos, anims, speed=random.uniform(0.1, 0.15))
        self.limits = limits;
        self.speed = random.uniform(1.5, 2.5)
        self.vx = self.speed if random.choice([True, False]) else -self.speed;
        self.facing_right = self.vx > 0
        self.shoot_cd, self.shoot_int = random.uniform(1.5, 3.5), random.uniform(2.5, 4.5)  # Cooldown, Interval
        self.detect_range, self.health, self.dying, self.death_timer = 300, ENEMY_HEALTH, False, 0.5  # Death anim time
        self.set_state('walk' if 'walk' in self.anims else 'idle')

    def update(self, dt, hero_actor_ref):  # hero_actor_ref is the hero.actor for position checks
        if self.dying:
            self.set_state('die');
            self.update_anim(dt);
            self.death_timer -= dt
            return self.death_timer > 0  # False when fully dead and animation over

        if self.state == 'hurt':
            if self.a_timer >= self.a_speed * len(self.anims['hurt']):  # After hurt anim
                self.set_state('walk')  # Or 'idle'
                self.vx = self.speed if self.facing_right else -self.speed  # Resume movement
            self.update_anim(dt);
            return True  # Still alive

        # Patrol
        self.x += self.vx * dt * 60  # dt scaled movement
        if (self.vx > 0 and self.actor.right >= self.limits[1]) or \
                (self.vx < 0 and self.actor.left <= self.limits[0]):
            self.vx *= -1;
            self.facing_right = self.vx > 0
            self.set_state('walk')  # Refresh animation state for direction
            self.actor.right = min(self.actor.right, self.limits[1])
            self.actor.left = max(self.actor.left, self.limits[0])

        # Shoot Logic
        self.shoot_cd -= dt
        can_shoot = False
        if hero_actor_ref and self.state != 'shoot':  # Only if hero exists and not already shooting
            dx = hero_actor_ref.x - self.x
            dy = abs(hero_actor_ref.y - self.y)
            # Check if hero is in range, roughly on same level, and enemy is facing hero
            if abs(dx) < self.detect_range and dy < self.height * 1.5 and \
                    ((self.facing_right and dx > 0) or (not self.facing_right and dx < 0)):
                can_shoot = True

        if can_shoot and self.shoot_cd <= 0:
            self.shoot();
            self.shoot_cd = self.shoot_int  # Reset cooldown
            self.set_state('shoot');
            self.vx = 0  # Stop moving to shoot
        elif self.state == 'shoot' and self.a_timer >= self.a_speed * len(
                self.anims['shoot']):  # Finished shooting anim
            self.vx = self.speed if self.facing_right else -self.speed  # Resume patrol
            self.set_state('walk')
        elif self.state not in ['walk', 'shoot', 'hurt', 'die']:  # If stuck in a weird state, default to walk
            self.set_state('walk');
            self.vx = self.speed if self.facing_right else -self.speed

        self.update_anim(dt);
        return True  # Still alive

    def shoot(self):
        play_sound('enemy_shoot')  # Assuming 'enemy_shoot.wav' or '.ogg'
        proj_x = self.actor.right + 5 if self.facing_right else self.actor.left - 5
        projectiles.append(Projectile((proj_x, self.actor.centery), P_SPEED if self.facing_right else -P_SPEED))

    def take_damage(self, amount):
        if not self.dying and self.health > 0:
            self.health -= amount;
            play_sound('enemy_hurt');
            self.set_state('hurt');
            self.vx = 0  # Stop when hurt
            if self.health <= 0: self.die()

    def die(self):
        if not self.dying:  # Ensure die is only called once
            self.dying = True;
            self.set_state('die');
            self.vx = 0;
            play_sound('enemy_die')


# --- Projectile Class ---
class Projectile(Actor):  # Pygame Zero Actor is fine for simple projectiles
    def __init__(self, pos, vx_speed):
        # Ensure 'water_projectile.png' (or your chosen name) exists in 'images/'
        # Or a 'default_projectile.png' as fallback
        try:
            super().__init__('water_projectile', pos)  # Use your projectile image name
        except Exception as e:
            print(f"Error loading water_projectile: {e}. Using 'default_image'.")
            super().__init__('default_image', pos)  # Fallback
        self.vx = vx_speed
        self.life = 3.0  # Projectile lasts for 3 seconds

    def update(self, dt, current_platforms):
        self.x += self.vx * dt * 60  # dt scaled movement
        self.life -= dt
        # Check collision with platforms or if life expired
        if self.life <= 0 or any(self.colliderect(p) for p in current_platforms):
            return False  # Signal to remove projectile
        # Check if out of bounds (optional, life timer usually handles it)
        if not (-self.width < self.x < WIDTH + self.width):
            return False
        return True  # Still active


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
    enemies, projectiles = [], []  # Clear previous game entities
    try:
        hero = Hero((WIDTH // 4, HEIGHT - 80))  # Reset hero
    except Exception as e:
        print(f"FATAL Hero Error: {e}. Check images! Exiting."); sys.exit()

    platforms = [
        Rect(0, HEIGHT - 40, WIDTH, 40), Rect(200, HEIGHT - 150, 150, 20),
        Rect(450, HEIGHT - 250, 100, 20), Rect(WIDTH - 300, HEIGHT - 120, 150, 20),
        Rect(50, HEIGHT - 350, 100, 20)
    ]
    try:
        enemies.append(Enemy((300, HEIGHT - 80 - 10), (220, 380)))
        enemies.append(Enemy((WIDTH - 150, HEIGHT - 160 - 10), (WIDTH - 300, WIDTH - 50)))
        enemies.append(Enemy((100, HEIGHT - 400 - 10), (50, 150)))
    except Exception as e:
        print(f"Enemy Error: {e}. Check enemy images.")

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
    for p in projectiles: p.draw()
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
        draw_end_screen("VITÓRIA!", 'victory', 'bg')


# --- Update Function ---
def update(dt):
    global projectiles, enemies, game_state
    if game_state == 'playing':
        if hero: hero.update(dt, platforms, enemies)

        enemies_alive = [e for e in enemies if e.update(dt, hero.actor if hero else None)]
        enemies = enemies_alive

        # Update projectiles and check for collision with hero
        active_projectiles = []
        for p in projectiles:
            if p.update(dt, platforms):  # If projectile is still active
                if hero and hero.invul_timer <= 0 and p.colliderect(hero.rect):
                    hero.take_damage(1)
                    # Projectile is consumed by hitting hero, so don't add to active_projectiles
                else:
                    active_projectiles.append(p)
        projectiles = active_projectiles

        # Check for victory condition
        if not enemies and hero and hero.health > 0 and game_state == 'playing':  # Check game_state to avoid re-triggering
            game_state = 'victory'
            stop_background_music()
            play_sound('victory')  # Assuming 'victory.wav' or '.ogg'

    elif game_state in ['game_over', 'victory'] and keyboard.space:
        game_state = 'menu'
        # setup_game() # Optional: Reset game immediately, or let menu handle fresh start.
        # Current setup_game clears lists, so it's fine if called from menu.


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
# print("Instructions: Ensure all images/sounds folders exist and are populated.")
# print("Needed: robot_*, enemy_*, default_image, water_projectile images.")
# print("Needed: jump, hero_hurt, game_over, enemy_hurt, enemy_die, enemy_shoot, stomp, victory sounds, background music.")
pgzrun.go()