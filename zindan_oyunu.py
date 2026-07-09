import math
import random
import os
import pygame
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.mixer.init()

import pgzrun
from pgzero import loaders as _pgzero_loaders


MUSIC_PATH = os.path.join(_pgzero_loaders.root, "music", "theme.wav")
SOUNDS_DIR = os.path.join(_pgzero_loaders.root, "sounds")


SOUND_FILES = ["attack", "hit", "coin", "win", "lose"]
SOUNDS = {}

print("=== SES TANI BILGISI ===")
print("Mixer baslatildi mi:", pygame.mixer.get_init())
print("Ses efektleri klasoru araniyor:", SOUNDS_DIR)
print("Klasor bulundu mu:", os.path.isdir(SOUNDS_DIR))
for _name in SOUND_FILES:
    _path = os.path.join(SOUNDS_DIR, _name + ".wav")
    try:
        SOUNDS[_name] = pygame.mixer.Sound(_path)
        print(f"  {_name}.wav : YUKLENDI ({_path})")
    except Exception as _e:
        print(f"  {_name}.wav : HATA -> {_e}  (aranan yol: {_path})")
print("Muzik dosyasi araniyor:", MUSIC_PATH)
print("Muzik dosyasi bulundu mu:", os.path.exists(MUSIC_PATH))
print("=========================")

WIDTH = 800
HEIGHT = 600
TITLE = "Zindan Kaçışı"

PLAY_AREA = Rect(40, 90, 720, 460)  # oyun alaninin sinirlari


# ------------------------------------------------------------------
# YARDIMCI FONKSIYON
# ------------------------------------------------------------------
def clamp(value, lo, hi):
    return max(lo, min(hi, value))
def distance(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)
# Ses efektleri (SFX) genel acik/kapali durumu - menudeki "Ses" butonuyla degisir
SFX_ENABLED = True


def play_sound(name):
    """Bir ses efektini calar; ses cihazi/dosyasi ile ilgili bir sorun
    olsa bile oyunun cokmesini engeller."""
    if not SFX_ENABLED:
        return
    snd = SOUNDS.get(name)
    if snd is None:
        print(f"Ses calinamadi ({name}): bu ses hic yuklenememisti (yukaridaki HATA satirina bak)")
        return
    try:
        snd.play()
    except Exception as e:
        print(f"Ses calinamadi ({name}):", e)


# ------------------------------------------------------------------
# TEMEL SINIF
# ------------------------------------------------------------------
class Entity:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        self.alive = True

    def collides_with(self, other):
        return (self.alive and other.alive and
                distance(self.x, self.y, other.x, other.y) < self.radius + other.radius)


