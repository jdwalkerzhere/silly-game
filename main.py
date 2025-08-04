"""
n*m: height * width -> arbitrarily sized

        |
        V   <- cursor
________________
________________
_____C___A______
___ABCBB_BAA____

{
0: [a, b, c],
1: [b, _, d],
}

{
(0,0): val,
(0,1): val,
(0,2): val,
}
"""

import os
import sys
from dataclasses import dataclass
from random import choice
from typing import Callable

LETTERS = ("A", "B", "C")

@dataclass
class Move:
    key: str
    description: str
    action: Callable


class GameBoard:
    def __init__(self, width: int = 10, height: int = 10, destroy_count: int = 3) -> None:
        self._valid_moves = {
                "h": Move("h", "Move Left", self.cursor_left),
                "l": Move("l", "Move Right",self.cursor_right),
                "i": Move("i", "Drop Letter at Position", self.drop_letter),
                "x": Move("x", "Leave Game", self.quit_game),
        }

        self.width = width
        self.height = height
        self.destroy_count = destroy_count
        self.board = self.build_board()
        self.cursor: int = width // 2
        self.current_letter = self.get_letter()
        self.turn = 0
        self.score = 0
        self.play()


    def __str__(self) -> str:
        board = []
        board.append("".join([" " if i != self.cursor else "|" for i in range(self.width)]) + f"Current Letter: {self.current_letter}")
        board.append("".join([" " if i != self.cursor else "v" for i in range(self.width)]) + f"Turn: {self.turn}")
        for j in range(self.height):
            board.append("".join([self.board[(i,j)] for i in range(self.width)]))
        board.append("".join([" " if i != self.cursor else "^" for i in range(self.width)]))
        board.append("".join([" " if i != self.cursor else "|" for i in range(self.width)]) + f"Score: {self.score}")
        return "\n".join(board)

    def build_board(self) -> dict[tuple[int,int],str]:
        return {(i,j):"_" for i in range(self.width) for j in range(self.height)}

    def get_letter(self) -> str:
        return choice(LETTERS)

    def play(self) -> None:
        while True:
            print(self)
            user_input = input(f"Controls:\n{'\n'.join([f'\t{m.key}: {m.description}' for m in self._valid_moves.values()])}\nInput: ")
            os.system("clear")
            if user_input not in self._valid_moves:
                continue
            self._valid_moves[user_input].action()

    def destroy_matches(self, x: int, y: int, letter: str) -> set[tuple[int,int]]:
        # We need to look left, right, and down
        to_destroy_horizontal = [(x, y)]
        to_destroy_vertical = [(x, y)]
        left = x - 1
        right = x + 1 
        down = y + 1
        while left >= 0 and self.board[(left, y)] == letter:
            to_destroy_horizontal.append((left, y))
            left -= 1
        while right < self.width and self.board[(right, y)] == letter:
            to_destroy_horizontal.append((right, y))
            right += 1
        while down < self.height and self.board[(x, down)] == letter:
            to_destroy_vertical.append((x, down))
            down += 1

        destroyed = set()
        if len(to_destroy_horizontal) >= self.destroy_count:
            for x, y in to_destroy_horizontal:
                destroyed.add((x, y))
                self.board[(x, y)] = "_"
        if len(to_destroy_vertical) >= self.destroy_count:
            for x, y in to_destroy_vertical:
                destroyed.add((x,y))
                self.board[(x, y)] = "_"

        return destroyed

    def drop_supported(self, d_cell: tuple[int, int]) -> None:
        x, curr_y = d_cell
        next_y = curr_y - 1
        while next_y >= 0:
            self.board[(x, curr_y)] = self.board[(x, next_y)]
            curr_y -= 1
            next_y -= 1
        self.board[(x, 0)] = "_"

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
        # Iterate until we find an empty spot
        while y_check >= 0 and self.board[(self.cursor, y_check)] != "_":
            y_check -= 1

        # attempting to place letter on full column
        if y_check == -1:
            return

        self.board[(self.cursor, y_check)] = self.current_letter
        destroyed_cells = self.destroy_matches(self.cursor, y_check, self.current_letter)
        self.score += 10 * len(destroyed_cells)
        self.current_letter = self.get_letter()

        for d_cell in destroyed_cells:
            self.drop_supported(d_cell)

    def quit_game(self) -> None:
        print("Thanks for playing!")
        sys.exit(0)


def main():
    gb = GameBoard(20, 10)

if __name__ == "__main__":
    main()
