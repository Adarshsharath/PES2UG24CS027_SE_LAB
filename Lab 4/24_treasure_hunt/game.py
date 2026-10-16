import pygame
import random

TILE = 40
COLS, ROWS = 32, 22
WALL, FLOOR, CHEST, KEY, TRAP, SPIKE_TRAP = range(6)
SPEED = 3
FPS = 60

VIEW_COLS, VIEW_ROWS = 24, 16
WIDTH = VIEW_COLS * TILE
HUD_HEIGHT = 70
HEIGHT = VIEW_ROWS * TILE + HUD_HEIGHT
WORLD_WIDTH = COLS * TILE
WORLD_HEIGHT = ROWS * TILE

COLORS = {
    WALL: (60, 50, 70),
    FLOOR: (200, 190, 170),
    CHEST: (200, 160, 30),
    KEY: (220, 220, 60),
    TRAP: (145, 65, 65),
    SPIKE_TRAP: (95, 75, 115),
}

WALKABLE_TILES = {FLOOR, CHEST, KEY, TRAP, SPIKE_TRAP}


def generate_world():
    """Generate a larger, connected dungeon with guaranteed key/chest access."""
    grid = [[WALL] * COLS for _ in range(ROWS)]
    rooms = []

    # Place non-overlapping rooms, then connect each new room to the previous one.
    attempts = 0
    while len(rooms) < 10 and attempts < 300:
        attempts += 1
        w = random.randint(4, 7)
        h = random.randint(3, 5)
        x = random.randint(1, COLS - w - 1)
        y = random.randint(1, ROWS - h - 1)
        room = pygame.Rect(x, y, w, h)
        if any(room.inflate(1, 1).colliderect(existing) for existing in rooms):
            continue
        rooms.append(room)
        for ry in range(y, y + h):
            for rx in range(x, x + w):
                grid[ry][rx] = FLOOR

    # Fallback ensures a playable world even if random room placement is unlucky.
    if len(rooms) < 2:
        rooms = [
            pygame.Rect(1, 1, 6, 5),
            pygame.Rect(COLS - 8, ROWS - 6, 6, 5),
        ]
        for room in rooms:
            for ry in range(room.top, room.bottom):
                for rx in range(room.left, room.right):
                    grid[ry][rx] = FLOOR

    # L-shaped corridors connect every room in sequence, making all rooms reachable.
    for i in range(len(rooms) - 1):
        ax, ay = rooms[i].centerx, rooms[i].centery
        bx, by = rooms[i + 1].centerx, rooms[i + 1].centery
        cx = ax
        while cx != bx:
            grid[ay][cx] = FLOOR
            cx += 1 if bx > cx else -1
        cy = ay
        while cy != by:
            grid[cy][bx] = FLOOR
            cy += 1 if by > cy else -1
        grid[by][bx] = FLOOR

    start_room = rooms[0]
    key_room = rooms[len(rooms) // 2]
    chest_room = rooms[-1]

    # Reserve a dedicated, walkable key tile and chest tile.
    key_pos = (key_room.centery, key_room.centerx)
    chest_pos = (chest_room.centery, chest_room.centerx)
    grid[key_pos[0]][key_pos[1]] = KEY
    grid[chest_pos[0]][chest_pos[1]] = CHEST

    # Traps are placed on corridor/floor cells, never blocking the only route,
    # and never in the start, key, or chest rooms.
    candidates = []
    protected_rooms = [start_room, key_room, chest_room]
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] != FLOOR:
                continue
            if any(room.inflate(1, 1).collidepoint(c, r) for room in protected_rooms):
                continue
            candidates.append((r, c))
    random.shuffle(candidates)
    for index, (r, c) in enumerate(candidates[:min(10, len(candidates))]):
        grid[r][c] = TRAP if index % 2 == 0 else SPIKE_TRAP

    return grid, start_room, rooms


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 28, 28)
        self.color = (60, 120, 220)
        self.has_key = False

    def move(self, keys, grid, rows, cols):
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += SPEED

        # Keep axis-by-axis movement so the original collision behaviour
        # is preserved and the player can slide along walls.
        self._try_move(dx, 0, grid, rows, cols)
        self._try_move(0, dy, grid, rows, cols)

    def _try_move(self, dx, dy, grid, rows, cols):
        if dx == 0 and dy == 0:
            return

        new_rect = self.rect.move(dx, dy)
        corners = [
            (new_rect.left, new_rect.top),
            (new_rect.right - 1, new_rect.top),
            (new_rect.left, new_rect.bottom - 1),
            (new_rect.right - 1, new_rect.bottom - 1),
        ]

        for px, py in corners:
            c, r = px // TILE, py // TILE
            if not (0 <= r < rows and 0 <= c < cols):
                return
            if grid[r][c] == WALL:
                return

        self.rect = new_rect

    def draw(self, screen):
        pygame.draw.ellipse(screen, self.color, self.rect)
        if self.has_key:
            pygame.draw.circle(
                screen, (255, 225, 40),
                (self.rect.right - 6, self.rect.top + 6), 5
            )


