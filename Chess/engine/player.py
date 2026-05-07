import os

class Player:
    wins = 0
    loses = 0

    def __init__(self):
        self.name = ""
        self.win_percentage = 0.0
        self.stats = []
        self.filename = "players.txt"

    def set_name(self):
        # self.name = input("Enter a username: ")
        self.name = "S"

    @classmethod
    def increase_wins(cls):
        cls.wins += 1

    @classmethod
    def increase_loses(cls):
        cls.loses += 1

    def read_file(self):
        found = False
        if not os.path.exists(self.filename):
            open(self.filename, 'w').close()
            
        with open(self.filename, "r") as file:
            for line in file:
                line = line.strip()
                if line:
                    self.stats.append(line)

        for element in self.stats:
            if self.name in element:
                parts = element.split(" ")
                Player.wins = int(parts[1])
                Player.loses = int(parts[2])
                self.win_percentage = float(parts[3])
                found = True

        if not found:
            self.stats.append(f"{self.name} {Player.wins} {Player.loses} {self.win_percentage}")

    def update_line(self):
        self.calc_win_per()
        with open(self.filename, "w") as out:
            for i in range(len(self.stats)):
                if self.name in self.stats[i]:
                    self.stats[i] = f"{self.name} {Player.wins} {Player.loses} {self.win_percentage}"
                out.write(self.stats[i] + "\n")

    def calc_win_per(self):
        if Player.loses == 0:
            self.win_percentage = float(Player.wins)
        else:
            self.win_percentage = (Player.wins * 1.0) / (Player.wins + Player.loses)

    def __str__(self):
        return f"{self.name}: Wins: {Player.wins} Loses: {Player.loses} Win Percentage: {self.win_percentage}"

    def close_file(self):
        pass # Automatically handled by context managers during writing/reading!