# ------------------------------------------------------------------
# OYUNCU (KAHRAMAN)
# ------------------------------------------------------------------
class Player(Entity):
    SPEED = 190
    MAX_HP = 100

    def __init__(self, x, y):
        super().__init__(x, y, 16)
        self.hp = self.MAX_HP
        self.facing = (0, 1)          # son baktigi yon (attack ve bacak animasyonu icin)
        self.moving = False
        self.walk_timer = 0
        self.attack_timer = 0          # saldiri animasyonu suresi
        self.attack_cooldown = 0       # tekrar saldirana kadar bekleme
        self.invincible_timer = 0
        self.score = 0

    def update(self, dt):
        dx = dy = 0
        if keyboard.left or keyboard.a:
            dx -= 1
        if keyboard.right or keyboard.d:
            dx += 1
        if keyboard.up or keyboard.w:
            dy -= 1
        if keyboard.down or keyboard.s:
            dy += 1

        self.moving = (dx != 0 or dy != 0)
        if self.moving:
            length = math.hypot(dx, dy)
            dx, dy = dx / length, dy / length
            self.facing = (dx, dy)
            self.x += dx * self.SPEED * dt
            self.y += dy * self.SPEED * dt
            self.walk_timer += dt * 9

        # oyun alani disina cikamaz
        self.x = clamp(self.x, PLAY_AREA.left + self.radius, PLAY_AREA.right - self.radius)
        self.y = clamp(self.y, PLAY_AREA.top + self.radius, PLAY_AREA.bottom - self.radius)

        if self.attack_timer > 0:
            self.attack_timer -= dt
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        if self.invincible_timer > 0:
            self.invincible_timer -= dt

    def try_shoot(self):
        """SPACE tusuna basildiginda bakilan yonde bir mermi ateşler.
        Basarili olursa yeni Projectile nesnesini dondurur, aksi halde None."""
        if self.attack_cooldown <= 0:
            self.attack_cooldown = 0.35
            self.attack_timer = 0.18
            play_sound("attack")
            bullet_x = self.x + self.facing[0] * (self.radius + 6)
            bullet_y = self.y + self.facing[1] * (self.radius + 6)
            return Projectile(bullet_x, bullet_y, self.facing[0], self.facing[1])
        return None

    def attack_point(self):
        return (self.x + self.facing[0] * 34, self.y + self.facing[1] * 34)

    def take_damage(self, amount):
        if self.invincible_timer <= 0:
            self.hp -= amount
            self.invincible_timer = 1.0
            play_sound("hit")
            return True
        return False

    def draw(self):
        blink = self.invincible_timer > 0 and int(self.invincible_timer * 12) % 2 == 0
        if blink:
            return

        # Bacak animasyonu: yururken bacaklar makas gibi acilip kapanir
        leg_swing = math.sin(self.walk_timer) * 6 if self.moving else 0
        screen.draw.filled_rect(Rect(self.x - 8 - leg_swing, self.y + 8, 6, 12), (90, 60, 40))
        screen.draw.filled_rect(Rect(self.x + 2 + leg_swing, self.y + 8, 6, 12), (90, 60, 40))

        # Govde
        screen.draw.filled_circle((self.x, self.y), self.radius, (70, 170, 240))
        screen.draw.filled_circle((self.x, self.y - 4), 9, (250, 220, 180))  # kafa

        # Ates animasyonu: namluda kisa bir parlama
        if self.attack_timer > 0:
            fx = self.x + self.facing[0] * (self.radius + 10)
            fy = self.y + self.facing[1] * (self.radius + 10)
            screen.draw.filled_circle((fx, fy), 7, (255, 240, 140))

    def hp_ratio(self):
        return max(0, self.hp) / self.MAX_HP


# ------------------------------------------------------------------
# DUSMANLAR (Enemy - kendi bolgesinde hareket eden, tehlikeli)
# ------------------------------------------------------------------
class Enemy(Entity):
    MAX_HP = 30
    COLOR = (200, 60, 60)
    CONTACT_DAMAGE = 12
    SCORE_VALUE = 20

    def __init__(self, x, y):
        super().__init__(x, y, 15)
        self.hp = self.MAX_HP
        self.hit_cooldown = 0     # oyuncuya art arda hemen hasar vermesin diye
        self.flash_timer = 0      # vurulunca kisa beyaz yanip sonme
        self.anim_t = random.uniform(0, 10)

    def update(self, dt):
        self.anim_t += dt * 6
        if self.hit_cooldown > 0:
            self.hit_cooldown -= dt
        if self.flash_timer > 0:
            self.flash_timer -= dt

    def take_hit(self, damage):
        self.hp -= damage
        self.flash_timer = 0.12
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def try_damage_player(self, player):
        if self.hit_cooldown <= 0 and self.collides_with(player):
            if player.take_damage(self.CONTACT_DAMAGE):
                self.hit_cooldown = 0.8

    def body_color(self):
        return (255, 255, 255) if self.flash_timer > 0 else self.COLOR

    def draw_zone(self):
        pass  # alt siniflar kendi bolgesini cizer (yari saydam)


class GuardEnemy(Enemy):
    """Kendi bolgesinde (belirli bir x araligi) ileri geri devriye gezer."""

    COLOR = (210, 70, 60)
    SCORE_VALUE = 20

    def __init__(self, x, y, patrol_min_x, patrol_max_x):
        super().__init__(x, y)
        self.min_x = patrol_min_x
        self.max_x = patrol_max_x
        self.dir = 1
        self.speed = 55

    def update(self, dt):
        super().update(dt)
        self.x += self.dir * self.speed * dt
        if self.x >= self.max_x:
            self.x = self.max_x
            self.dir = -1
        elif self.x <= self.min_x:
            self.x = self.min_x
            self.dir = 1

    def draw_zone(self):
        screen.draw.rect(Rect(self.min_x - 15, self.y - 15, (self.max_x - self.min_x) + 30, 30),
                          (90, 40, 40))

    def draw(self):
        leg_swing = math.sin(self.anim_t) * 5
        screen.draw.filled_rect(Rect(self.x - 7 - leg_swing, self.y + 6, 5, 10), (60, 20, 20))
        screen.draw.filled_rect(Rect(self.x + 2 + leg_swing, self.y + 6, 5, 10), (60, 20, 20))
        screen.draw.filled_circle((self.x, self.y), self.radius, self.body_color())
        # gozler (bakis yonunu belli eder)
        eye_dx = 4 * self.dir
        screen.draw.filled_circle((self.x + eye_dx, self.y - 3), 2.5, (0, 0, 0))


