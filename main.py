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
    """
    Dataclass used to populate the `_valid_moves` member of the `GameBoard` class.

    Fields:
    - key: `str` - The actual keyboard key press associated with the action
    - description: `str` - (unsurprisingly) describes the action
    - action: `typing.Callable` - functions to navigate the board, drop letters, or exit the game
    """
    key: str
    description: str
    action: Callable


class GameBoard:
    """
    GameBoard represents the entirity of the Letter Crush game. It should likely be renamed to Letter Crush for this reason.

    The game is simple, given some set of letters you need to line them up either vertically or horizontally. If the number
    you have lined up is greater than the `destroy_count` member (defaults to 3), those letters get destroyed. Probably most
    interesting is that upon crushing some letters, new letters could fall into alignments that cause cascading crushes.

    TO DO:
        - Implement a `starting_board` functionality so that a board can be populated from an existing file.
        - Implement some nicer representation of when letters get crushed (print them red, sleep, drop letters, print again)
        - Fina a more performant way to print the board, I don't want to iterate through it each render if state hasn't changed
            - of note can't cache the board
        - Find a more performant way to do letter destruction without passing a ton of data around
    """
    def __init__(self, width: int = 10, height: int = 10, 
                 destroy_count: int = 3, starting_board: Union[str, None] = None) -> None:
        self._valid_moves = {
                "h": Move("h", "Move Left", self.cursor_left),
                "l": Move("l", "Move Right",self.cursor_right),
                "i": Move("i", "Drop Letter at Position", self.drop_letter),
                "x": Move("x", "Leave Game", self.quit_game),
        }
        self._controls_string = '\n'.join([f'\t{m.key}: {m.description}' for m in self._valid_moves.values()])

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
        """
        A highly inefficient way to fetch and display the game board's state
        """
        board = []
        board.append("".join([" " if i != self.cursor else "|" for i in range(self.width)]) + f"Current Letter: {self.current_letter}")
        board.append("".join([" " if i != self.cursor else "v" for i in range(self.width)]) + f"Turn: {self.turn}")
        for j in range(self.height):
            board.append("".join([self.board[(i,j)] for i in range(self.width)]))
        board.append("".join([" " if i != self.cursor else "^" for i in range(self.width)]))
        board.append("".join([" " if i != self.cursor else "|" for i in range(self.width)]) + f"Score: {self.score}")
        board.append(f"Controls:\n{self._controls_string}")
        board.append("Input: ")
        return "\n".join(board)

    def build_board(self, starting_board: Union[str, None] = None) -> dict[tuple[int,int],str]:
        """
        Builds the initial game board state and stores it, only caller is `__init__`.

        Eventually will support receiving an existing game board (probably stored in a `.games/game_number.txt`
        or some JSON blob. Will just take the file, parse it (error if some invalid state is found), and store it.

        Arguments:
        - starting_board: `Union[str, None]` - Currently raises NotImplementedError

        Returns:
        `dict[tuple[int, int]str]` - Represents the board state
        """
        if starting_board:
            raise NotImplementedError
        return {(i,j):"_" for i in range(self.width) for j in range(self.height)}

    def get_letter(self) -> str:
        """
        Fetches a random letter from constant `LETTERS` using `random.choice`

        Returns:
        `str` - Whatever random letter was selected from `LETTERS`
        """
        return choice(LETTERS)

    def render(self) -> None:
        """
        Clears out the terminal and prints the current board state to stdout.

        Works beautifully well on iTerm2, but some terminal emulators (such as Warp)
        seem to struggle with clearing the screen and printing in the case of rapid
        user input.
        """
        os.system("clear")
        print(self)

    def play(self) -> None:
        """
        The primary game loop. Pretty self-explanatory:
        - render the board
        - blocking until user presses a key
        - check for and execute the appropriate move, if valid
        """
        while True:
            self.render()
            user_input = self.queue.get()
            if user_input not in self._valid_moves:
                continue
            self._valid_moves[user_input].action()

    def _on_press(self, key):
        """
        The callback method `self.listener` uses to grab user keystrokes.

        Doesn't support any special keys. Places useful keystrokes on `self.queue`.
        """
        try:
            if hasattr(key, "char") and key.char not in self._valid_moves:
                return
            if hasattr(key, "char"):
                self.queue.put(key.char)
        # Pressed a special key (such as arrows, return, etc) -> Obviously do nothing
        except AttributeError:
            pass


    def check_and_destroy_matches(self, x: int, y: int, letter: str, depth: int = 1) -> None:
        """
        Recursive method that:
        1. Checks for matches horizontally and vertically at the given (x,y) coordinates (three pointer method)
        2. Confirms matches in both directions exceed the `destroy_count` member, add those to a set for removal
        3. Increment the score (cascading crushes get a multiplier)
        4. Iteratively call to `drop_supported` to populate a list of new candidate cells for deletion (necessary because of cascades)
        5. Calls itself with each new candidate coordinate pair and cascades crushes if needed
            - The above could likely be memoized in some way to avoid redundant match-checking

        Arguments:
        - x: `int` - The location the check starts on the horizontal axis of the board
        - y: `int` - The location the check starts on the vertical axis of the board
        - letter: `str` - The letter we are checking for matches against
        - depth: `int` - the score multiplier (for the case of cascading crushes)

        Modifies:
        `self.board`
        `self.score`
        """
        if letter == "_":
            return

        # Look left for letter matches
        left = x
        while left >= 0 and self.board[(left, y)] == letter:
            left -= 1

        # Look right for letter matches
        right = x 
        while right < self.width and self.board[(right, y)] == letter:
            right += 1

        # Look down for letter matches
        down = y
        while down < self.height and self.board[(x, down)] == letter:
            down += 1

        destroyed = set()
        # Confirm windows of matches are greater than `destroy_count`
        if right - left > self.destroy_count:
            for i in range(left + 1, right):
                destroyed.add((i, y))
        if down - y >= self.destroy_count:
            for j in range(y, down):
                destroyed.add((x, j))

        # Update score
        self.score += 10 * len(destroyed) * depth

        new_candidates = []

        # This sort is necessary for vertical crushes to work
        for d_cell in sorted(destroyed, key=lambda x: x[1]):
            # It is also necessary to do all possible drops before attempting cascading crushes
            new_candidates.extend(self.drop_supported(d_cell))

        # Recursively check and delete any new cascading matches
        for cell in new_candidates:
            x, y, letter = *cell, self.board[cell]
            self.check_and_destroy_matches(x, y, letter, depth + 1)

    def drop_supported(self, d_cell: tuple[int, int]) -> list[tuple[int, int]]:
        """
        This recursive method is responsible for taking an (x,y) coordinate pair and 'looking up'.

        In the condition that we are already at the top of the board or the next cell up is already
        empty, we can just set our current cell to empty (effectively dropping the existing value)
        and return no new candidates for match checking.

        Otherwise, the cell above the current coordinates contains a letter. In this case we drop
        that value into our current cell and recursively (depth first) populate a new list of 
        cells that we need to match check for deletion.

        Arguments:
        d_cell: `tuple[int, int]` - the (x,y) coordinate pair we need to 'delete'

        Modifies:
        `self.board`
        """
        x, curr_y = d_cell
        next_y = curr_y - 1

        # If you're at the top or empty cell above, set current cell empty and return
        if curr_y == 0 or self.board[(x, next_y)] == "_":
            self.board[(x, curr_y)] = "_"
            return []

        # Some value exists above, move it down and recursively shift cells down
        new_candidates = [(x, curr_y)]
        self.board[(x, curr_y)] = self.board[(x, next_y)]
        new_candidates.extend(self.drop_supported((x, next_y)))

        # Return new possible candidates for match checking and cascading deletions
        return new_candidates

    def cursor_left(self) -> None:
        """
        The callback for "Move Left" keyboard inputs.

        Modifies:
        `self.cursor`
        """
        assert 0 <= self.cursor <= self.width - 1  # Asserting against impossible behavior
        if self.cursor == 0:
            return
        self.cursor -= 1

    def cursor_right(self) -> None:
        """
        The callback for "Move Right" keyboard inputs.

        Modifies:
        `self.cursor`
        """
        assert 0 <= self.cursor <= self.width - 1  # Asserting against impossible behavior
        if self.cursor == self.width - 1:
            return
        self.cursor += 1

    def drop_letter(self) -> None:
        """
        The callback for "Drop Letter at Position" keyboard inputs.

        1. Checks where a letter should be set vertically
        2. Places the letter
        3. Calls `check_and_destroy_matches` on that cell with that letter
        4. Updates the `current_letter` field
        5. Increments the `turn` member

        Modifies:
        `self.board` <- Indirectly via `check_and_destroy_matches`
        `self.current_letter`
        `self.turn`
        """
        y_check = self.height - 1

        while y_check >= 0 and self.board[(self.cursor, y_check)] != "_":
            y_check -= 1

        if y_check == -1:
            return

        self.board[(self.cursor, y_check)] = self.current_letter
        self.check_and_destroy_matches(self.cursor, y_check, self.board[(self.cursor, y_check)])
        self.current_letter = self.get_letter()
        self.turn += 1

    def quit_game(self) -> None:
        """
        The callback for "Leave Game" keyboard inputs.
        """
        self.listener.stop()
        print("Thanks for playing!")
        sys.exit(0)


def main():
    GameBoard()

if __name__ == "__main__":
    main()