class Particle:
    """Animated sparks used for pickups, damage, and victory effects."""
    def __init__(self, x, y, color, velocity, life=28, radius=4):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = velocity
        self.color = color
        self.life = self.max_life = life
        self.radius = radius

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.12
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            radius = max(1, int(self.radius * self.life / self.max_life))
            pygame.draw.circle(surface, self.color,
                               (int(self.x), int(self.y)), radius)


class Guard:
    """A simple guard that patrols horizontally between two pixel positions."""
    def __init__(self, x, y, patrol_left, patrol_right):
        self.rect = pygame.Rect(x, y, 26, 30)
        self.patrol_left = patrol_left
        self.patrol_right = patrol_right
        self.speed = 2
        self.direction = 1

    def update(self):
        self.rect.x += self.speed * self.direction

        if self.rect.left <= self.patrol_left:
            self.rect.left = self.patrol_left
            self.direction = 1
        elif self.rect.right >= self.patrol_right:
            self.rect.right = self.patrol_right
            self.direction = -1

    def draw(self, screen):
        # Red body and a small gold helmet make the guard easy to identify.
        pygame.draw.rect(screen, (170, 45, 55), self.rect, border_radius=5)
        pygame.draw.circle(screen, (235, 185, 70),
                           (self.rect.centerx, self.rect.top + 5), 7)
        eye_x = self.rect.centerx + (4 if self.direction > 0 else -4)
        pygame.draw.circle(screen, (30, 25, 35),
                           (eye_x, self.rect.top + 5), 2)


