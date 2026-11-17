import random
import time
import tkinter as tk


WIDTH = 640
HEIGHT = 720
TILE_SIZE = 64
COLUMN_COUNT = WIDTH // TILE_SIZE
PLAYER_SCREEN_Y = HEIGHT - TILE_SIZE * 2


class CrossingGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Crossing Chicken")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            root,
            width=WIDTH,
            height=HEIGHT,
            background="#64b95c",
            highlightthickness=0,
        )
        self.canvas.pack()
        self.canvas.focus_set()
        self.root.bind("<KeyPress>", self.on_key_press)

        self.best_score = 0
        self.last_frame_time = time.perf_counter()
        self.next_move_time = 0
        self.reset()
        self.root.after(33, self.update)

    def reset(self):
        self.player_x = COLUMN_COUNT / 2
        self.player_row = 0
        self.lanes = {}
        self.game_over = False
        self.next_move_time = 0
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
                spacing = WIDTH / 2
                lane["objects"].append(
                    {
                        "x": index * spacing + rng.uniform(0, spacing),
                        "width": width,
                        "color": rng.choice(
                            ("#e75b4b", "#f2c14e", "#5596e6", "#9b6bd3")
                        ),
                    }
                )
        elif kind == "water":
            lane["speed"] = rng.randint(45, 75)
            for index in range(2):
                width = rng.choice((2.5, 2.8, 3.1)) * TILE_SIZE
                spacing = WIDTH / 2
                lane["objects"].append(
                    {
                        "x": index * spacing + rng.uniform(0, spacing),
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

    def on_key_press(self, event):
        key = event.keysym.lower()
        if self.game_over:
            if key in ("return", "enter"):
                self.reset()
            return

        now = time.perf_counter()
        if now < self.next_move_time:
            return

        if key in ("up", "w"):
            self.player_row += 1
        elif key in ("down", "s"):
            self.player_row = max(0, self.player_row - 1)
        elif key in ("left", "a"):
            self.player_x = max(0.5, self.player_x - 1)
        elif key in ("right", "d"):
            self.player_x = min(COLUMN_COUNT - 0.5, self.player_x + 1)
        else:
            return

        self.next_move_time = now + 0.11
        self.best_score = max(self.best_score, self.player_row)
        self.ensure_lanes()

    def update_lanes(self, delta_time):
        for lane in self.lanes.values():
            if lane["kind"] in ("road", "water"):
                for item in lane["objects"]:
                    item["x"] += lane["direction"] * lane["speed"] * delta_time
                    if lane["direction"] > 0 and item["x"] > WIDTH:
                        item["x"] = -item["width"]
                    elif lane["direction"] < 0 and item["x"] + item["width"] < 0:
                        item["x"] = WIDTH
            elif lane["kind"] == "rail":
                if lane["train_x"] is None:
                    lane["train_timer"] -= delta_time
                    if lane["train_timer"] <= 0:
                        lane["train_x"] = (
                            -lane["train_width"]
                            if lane["direction"] > 0
                            else WIDTH
                        )
                else:
                    lane["train_x"] += (
                        lane["direction"] * lane["speed"] * delta_time
                    )
                    train_end = lane["train_x"] + lane["train_width"]
                    if (
                        lane["direction"] > 0
                        and lane["train_x"] > WIDTH
                    ) or (
                        lane["direction"] < 0
                        and train_end < 0
                    ):
                        lane["train_x"] = None
                        lane["train_timer"] = random.uniform(3.0, 5.5)

    def player_is_on_log(self, lane):
        player_center = self.player_x * TILE_SIZE
        return any(
            item["x"] <= player_center <= item["x"] + item["width"]
            for item in lane["objects"]
        )

    def check_collision(self):
        lane = self.lanes.get(self.player_row)
        if lane is None:
            return

        player_center = self.player_x * TILE_SIZE
        if lane["kind"] == "road":
            hit = any(
                item["x"] <= player_center <= item["x"] + item["width"]
                for item in lane["objects"]
            )
            if hit:
                self.end_game()
        elif lane["kind"] == "water" and not self.player_is_on_log(lane):
            self.end_game()
        elif lane["kind"] == "rail" and lane["train_x"] is not None:
            train_end = lane["train_x"] + lane["train_width"]
            if lane["train_x"] <= player_center <= train_end:
                self.end_game()

    def end_game(self):
        self.game_over = True
        self.best_score = max(self.best_score, self.player_row)

    def draw_lane(self, row, lane, y):
        kind = lane["kind"]
        if kind == "grass":
            color = "#64b95c" if row % 2 == 0 else "#5caf55"
            self.canvas.create_rectangle(
                0, y, WIDTH, y + TILE_SIZE, fill=color, outline=""
            )
            for x in range(18, WIDTH, 105):
                self.canvas.create_line(
                    x, y + 15, x + 5, y + 10, fill="#7cca70", width=2
                )
        elif kind == "road":
            self.canvas.create_rectangle(
                0, y, WIDTH, y + TILE_SIZE, fill="#414850", outline=""
            )
            self.canvas.create_line(
                0,
                y + TILE_SIZE / 2,
                WIDTH,
                y + TILE_SIZE / 2,
                fill="#d7d2a4",
                width=2,
                dash=(18, 16),
            )
            for item in lane["objects"]:
                x = item["x"]
                width = item["width"]
                self.canvas.create_rectangle(
                    x,
                    y + 15,
                    x + width,
                    y + 50,
                    fill=item["color"],
                    outline="#26313b",
                    width=2,
                )
                self.canvas.create_rectangle(
                    x + width * 0.22,
                    y + 19,
                    x + width * 0.72,
                    y + 31,
                    fill="#c8e8ed",
                    outline="",
                )
                self.canvas.create_oval(
                    x + 10, y + 44, x + 23, y + 57, fill="#20252a", outline=""
                )
                self.canvas.create_oval(
                    x + width - 23,
                    y + 44,
                    x + width - 10,
                    y + 57,
                    fill="#20252a",
                    outline="",
                )
        elif kind == "water":
            self.canvas.create_rectangle(
                0, y, WIDTH, y + TILE_SIZE, fill="#36a9d0", outline=""
            )
            wave_offset = int(time.perf_counter() * 35) % 70
            for x in range(-70 + wave_offset, WIDTH, 70):
                self.canvas.create_line(
                    x, y + 13, x + 25, y + 13, fill="#8de0e8", width=2
                )
                self.canvas.create_line(
                    x + 34, y + 51, x + 58, y + 51, fill="#8de0e8", width=2
                )
            for item in lane["objects"]:
                x = item["x"]
                width = item["width"]
                self.canvas.create_rectangle(
                    x + 8,
                    y + 18,
                    x + width - 8,
                    y + 47,
                    fill="#895a35",
                    outline="#583a25",
                    width=2,
                )
                self.canvas.create_oval(
                    x, y + 18, x + 18, y + 47, fill="#a87545", outline="#583a25"
                )
                self.canvas.create_oval(
                    x + width - 18,
                    y + 18,
                    x + width,
                    y + 47,
                    fill="#a87545",
                    outline="#583a25",
                )
                for mark_x in range(int(x + 35), int(x + width - 20), 35):
                    self.canvas.create_line(
                        mark_x, y + 21, mark_x, y + 44, fill="#68452c", width=2
                    )
        else:
            self.canvas.create_rectangle(
                0, y, WIDTH, y + TILE_SIZE, fill="#657769", outline=""
            )
            for x in range(10, WIDTH, 30):
                self.canvas.create_rectangle(
                    x, y + 8, x + 8, y + 56, fill="#755e4c", outline=""
                )
            self.canvas.create_line(
                0, y + 20, WIDTH, y + 20, fill="#d4d7d0", width=4
            )
            self.canvas.create_line(
                0, y + 44, WIDTH, y + 44, fill="#d4d7d0", width=4
            )
            if lane["train_x"] is not None:
                x = lane["train_x"]
                train_width = lane["train_width"]
                self.canvas.create_rectangle(
                    x,
                    y + 10,
                    x + train_width,
                    y + 54,
                    fill="#bd493d",
                    outline="#71342f",
                    width=3,
                )
                for car_x in range(int(x + 22), int(x + train_width - 12), 58):
                    self.canvas.create_rectangle(
                        car_x,
                        y + 17,
                        car_x + 30,
                        y + 32,
                        fill="#b9e3eb",
                        outline="",
                    )
                front_x = (
                    x + train_width - 16
                    if lane["direction"] > 0
                    else x + 4
                )
                self.canvas.create_rectangle(
                    front_x, y + 36, front_x + 12, y + 45, fill="#f3c35b", outline=""
                )

    def draw_player(self):
        x = self.player_x * TILE_SIZE
        y = PLAYER_SCREEN_Y
        self.canvas.create_oval(
            x - 20, y - 25, x + 20, y + 22, fill="#fffdf3", outline="#d8d6ca", width=2
        )
        self.canvas.create_oval(
            x - 11, y - 43, x + 13, y - 18, fill="#fffdf3", outline="#d8d6ca", width=2
        )
        self.canvas.create_oval(
            x + 3, y - 36, x + 7, y - 32, fill="#292929", outline=""
        )
        self.canvas.create_polygon(
            x + 10,
            y - 30,
            x + 25,
            y - 25,
            x + 10,
            y - 21,
            fill="#f2a83b",
            outline="#c47b22",
        )
        self.canvas.create_oval(
            x - 8, y - 49, x - 2, y - 41, fill="#df554a", outline=""
        )
        self.canvas.create_oval(
            x, y - 51, x + 7, y - 42, fill="#df554a", outline=""
        )
        self.canvas.create_line(
            x - 8, y + 18, x - 15, y + 24, fill="#d88832", width=3
        )
        self.canvas.create_line(
            x + 8, y + 18, x + 15, y + 24, fill="#d88832", width=3
        )

    def draw(self):
        self.canvas.delete("all")
        first_row = self.player_row - 5
        last_row = self.player_row + 7
        for row in range(first_row, last_row + 1):
            lane = self.lanes.get(row)
            if lane is None:
                continue
            y = PLAYER_SCREEN_Y + (self.player_row - row) * TILE_SIZE
            self.draw_lane(row, lane, y)

        self.draw_player()
        self.canvas.create_rectangle(
            12, 12, 240, 52, fill="#263238", outline="", stipple="gray50"
        )
        self.canvas.create_text(
            25,
            32,
            anchor="w",
            text=f"Scor: {self.player_row}    Record: {self.best_score}",
            fill="white",
            font=("Arial", 14, "bold"),
        )
        self.canvas.create_text(
            WIDTH - 14,
            25,
            anchor="e",
            text="WASD / sageti",
            fill="white",
            font=("Arial", 11, "bold"),
        )

        if self.game_over:
            self.canvas.create_rectangle(
                85, 270, WIDTH - 85, 435, fill="#202a33", outline="#ffffff", width=2
            )
            self.canvas.create_text(
                WIDTH / 2,
                315,
                text="Joc terminat!",
                fill="white",
                font=("Arial", 28, "bold"),
            )
            self.canvas.create_text(
                WIDTH / 2,
                360,
                text=f"Ai ajuns la scorul {self.player_row}",
                fill="white",
                font=("Arial", 15),
            )
            self.canvas.create_text(
                WIDTH / 2,
                400,
                text="Apasa ENTER pentru a incerca din nou",
                fill="#f5d477",
                font=("Arial", 13, "bold"),
            )

    def update(self):
        now = time.perf_counter()
        delta_time = min(now - self.last_frame_time, 0.08)
        self.last_frame_time = now

        if not self.game_over:
            lane = self.lanes.get(self.player_row)
            riding_speed = 0
            if lane is not None and lane["kind"] == "water":
                if self.player_is_on_log(lane):
                    riding_speed = lane["direction"] * lane["speed"]
                else:
                    self.end_game()

            self.update_lanes(delta_time)
            if riding_speed:
                self.player_x += riding_speed * delta_time / TILE_SIZE
                if not 0.5 <= self.player_x <= COLUMN_COUNT - 0.5:
                    self.end_game()

            self.check_collision()
            self.ensure_lanes()

        self.draw()
        self.root.after(33, self.update)


def main():
    root = tk.Tk()
    CrossingGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
