import os
import sys
from dataclasses import dataclass
from queue import Queue
from random import choice
from typing import Callable, Union

from pynput import keyboard

LETTERS = ("A", "B", "C")

@dataclass
class Move:
    key: str
    description: str
    action: Callable


@dataclass
class Cell:
    value: str
    color: str


class GameBoard:
    def __init__(self, width: int = 10, height: int = 10, 
                 destroy_count: int = 3, starting_board: Union[str, None] = None) -> None:
        self._valid_moves = {
                "h": Move("h", "Move Left", self.cursor_left),
                "l": Move("l", "Move Right",self.cursor_right),
                "i": Move("i", "Drop Letter at Position", self.drop_letter),
                "x": Move("x", "Leave Game", self.quit_game),
        }

        self.width = width
        self.height = height
        self.destroy_count = destroy_count
        self.cursor: int = width // 2

        self.board = self.build_board(starting_board)
        self.current_letter = self.get_letter()

        self.turn = 0
        self.score = 0

        self.queue = Queue()
        self.listener = keyboard.Listener(on_press=self._on_press, suppress=True)
        self.listener.start()

        self.play()


    def __str__(self) -> str:
        board = []
        board.append("".join([" " if i != self.cursor else "|" for i in range(self.width)]) + f"Current Letter: {self.current_letter}")
        board.append("".join([" " if i != self.cursor else "v" for i in range(self.width)]) + f"Turn: {self.turn}")
        for j in range(self.height):
            board.append("".join([self.board[(i,j)] for i in range(self.width)]))
        board.append("".join([" " if i != self.cursor else "^" for i in range(self.width)]))
        board.append("".join([" " if i != self.cursor else "|" for i in range(self.width)]) + f"Score: {self.score}")
        controls = '\n'.join([f'\t{m.key}: {m.description}' for m in self._valid_moves.values()])
        board.append(f"Controls:\n{controls}")
        board.append("Input: ")
        return "\n".join(board)

    def build_board(self, starting_board: Union[str, None] = None) -> dict[tuple[int,int],str]:
        if starting_board:
            raise NotImplementedError
        return {(i,j):"_" for i in range(self.width) for j in range(self.height)}

    def get_letter(self) -> str:
        return choice(LETTERS)

    def render(self) -> None:
        os.system("clear")
        print(self)

    def play(self) -> None:
        while True:
            self.render()
            user_input = self.queue.get()
            if user_input not in self._valid_moves:
                continue
            self._valid_moves[user_input].action()

    def _on_press(self, key):
        try:
            if hasattr(key, "char") and key.char not in self._valid_moves:
                return
            if hasattr(key, "char"):
                self.queue.put(key.char)
        except AttributeError:
            pass


    def destroy_matches(self, x: int, y: int, letter: str) -> None:
        """
        """
        if letter == "_":
            return

        left = x
        while left >= 0 and self.board[(left, y)] == letter:
            left -= 1

        right = x 
        while right < self.width and self.board[(right, y)] == letter:
            right += 1

        down = y
        while down < self.height and self.board[(x, down)] == letter:
            down += 1

        destroyed = set()
        if right - left > self.destroy_count:
            for i in range(left + 1, right):
                destroyed.add((i, y))
        if down - y >= self.destroy_count:
            for j in range(y, down):
                destroyed.add((x, j))

        self.score += 10 * len(destroyed)
        new_candidates = []
        for d_cell in sorted(destroyed, key=lambda x: x[1]):
            new_candidates.extend(self.drop_supported(d_cell))

        for cell in new_candidates:
            x, y = cell
            letter = self.board[cell]
            self.destroy_matches(x, y, letter)

    def drop_supported(self, d_cell: tuple[int, int]) -> list[tuple[int, int]]:
        x, curr_y = d_cell
        next_y = curr_y - 1

        if curr_y == 0 or self.board[(x, next_y)] == "_":
            self.board[(x, curr_y)] = "_"
            return []

        new_candidates = [(x, curr_y)]
        self.board[(x, curr_y)] = self.board[(x, next_y)]
        new_candidates.extend(self.drop_supported((x, next_y)))
        return new_candidates

    def cursor_left(self) -> None:
        assert 0 <= self.cursor <= self.width - 1
        if self.cursor == 0:
            return
        self.cursor -= 1

    def cursor_right(self) -> None:
        assert 0 <= self.cursor <= self.width - 1
        if self.cursor == self.width - 1:
            return
        self.cursor += 1

    def drop_letter(self) -> None:
        y_check = self.height - 1

        while y_check >= 0 and self.board[(self.cursor, y_check)] != "_":
            y_check -= 1

        if y_check == -1:
            return

        self.board[(self.cursor, y_check)] = self.current_letter
        self.destroy_matches(self.cursor, y_check, self.board[(self.cursor, y_check)])
        self.current_letter = self.get_letter()
        self.turn += 1

    def quit_game(self) -> None:
        self.listener.stop()
        print("Thanks for playing!")
        sys.exit(0)


def main():
    GameBoard(20, 10)

if __name__ == "__main__":
    main()
