import random

import pygame


WIDTH = 640
HEIGHT = 720
TILE_SIZE = 64
PLAYER_Y = HEIGHT - TILE_SIZE * 2

GRASS_COLORS = ("#64b95c", "#5caf55")
CAR_COLORS = ("#e75b4b", "#f2c14e", "#5596e6", "#9b6bd3")


class CrossingGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Crossing Chicken")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 23)
        self.large_font = pygame.font.Font(None, 54)

        self.lane_drawers = {
            "grass": self.draw_grass_lane,
            "road": self.draw_road_lane,
            "water": self.draw_water_lane,
            "rail": self.draw_rail_lane,
        }
        self.collision_checks = {
            "grass": self.check_grass_collision,
            "road": self.check_road_collision,
            "water": self.check_water_collision,
            "rail": self.check_rail_collision,
        }

        self.best_score = 0
        self.reset()

    def reset(self):
        self.player_x = WIDTH / 2
        self.player_row = 0
        self.lanes = {}
        self.game_over = False
        self.ensure_lanes()

    def make_lane(self, row):
        if row <= 0:
            kind = "grass"
        else:
            pattern = [
                "road",
                "road",
                "grass",
                "water",
                "road",
                "rail",
                "grass",
                "water",
                "road",
                "grass",
            ]
            kind = pattern[(row - 1) % len(pattern)]

        rng = random.Random(row * 1009 + 17)
        lane = {
            "kind": kind,
            "direction": rng.choice((-1, 1)),
            "speed": 0,
            "objects": [],
            "train_x": None,
            "train_width": TILE_SIZE * 5,
            "train_timer": 0,
        }

        if kind == "road":
            lane["speed"] = rng.randint(90, 155)
            for index in range(rng.randint(1, 2)):
                width = rng.choice((1.2, 1.4, 1.6)) * TILE_SIZE
                lane["objects"].append(
                    {
                        "x": index * WIDTH / 2 + rng.uniform(0, WIDTH / 2),
                        "width": width,
                        "color": rng.choice(CAR_COLORS),
                    }
                )
        elif kind == "water":
            lane["speed"] = rng.randint(45, 75)
            for index in range(2):
                width = rng.choice((2.5, 2.8, 3.1)) * TILE_SIZE
                lane["objects"].append(
                    {
                        "x": index * WIDTH / 2 + rng.uniform(0, WIDTH / 2),
                        "width": width,
                    }
                )
        elif kind == "rail":
            lane["speed"] = rng.randint(390, 470)
            lane["train_timer"] = rng.uniform(1.5, 4.0)

        return lane

    def ensure_lanes(self):
        first_row = max(-5, self.player_row - 5)
        last_row = self.player_row + 13

        for row in range(first_row, last_row):
            if row not in self.lanes:
                self.lanes[row] = self.make_lane(row)

        for row in list(self.lanes):
            if row < self.player_row - 6:
                del self.lanes[row]

    def move_player(self, key):
        if self.game_over:
            if key == pygame.K_RETURN:
                self.reset()
            return

        if key in (pygame.K_UP, pygame.K_w):
            self.player_row += 1
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.player_row = max(0, self.player_row - 1)
        elif key in (pygame.K_LEFT, pygame.K_a):
            self.player_x = max(TILE_SIZE / 2, self.player_x - TILE_SIZE)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.player_x = min(WIDTH - TILE_SIZE / 2, self.player_x + TILE_SIZE)
        else:
            return

        self.best_score = max(self.best_score, self.player_row)
        self.ensure_lanes()

    def player_rect(self):
        return pygame.Rect(
            round(self.player_x - 16),
            PLAYER_Y + 10,
            32,
            42,
        )

    def player_is_on_log(self, lane):
        player = self.player_rect()

        for item in lane["objects"]:
            log = pygame.Rect(
                round(item["x"] + 4),
                PLAYER_Y + 17,
                round(item["width"] - 8),
                30,
            )
            if player.colliderect(log):
                return True

        return False

    def update_lanes(self, delta_time):
        for lane in self.lanes.values():
            if lane["kind"] in ("road", "water"):
                for item in lane["objects"]:
                    item["x"] += (
                        lane["direction"] * lane["speed"] * delta_time
                    )

                    if lane["direction"] > 0 and item["x"] > WIDTH:
                        item["x"] = -item["width"]
                    elif (
                        lane["direction"] < 0
                        and item["x"] + item["width"] < 0
                    ):
                        item["x"] = WIDTH
            elif lane["kind"] == "rail":
                if lane["train_x"] is None:
                    lane["train_timer"] -= delta_time
                    if lane["train_timer"] <= 0:
                        if lane["direction"] > 0:
                            lane["train_x"] = -lane["train_width"]
                        else:
                            lane["train_x"] = WIDTH
                else:
                    lane["train_x"] += (
                        lane["direction"] * lane["speed"] * delta_time
                    )
                    train_end = lane["train_x"] + lane["train_width"]
                    train_left_screen = (
                        lane["direction"] > 0 and lane["train_x"] > WIDTH
                    )
                    train_right_screen = (
                        lane["direction"] < 0 and train_end < 0
                    )

                    if train_left_screen or train_right_screen:
                        lane["train_x"] = None
                        lane["train_timer"] = random.uniform(3.0, 5.5)

    def check_collision(self):
        lane = self.lanes.get(self.player_row)
        if lane is None:
            return

        collision_check = self.collision_checks.get(lane["kind"])
        if collision_check is None:
            raise ValueError(f"Unknown lane type: {lane['kind']}")

        if collision_check(lane):
            self.end_game()

    def check_grass_collision(self, lane):
        return False

    def check_road_collision(self, lane):
        player = self.player_rect()

        for item in lane["objects"]:
            car = pygame.Rect(
                round(item["x"]),
                PLAYER_Y + 15,
                round(item["width"]),
                35,
            )
            if player.colliderect(car):
                return True

        return False

    def check_water_collision(self, lane):
        return not self.player_is_on_log(lane)

    def check_rail_collision(self, lane):
        if lane["train_x"] is None:
            return False

        train = pygame.Rect(
            round(lane["train_x"]),
            PLAYER_Y + 10,
            lane["train_width"],
            44,
        )
        return self.player_rect().colliderect(train)

    def end_game(self):
        self.game_over = True
        self.best_score = max(self.best_score, self.player_row)

    def draw_lane(self, row, lane, y):
        drawer = self.lane_drawers.get(lane["kind"])
        if drawer is None:
            raise ValueError(f"Unknown lane type: {lane['kind']}")

        drawer(row, lane, y)

    def draw_grass_lane(self, row, lane, y):
        color = GRASS_COLORS[row % 2]
        pygame.draw.rect(self.screen, color, (0, y, WIDTH, TILE_SIZE))

        for x in range(18, WIDTH, 105):
            pygame.draw.line(
                self.screen,
                "#7cca70",
                (x, y + 15),
                (x + 5, y + 10),
                2,
            )

    def draw_road_lane(self, row, lane, y):
        pygame.draw.rect(self.screen, "#414850", (0, y, WIDTH, TILE_SIZE))

        for x in range(0, WIDTH, 36):
            pygame.draw.rect(
                self.screen,
                "#d7d2a4",
                (x, y + TILE_SIZE // 2, 18, 2),
            )

        for item in lane["objects"]:
            x = round(item["x"])
            width = round(item["width"])

            pygame.draw.rect(
                self.screen,
                item["color"],
                (x, y + 15, width, 35),
                border_radius=8,
            )
            pygame.draw.rect(
                self.screen,
                "#c8e8ed",
                (x + round(width * 0.22), y + 19, round(width * 0.5), 12),
            )
            pygame.draw.circle(self.screen, "#20252a", (x + 16, y + 49), 7)
            pygame.draw.circle(
                self.screen,
                "#20252a",
                (x + width - 16, y + 49),
                7,
            )

    def draw_water_lane(self, row, lane, y):
        pygame.draw.rect(self.screen, "#36a9d0", (0, y, WIDTH, TILE_SIZE))

        wave_offset = int(pygame.time.get_ticks() / 1000 * 35) % 70
        for x in range(-70 + wave_offset, WIDTH, 70):
            pygame.draw.line(
                self.screen,
                "#8de0e8",
                (x, y + 13),
                (x + 25, y + 13),
                2,
            )
            pygame.draw.line(
                self.screen,
                "#8de0e8",
                (x + 34, y + 51),
                (x + 58, y + 51),
                2,
            )

        for item in lane["objects"]:
            x = round(item["x"])
            width = round(item["width"])
            log = pygame.Rect(x + 8, y + 18, width - 16, 29)

            pygame.draw.rect(self.screen, "#895a35", log, border_radius=12)
            pygame.draw.circle(self.screen, "#a87545", (x + 12, y + 32), 14)
            pygame.draw.circle(
                self.screen,
                "#a87545",
                (x + width - 12, y + 32),
                14,
            )

            for mark_x in range(x + 35, x + width - 20, 35):
                pygame.draw.line(
                    self.screen,
                    "#68452c",
                    (mark_x, y + 21),
                    (mark_x, y + 44),
                    2,
                )

    def draw_rail_lane(self, row, lane, y):
        pygame.draw.rect(self.screen, "#657769", (0, y, WIDTH, TILE_SIZE))

        for x in range(10, WIDTH, 30):
            pygame.draw.rect(self.screen, "#755e4c", (x, y + 8, 8, 48))

        pygame.draw.line(
            self.screen, "#d4d7d0", (0, y + 20), (WIDTH, y + 20), 4
        )
        pygame.draw.line(
            self.screen, "#d4d7d0", (0, y + 44), (WIDTH, y + 44), 4
        )

        if lane["train_x"] is not None:
            x = round(lane["train_x"])
            train_width = lane["train_width"]

            pygame.draw.rect(
                self.screen,
                "#bd493d",
                (x, y + 10, train_width, 44),
                border_radius=5,
            )

            for car_x in range(x + 22, x + train_width - 12, 58):
                pygame.draw.rect(
                    self.screen,
                    "#b9e3eb",
                    (car_x, y + 17, 30, 15),
                )

            if lane["direction"] > 0:
                front_x = x + train_width - 16
            else:
                front_x = x + 4

            pygame.draw.rect(
                self.screen,
                "#f3c35b",
                (front_x, y + 36, 12, 9),
            )

    def draw_player(self):
        center_x = round(self.player_x)
        center_y = PLAYER_Y + TILE_SIZE // 2

        pygame.draw.ellipse(
            self.screen,
            "#fffdf3",
            (center_x - 20, center_y - 15, 40, 38),
        )
        pygame.draw.circle(
            self.screen,
            "#fffdf3",
            (center_x + 1, center_y - 20),
            13,
        )
        pygame.draw.circle(
            self.screen,
            "#292929",
            (center_x + 5, center_y - 23),
            2,
        )
        pygame.draw.polygon(
            self.screen,
            "#f2a83b",
            [
                (center_x + 10, center_y - 19),
                (center_x + 25, center_y - 15),
                (center_x + 10, center_y - 11),
            ],
        )
        pygame.draw.circle(
            self.screen, "#df554a", (center_x - 5, center_y - 31), 4
        )
        pygame.draw.circle(
            self.screen, "#df554a", (center_x + 3, center_y - 32), 4
        )
        pygame.draw.line(
            self.screen,
            "#d88832",
            (center_x - 8, center_y + 17),
            (center_x - 15, center_y + 23),
            3,
        )
        pygame.draw.line(
            self.screen,
            "#d88832",
            (center_x + 8, center_y + 17),
            (center_x + 15, center_y + 23),
            3,
        )

    def draw_text(self, text, font, color, position, center=False):
        image = font.render(text, True, color)
        rect = image.get_rect()

        if center:
            rect.center = position
        else:
            rect.topleft = position

        self.screen.blit(image, rect)

    def draw(self):
        self.screen.fill("#64b95c")

        first_row = self.player_row - 5
        last_row = self.player_row + 7

        for row in range(first_row, last_row + 1):
            lane = self.lanes.get(row)
            if lane is None:
                continue

            y = PLAYER_Y + (self.player_row - row) * TILE_SIZE
            self.draw_lane(row, lane, y)

        self.draw_player()

        pygame.draw.rect(
            self.screen, "#263238", (12, 12, 245, 42), border_radius=6
        )
        self.draw_text(
            f"Scor: {self.player_row}    Record: {self.best_score}",
            self.font,
            "white",
            (23, 21),
        )
        self.draw_text(
            "WASD / sageti",
            self.small_font,
            "white",
            (WIDTH - 145, 20),
        )

        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            self.screen.blit(overlay, (0, 0))

            pygame.draw.rect(
                self.screen,
                "#202a33",
                (75, 265, WIDTH - 150, 180),
                border_radius=12,
            )
            pygame.draw.rect(
                self.screen,
                "white",
                (75, 265, WIDTH - 150, 180),
                width=2,
                border_radius=12,
            )

            self.draw_text(
                "Joc terminat!",
                self.large_font,
                "white",
                (WIDTH // 2, 315),
                center=True,
            )
            self.draw_text(
                f"Ai ajuns la scorul {self.player_row}",
                self.font,
                "white",
                (WIDTH // 2, 365),
                center=True,
            )
            self.draw_text(
                "Apasa ENTER pentru a incerca din nou",
                self.small_font,
                "#f5d477",
                (WIDTH // 2, 410),
                center=True,
            )

        pygame.display.flip()

    def run(self):
        running = True

        while running:
            delta_time = min(self.clock.tick(60) / 1000, 0.08)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.move_player(event.key)

            if not self.game_over:
                lane = self.lanes.get(self.player_row)
                riding_speed = 0

                if lane is not None and lane["kind"] == "water":
                    if self.player_is_on_log(lane):
                        riding_speed = lane["direction"] * lane["speed"]

                self.update_lanes(delta_time)

                if riding_speed:
                    self.player_x += riding_speed * delta_time

                if not TILE_SIZE / 2 <= self.player_x <= WIDTH - TILE_SIZE / 2:
                    self.end_game()

                self.check_collision()
                self.ensure_lanes()

            self.draw()

        pygame.quit()


if __name__ == "__main__":
    CrossingGame().run()