class OrbiterEnemy(Enemy):
    """Kendi bolgesi icinde (sabit merkez etrafinda) daire cizerek doner."""

    COLOR = (160, 70, 210)
    SCORE_VALUE = 25

    def __init__(self, center_x, center_y, radius_of_zone):
        super().__init__(center_x + radius_of_zone, center_y)
        self.cx = center_x
        self.cy = center_y
        self.zone_radius = radius_of_zone
        self.angle = 0
        self.angular_speed = 1.6

    def update(self, dt):
        super().update(dt)
        self.angle += self.angular_speed * dt
        self.x = self.cx + math.cos(self.angle) * self.zone_radius
        self.y = self.cy + math.sin(self.angle) * self.zone_radius

    def draw_zone(self):
        screen.draw.circle((self.cx, self.cy), self.zone_radius, (60, 30, 70))

    def draw(self):
        pulse = 3 * math.sin(self.anim_t * 2)
        screen.draw.filled_circle((self.x, self.y), self.radius + pulse, self.body_color())
        screen.draw.filled_circle((self.x, self.y), 5, (255, 255, 255))


# ------------------------------------------------------------------
# MERMI (oyuncunun ates ettigi mermi)
# ------------------------------------------------------------------
class Projectile(Entity):
    SPEED = 480

    def __init__(self, x, y, dx, dy):
        super().__init__(x, y, 6)
        self.dx = dx
        self.dy = dy

    def update(self, dt):
        self.x += self.dx * self.SPEED * dt
        self.y += self.dy * self.SPEED * dt
        if not PLAY_AREA.collidepoint(self.x, self.y):
            self.alive = False

    def draw(self):
        screen.draw.filled_circle((self.x, self.y), self.radius, (255, 230, 90))
        screen.draw.filled_circle((self.x, self.y), 3, (255, 255, 220))


# ------------------------------------------------------------------
# ALTIN (COIN)
# ------------------------------------------------------------------
class Coin(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 10)
        self.bob_t = random.uniform(0, 10)

    def update(self, dt):
        self.bob_t += dt * 4

    def draw(self):
        bob = math.sin(self.bob_t) * 3
        screen.draw.filled_circle((self.x, self.y + bob), 8, (255, 210, 60))
        screen.draw.filled_circle((self.x, self.y + bob), 8, (200, 150, 20))
        screen.draw.filled_circle((self.x, self.y + bob), 5, (255, 230, 120))


# ------------------------------------------------------------------
# KAPI (COKIS / hedef)
# ------------------------------------------------------------------
class Door(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 22)
        self.unlocked = False

    def draw(self):
        color = (90, 200, 100) if self.unlocked else (110, 90, 70)
        screen.draw.filled_rect(Rect(self.x - 20, self.y - 28, 40, 56), color)
        screen.draw.filled_circle((self.x + 12, self.y), 3, (255, 230, 150))


# ------------------------------------------------------------------
# BUTON (ana menu icin)
# ------------------------------------------------------------------
class Button:
    def __init__(self, x, y, w, h, label):
        self.rect = Rect(x - w / 2, y - h / 2, w, h)
        self.label = label

    def contains(self, pos):
        return self.rect.collidepoint(pos)

    def draw(self, hover=False):
        color = (90, 150, 230) if hover else (60, 100, 170)
        screen.draw.filled_rect(self.rect, color)
        screen.draw.rect(self.rect, (20, 30, 60))
        screen.draw.text(self.label, center=self.rect.center, fontsize=28, color="white")