class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Treasure Hunt")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 18)
        self.small_font = pygame.font.SysFont("monospace", 12)
        self.big_font = pygame.font.SysFont("monospace", 40, bold=True)
        self.reset()

    def reset(self):
        self.grid, start_room, rooms = generate_world()

        if start_room:
            self.start_position = (
                start_room.x * TILE + (start_room.width * TILE - 28) // 2,
                start_room.y * TILE + (start_room.height * TILE - 28) // 2,
            )
        else:
            self.start_position = (TILE + 6, TILE + 6)

        self.player = Player(*self.start_position)
        self.won = False
        self.status = "Find the KEY, then the CHEST!"
        self.guard = self._create_guard(rooms)
        self.camera_x = 0
        self.camera_y = 0
        self.particles = []
        self.frame = 0
        self.flash_timer = 0
        self.flash_color = (255, 70, 70)

    def _create_guard(self, rooms):
        """Place the guard in the chest room, with safe fallback positions."""
        if len(rooms) >= 2:
            room = rooms[-1]
            center_y = room.centery
            left_col = max(room.left, room.centerx - 1)
            right_col = min(room.right - 1, room.centerx + 1)

            # The chest occupies the room centre; patrol on a nearby row
            # where possible, avoiding the chest tile itself.
            patrol_row = room.top if room.top != center_y else room.bottom - 1
            if self.grid[patrol_row][left_col] in WALKABLE_TILES and \
               self.grid[patrol_row][right_col] in WALKABLE_TILES:
                left_x = left_col * TILE + 4
                right_x = right_col * TILE + TILE - 30
                y = patrol_row * TILE + 5
                return Guard(left_x, y, left_x, right_x)

            # A horizontal patrol through the room centre, stopping short
            # of the chest tile.
            left_x = room.left * TILE + 4
            right_x = (room.right - 1) * TILE + TILE - 30
            y = center_y * TILE + 5
            if left_x < right_x:
                return Guard(left_x, y, left_x, right_x)

        # Fallback for a generated world with too few rooms.
        x, y = self.start_position
        left = min(WORLD_WIDTH - 60, x + TILE)
        right = min(WORLD_WIDTH - 30, left + TILE)
        return Guard(left, y, left, right)

    def burst(self, x, y, color, count=18):
        for _ in range(count):
            angle = random.uniform(0, 6.28318)
            speed = random.uniform(1.0, 4.0)
            velocity = pygame.math.Vector2(speed, 0).rotate_rad(angle)
            self.particles.append(Particle(
                x, y, color, (velocity.x, velocity.y),
                random.randint(18, 38), random.randint(2, 5)
            ))

    def respawn_player(self, message):
        """Return to the start without regenerating the dungeon."""
        self.burst(self.player.rect.centerx, self.player.rect.centery,
                   (255, 65, 75), 24)
        self.player.rect.topleft = self.start_position
        # Keep the key once collected. Its original tile has been removed,
        # so retaining it guarantees the chest remains reachable after a hit.
        self.status = message
        self.flash_timer = 12
        self.flash_color = (190, 25, 45)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()
        return True

    def update(self):
        self.frame += 1
        for particle in self.particles:
            particle.update()
        self.particles = [p for p in self.particles if p.life > 0]
        if self.flash_timer > 0:
            self.flash_timer -= 1

        if self.won:
            if self.frame % 3 == 0:
                self.burst(random.randint(70, WIDTH - 70),
                           random.randint(70, ROWS * TILE - 70),
                           random.choice([(255, 210, 45), (70, 220, 255),
                                          (255, 90, 190)]), 2)
            return

        keys = pygame.key.get_pressed()
        self.player.move(keys, self.grid, ROWS, COLS)
        self.guard.update()

        # Use the player's centre tile for item and trap detection.
        pr = self.player.rect.centery // TILE
        pc = self.player.rect.centerx // TILE

        if 0 <= pr < ROWS and 0 <= pc < COLS:
            cell = self.grid[pr][pc]

            if cell == KEY:
                self.player.has_key = True
                self.grid[pr][pc] = FLOOR
                self.burst(self.player.rect.centerx, self.player.rect.centery,
                           (255, 225, 45), 30)
                self.status = "KEY ACQUIRED! The chest awaits..."
            elif cell == CHEST and self.player.has_key:
                self.won = True
                self.status = "Treasure found!"
            elif cell == TRAP:
                self.respawn_player("Trap triggered! Returned to start.")
            elif cell == SPIKE_TRAP:
                self.respawn_player("Spike trap! Returned to start.")

        # Guard collision also resets the player and removes the key.
        if self.player.rect.colliderect(self.guard.rect):
            self.respawn_player("Caught by the guard! Returned to start.")

    def draw_trap(self, cell, rect):
        if cell == TRAP:
            # Red pressure plate with a cross.
            pygame.draw.rect(self.screen, (120, 35, 45),
                             rect.inflate(-10, -10), border_radius=4)
            pygame.draw.line(self.screen, (245, 145, 90),
                             (rect.left + 13, rect.top + 13),
                             (rect.right - 13, rect.bottom - 13), 3)
            pygame.draw.line(self.screen, (245, 145, 90),
                             (rect.right - 13, rect.top + 13),
                             (rect.left + 13, rect.bottom - 13), 3)
        elif cell == SPIKE_TRAP:
            # Purple plate with three spike triangles.
            pygame.draw.rect(self.screen, (80, 55, 105),
                             rect.inflate(-8, -8), border_radius=4)
            for offset in (12, 20, 28):
                points = [
                    (rect.left + offset, rect.top + 11),
                    (rect.left + offset - 4, rect.bottom - 11),
                    (rect.left + offset + 4, rect.bottom - 11),
                ]
                pygame.draw.polygon(self.screen, (220, 210, 230), points)

    def draw_minimap(self):
        """Show the entire large dungeon in a compact live minimap."""
        scale = 3
        map_width = COLS * scale
        map_height = ROWS * scale
        margin = 8
        x0 = WIDTH - map_width - margin
        y0 = margin

        panel = pygame.Rect(x0 - 4, y0 - 4, map_width + 8, map_height + 8)
        pygame.draw.rect(self.screen, (12, 10, 20), panel, border_radius=4)
        mini_colors = {
            WALL: (48, 39, 60), FLOOR: (174, 164, 145),
            CHEST: (255, 175, 25), KEY: (255, 235, 40),
            TRAP: (220, 55, 65), SPIKE_TRAP: (170, 95, 225),
        }
        for r in range(ROWS):
            for c in range(COLS):
                pygame.draw.rect(
                    self.screen, mini_colors[self.grid[r][c]],
                    (x0 + c * scale, y0 + r * scale, scale, scale)
                )

        gx = x0 + (self.guard.rect.centerx // TILE) * scale
        gy = y0 + (self.guard.rect.centery // TILE) * scale
        pygame.draw.rect(self.screen, (255, 55, 55), (gx, gy, scale, scale))
        px = x0 + (self.player.rect.centerx // TILE) * scale
        py = y0 + (self.player.rect.centery // TILE) * scale
        pygame.draw.rect(self.screen, (40, 140, 255), (px, py, scale, scale))

    def draw_inventory(self, hud_y):
        slot = pygame.Rect(WIDTH - 58, hud_y + 12, 42, 42)
        pygame.draw.rect(self.screen, (65, 60, 78), slot, border_radius=5)
        pygame.draw.rect(self.screen, (175, 165, 190), slot, 2, border_radius=5)

        if self.player.has_key:
            # Simple key icon drawn with pygame primitives.
            cx, cy = slot.centerx - 4, slot.centery - 3
            pygame.draw.circle(self.screen, (255, 220, 45), (cx, cy), 8, 3)
            pygame.draw.line(self.screen, (255, 220, 45),
                             (cx + 7, cy + 5), (cx + 17, cy + 15), 4)
            pygame.draw.line(self.screen, (255, 220, 45),
                             (cx + 12, cy + 10), (cx + 16, cy + 6), 3)
            pygame.draw.line(self.screen, (255, 220, 45),
                             (cx + 16, cy + 14), (cx + 20, cy + 10), 3)

        label = self.small_font.render("KEY", True, (220, 220, 220))
        self.screen.blit(label, (slot.x + 8, slot.bottom + 2))

    def draw_glow(self, center, color, radius):
        glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for ring in range(5, 0, -1):
            r = int(radius * ring / 5)
            pygame.draw.circle(glow, (*color, 7 + ring * 2),
                               (radius, radius), r)
        self.screen.blit(glow, (center[0] - radius, center[1] - radius),
                         special_flags=pygame.BLEND_RGBA_ADD)

    def draw(self):
        self.screen.fill((18, 15, 28))

        # Camera follows the player while clamping to the large world edges.
        target_x = self.player.rect.centerx - WIDTH // 2
        target_y = self.player.rect.centery - (VIEW_ROWS * TILE) // 2
        self.camera_x = max(0, min(WORLD_WIDTH - WIDTH, target_x))
        self.camera_y = max(0, min(WORLD_HEIGHT - VIEW_ROWS * TILE, target_y))
        world_view = pygame.Rect(self.camera_x, self.camera_y, WIDTH, VIEW_ROWS * TILE)

        first_col = max(0, self.camera_x // TILE)
        last_col = min(COLS, (self.camera_x + WIDTH) // TILE + 2)
        first_row = max(0, self.camera_y // TILE)
        last_row = min(ROWS, (self.camera_y + VIEW_ROWS * TILE) // TILE + 2)

        for r in range(first_row, last_row):
            for c in range(first_col, last_col):
                cell = self.grid[r][c]
                world_rect = pygame.Rect(c * TILE, r * TILE, TILE, TILE)
                rect = world_rect.move(-self.camera_x, -self.camera_y)
                pygame.draw.rect(self.screen, COLORS[cell], rect)
                if cell != WALL:
                    pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)
                    if cell == FLOOR:
                        fx = rect.left + 7 + ((r * 13 + c * 7) % 25)
                        fy = rect.top + 8 + ((r * 5 + c * 11) % 23)
                        pygame.draw.circle(self.screen, (178, 167, 150), (fx, fy), 1)
                else:
                    pygame.draw.line(self.screen, (76, 65, 88),
                                     (rect.left + 4, rect.top + 5),
                                     (rect.right - 4, rect.top + 5), 2)

                if cell == KEY:
                    pygame.draw.circle(self.screen, (255, 240, 60), rect.center, 10)
                    pygame.draw.circle(self.screen, (255, 255, 190), rect.center, 14, 1)
                elif cell == CHEST:
                    chest_rect = rect.inflate(-12, -12)
                    pygame.draw.rect(self.screen, (120, 75, 15), chest_rect, border_radius=4)
                    pygame.draw.rect(self.screen, (180, 120, 20),
                                     chest_rect.inflate(-4, -4), border_radius=3)
                elif cell in (TRAP, SPIKE_TRAP):
                    self.draw_trap(cell, rect)

        def screen_rect(world_rect):
            return world_rect.move(-self.camera_x, -self.camera_y)

        pulse = 34 + int(5 * (1 + pygame.math.Vector2(1, 0).rotate(self.frame * 3).y))
        guard_screen = screen_rect(self.guard.rect)
        player_screen = screen_rect(self.player.rect)
        if world_view.colliderect(self.guard.rect):
            self.draw_glow(guard_screen.center, (255, 35, 55), pulse)
            guard_copy = Guard(guard_screen.x, guard_screen.y,
                               guard_screen.x, guard_screen.x + 1)
            guard_copy.rect = guard_screen
            guard_copy.direction = self.guard.direction
            guard_copy.draw(self.screen)
        if world_view.colliderect(self.player.rect):
            if self.player.has_key:
                self.draw_glow(player_screen.center, (255, 205, 35), 30)
            player_copy = Player(player_screen.x, player_screen.y)
            player_copy.rect = player_screen
            player_copy.has_key = self.player.has_key
            player_copy.draw(self.screen)

        for particle in self.particles:
            particle_copy = Particle(
                particle.x - self.camera_x, particle.y - self.camera_y,
                particle.color, (particle.vx, particle.vy),
                particle.life, particle.radius
            )
            particle_copy.max_life = particle.max_life
            particle_copy.draw(self.screen)
        self.draw_minimap()

        hud_y = VIEW_ROWS * TILE
        hud = pygame.Rect(0, hud_y, WIDTH, HUD_HEIGHT)
        pygame.draw.rect(self.screen, (20, 20, 35), hud)

        status_color = (255, 105, 105) if self.flash_timer else (
            (255, 220, 75) if self.player.has_key else (225, 225, 235)
        )
        status = self.font.render(self.status, True, status_color)
        self.screen.blit(status, (8, hud_y + 10))

        controls = self.small_font.render(
            "WASD/Arrows: Move  |  R: Restart", True, (160, 155, 175)
        )
        self.screen.blit(controls, (8, hud_y + 40))
        self.draw_inventory(hud_y)

        if self.flash_timer > 0:
            flash = pygame.Surface((WIDTH, VIEW_ROWS * TILE), pygame.SRCALPHA)
            flash.set_alpha(10 + self.flash_timer * 2)
            flash.fill(self.flash_color)
            self.screen.blit(flash, (0, 0))

        if self.won:
            overlay = pygame.Surface((WIDTH, VIEW_ROWS * TILE), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))

            msg = self.big_font.render("TREASURE FOUND!", True, (240, 195, 35))
            sub = self.font.render("Press R to Play Again", True, (220, 220, 220))
            self.screen.blit(
                msg, (WIDTH // 2 - msg.get_width() // 2,
                      VIEW_ROWS * TILE // 2 - 30)
            )
            self.screen.blit(
                sub, (WIDTH // 2 - sub.get_width() // 2,
                      VIEW_ROWS * TILE // 2 + 20)
            )

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()


if __name__ == "__main__":
    engine = GameEngine()
    engine.run()