# ------------------------------------------------------------------
# ANA OYUN SINIFI
# ------------------------------------------------------------------
class Game:
    def __init__(self):
        self.state = "menu"           # menu | playing | win | gameover
        self.music_on = True
        self.sfx_on = True
        self.play_btn = Button(WIDTH / 2, HEIGHT / 2 - 55, 260, 52, "Oyuna Başla")
        self.music_btn = Button(WIDTH / 2, HEIGHT / 2 + 12, 260, 52, "")
        self.sfx_btn = Button(WIDTH / 2, HEIGHT / 2 + 79, 260, 52, "")
        self.exit_btn = Button(WIDTH / 2, HEIGHT / 2 + 146, 260, 52, "Çıkış")
        self._update_music_label()
        self._update_sfx_label()
        self.start_music()
        self.reset_level()

    # ---------------- MUZIK ----------------
    def _update_music_label(self):
        self.music_btn.label = "Müzik: Açık" if self.music_on else "Müzik: Kapalı"

    def _update_sfx_label(self):
        self.sfx_btn.label = "Ses Efekti: Açık" if self.sfx_on else "Ses Efekti: Kapalı"

    def start_music(self):
        if self.music_on:
            try:
                pygame.mixer.music.load(MUSIC_PATH)
                pygame.mixer.music.set_volume(0.6)
                pygame.mixer.music.play(-1)
                print("Muzik baslatildi, calisiyor mu:", pygame.mixer.music.get_busy())
            except Exception as e:
                print("Muzik yuklenemedi:", e)

    def toggle_music(self):
        self.music_on = not self.music_on
        self._update_music_label()
        if self.music_on:
            self.start_music()
        else:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    def toggle_sfx(self):
        global SFX_ENABLED
        self.sfx_on = not self.sfx_on
        SFX_ENABLED = self.sfx_on
        self._update_sfx_label()
        if self.sfx_on:
            play_sound("coin")  # test amacli kisa bir "ses acildi" bip'i

    # ---------------- SEVIYE KURULUMU ----------------
    def reset_level(self):
        self.player = Player(WIDTH / 2, PLAY_AREA.bottom - 40)
        self.bullets = []

        self.enemies = [
            GuardEnemy(160, 180, 120, 300),
            GuardEnemy(560, 420, 480, 680),
            OrbiterEnemy(250, 420, 55),
            OrbiterEnemy(620, 200, 55),
        ]
        self.total_enemies = len(self.enemies)

        self.coins = [
            Coin(120, 130), Coin(680, 130), Coin(400, 300),
            Coin(120, 500), Coin(680, 500),
        ]
        self.total_coins = len(self.coins)

        self.door = Door(WIDTH / 2, PLAY_AREA.top + 15)

    # ---------------- GUNCELLEME ----------------
    def update(self, dt):
        if self.state != "playing":
            return

        self.player.update(dt)

        for b in self.bullets:
            b.update(dt)
        for e in self.enemies:
            e.update(dt)
            e.try_damage_player(self.player)
        for c in self.coins:
            c.update(dt)

        # mermi -> dusman carpismasi
        for b in self.bullets:
            if not b.alive:
                continue
            for e in self.enemies:
                if e.alive and b.collides_with(e):
                    b.alive = False
                    if e.take_hit(15):
                        self.player.score += e.SCORE_VALUE
                    break
        self.bullets = [b for b in self.bullets if b.alive]
        self.enemies = [e for e in self.enemies if e.alive]

        # altin toplama
        for c in self.coins:
            if c.alive and self.player.collides_with(c):
                c.alive = False
                self.player.score += 5
                play_sound("coin")
        self.coins = [c for c in self.coins if c.alive]

        # kapi kilit acma sarti
        if not self.door.unlocked and not self.enemies and not self.coins:
            self.door.unlocked = True

        # kapiya ulasma -> kazanma
        if self.door.unlocked and self.player.collides_with(self.door):
            self.state = "win"
            play_sound("win")

        # can biterse -> kaybetme
        if self.player.hp <= 0:
            self.state = "gameover"
            play_sound("lose")

    def handle_shoot(self):
        if self.state != "playing":
            return
        bullet = self.player.try_shoot()
        if bullet is not None:
            self.bullets.append(bullet)

    # ---------------- CIZIM ----------------
    def draw(self):
        screen.fill((25, 20, 30))

        if self.state == "menu":
            self._draw_menu()
            return

        # zindan zemini
        screen.draw.filled_rect(PLAY_AREA, (45, 40, 55))
        screen.draw.rect(PLAY_AREA, (15, 12, 20))

        for e in self.enemies:
            e.draw_zone()

        self.door.draw()
        for c in self.coins:
            c.draw()
        for e in self.enemies:
            e.draw()
        for b in self.bullets:
            b.draw()
        self.player.draw()

        self._draw_hud()

        if self.state == "win":
            self._draw_overlay("KAZANDIN!", (90, 230, 120),
                                "Tekrar oynamak için BOŞLUK'a bas")
        elif self.state == "gameover":
            self._draw_overlay("KAYBETTİN", (230, 90, 90),
                                "Tekrar denemek için BOŞLUK'a bas")

    def _draw_hud(self):
        # can (HP) cubugu
        screen.draw.text("Can:", topleft=(20, 20), fontsize=22, color="white")
        bar_bg = Rect(80, 20, 200, 20)
        screen.draw.filled_rect(bar_bg, (60, 20, 20))
        fill_w = 200 * self.player.hp_ratio()
        screen.draw.filled_rect(Rect(80, 20, fill_w, 20), (60, 200, 90))
        screen.draw.rect(bar_bg, (10, 10, 10))

        screen.draw.text(f"Skor: {self.player.score}", topleft=(20, 50), fontsize=22, color="white")
        screen.draw.text(f"Düşman: {len(self.enemies)}/{self.total_enemies}",
                          topleft=(WIDTH - 220, 20), fontsize=22, color="white")
        screen.draw.text(f"Altın: {self.total_coins - len(self.coins)}/{self.total_coins}",
                          topleft=(WIDTH - 220, 50), fontsize=22, color="white")

        if self.door.unlocked:
            screen.draw.text("Kapı açıldı! Çıkışa ulaş.",
                              center=(WIDTH / 2, PLAY_AREA.top - 10), fontsize=20, color=(120, 230, 140))

    def _draw_menu(self):
        # Ust ve alt dekoratif seritler
        screen.draw.filled_rect(Rect(0, 0, WIDTH, 8), (90, 60, 140))
        screen.draw.filled_rect(Rect(0, HEIGHT - 8, WIDTH, 8), (90, 60, 140))

        # Baslik - once golge (kaydirilmis koyu kopya), sonra ust uste parlak metin
        title_y = HEIGHT / 2 - 175
        screen.draw.text(TITLE.upper(), center=(WIDTH / 2 + 3, title_y + 3),
                          fontsize=54, color=(20, 15, 30))
        screen.draw.text(TITLE.upper(), center=(WIDTH / 2, title_y),
                          fontsize=54, color=(255, 210, 90))

        # Baslik altinda ince dekoratif cizgi
        screen.draw.filled_rect(Rect(WIDTH / 2 - 140, title_y + 36, 280, 3), (140, 100, 180))

        screen.draw.text("Yön tuşları / WASD: hareket    |    BOŞLUK: ateş et",
                          center=(WIDTH / 2, title_y + 62), fontsize=21, color=(210, 205, 220))

        mouse = getattr(self, "_mouse_pos", (-1, -1))
        self.play_btn.draw(hover=self.play_btn.contains(mouse))
        self.music_btn.draw(hover=self.music_btn.contains(mouse))
        self.sfx_btn.draw(hover=self.sfx_btn.contains(mouse))
        self.exit_btn.draw(hover=self.exit_btn.contains(mouse))

        screen.draw.text("Tüm düşmanları yen, tüm altınları topla, kapıya ulaş!",
                          center=(WIDTH / 2, HEIGHT - 40), fontsize=18, color=(150, 145, 165))

    def _draw_overlay(self, title, color, subtitle):
        screen.draw.filled_rect(Rect(WIDTH / 2 - 220, HEIGHT / 2 - 70, 440, 140), (0, 0, 0))
        screen.draw.text(title, center=(WIDTH / 2, HEIGHT / 2 - 25), fontsize=48, color=color)
        screen.draw.text(subtitle, center=(WIDTH / 2, HEIGHT / 2 + 25), fontsize=20, color="white")

    # ---------------- GIRDI (KLAVYE / FARE) ----------------
    def on_key_down(self, key):
        if key == keys.SPACE:
            if self.state == "playing":
                self.handle_shoot()
            elif self.state in ("win", "gameover"):
                self.reset_level()
                self.state = "playing"

    def on_mouse_move(self, pos):
        self._mouse_pos = pos

    def on_mouse_down(self, pos):
        if self.state != "menu":
            return
        if self.play_btn.contains(pos):
            self.reset_level()
            self.state = "playing"
        elif self.music_btn.contains(pos):
            self.toggle_music()
        elif self.sfx_btn.contains(pos):
            self.toggle_sfx()
        elif self.exit_btn.contains(pos):
            exit()


# ------------------------------------------------------------------
# PYGAME ZERO GIRIS NOKTALARI
# ------------------------------------------------------------------
game = Game()


def update(dt):
    game.update(dt)


def draw():
    game.draw()


def on_key_down(key):
    game.on_key_down(key)


def on_mouse_move(pos):
    game.on_mouse_move(pos)


def on_mouse_down(pos):
    game.on_mouse_down(pos)



pgzrun.go()
