import wordy
from wordy import get_board_state, make_guess, get_word_list, get_display_spec, DisplaySpecification
from PIL import Image


class Letter:
    def __init__(self, letter: str):
        self.letter = letter
        self.in_correct_place = False
        self.in_word = False

    def is_in_correct_place(self) -> bool:
        return self.in_correct_place

    def is_in_word(self) -> bool:
        return self.in_word


def _tuple_to_str(pixels: tuple) -> str:
    return "#{:02X}{:02X}{:02X}".format(pixels[0], pixels[1], pixels[2])


def _process_image(board_image: Image, word_length: int, num_rows: int, spec: DisplaySpecification) -> list:
    """Read every row of the board and return list of lists of Letter results.
    Since we don't know the actual guessed letters from the image alone,
    we return just the color codes per position per row."""
    row_height = spec.block_height
    all_rows = []

    for row in range(num_rows):
        row_colors = []
        for i in range(word_length):
            x = i * (spec.block_width + spec.space_between_letters) + spec.block_width // 2
            y = row * row_height + row_height // 2
            pixel = board_image.getpixel((x, y))
            row_colors.append(_tuple_to_str(pixel))
        all_rows.append(row_colors)

    return all_rows


def _is_valid_word(word, correct_positions, in_word_letters, absent_letters, wrong_positions):
    """Check if a word satisfies all constraints we know so far."""
    # must have correct letters in correct positions
    for pos, letter in correct_positions.items():
        if word[pos] != letter:
            return False

    # must contain all letters known to be in the word
    for letter in in_word_letters:
        if letter not in word:
            return False

    # must not contain absent letters
    for letter in absent_letters:
        if letter in word:
            return False

    # must not have in_word letters in their known wrong positions
    for pos, letter in wrong_positions:
        if word[pos] == letter:
            return False

    return True


def _score_word(word, in_word_letters, absent_letters, correct_positions):
    """Score a word by how many new unique letters it introduces — more = better."""
    known = in_word_letters | absent_letters | set(correct_positions.values())
    return len(set(word) - known)


def solution(board_image: Image) -> str:
    """Read the board state and return the next best guess."""
    spec = get_display_spec()
    word_list = get_word_list()

    # figure out word length and number of rows from image dimensions
    img_width, img_height = board_image.size
    word_length = (img_width + spec.space_between_letters) // (spec.block_width + spec.space_between_letters)
    num_rows = img_height // spec.block_height

    # filter word list to correct length
    candidates = [w for w in word_list if len(w) == word_length]

    # read color of every tile on the board
    all_rows = _process_image(board_image, word_length, num_rows, spec)

    # build knowledge from previous guesses
    correct_positions = {}   # {position: letter}
    in_word_letters  = set()
    absent_letters   = set()
    wrong_positions  = set()

    # access wordy's internal guess history
    guessed_words = wordy.__dict__.get('_WordyPy__last_guesses',
                    wordy.__dict__.get('__last_guesses',
                    wordy.__dict__.get('_wordy__last_guesses', [])))

    if guessed_words and len(guessed_words) == num_rows:
        for row_idx, guess in enumerate(guessed_words):
            row_colors = all_rows[row_idx]
            for pos, color in enumerate(row_colors):
                letter = guess[pos]
                if color == spec.correct_location_color:
                    correct_positions[pos] = letter
                    in_word_letters.add(letter)
                elif color == spec.incorrect_location_color:
                    in_word_letters.add(letter)
                    wrong_positions.add((pos, letter))
                else:
                    if letter not in in_word_letters:
                        absent_letters.add(letter)

    # filter candidates using everything we know
    valid_words = [
        w for w in candidates
        if _is_valid_word(w, correct_positions, in_word_letters, absent_letters, wrong_positions)
        and w not in (guessed_words or [])
    ]

    # fallback if no valid words found
    if not valid_words:
        valid_words = [w for w in candidates if w not in (guessed_words or [])]

    # pick word that maximises new unique letters
    best_guess = max(valid_words, key=lambda w: _score_word(w, in_word_letters, absent_letters, correct_positions))

    return best_guess




#FOLLOWING IS THE TESTING CELL GIVEN BY COURSERA TO CHECK THE GAME WITH 5 SIMPLE GUESSES:-

# The autograder for this assignment is easy, it will try and play
# a few rounds of the game and ensure that errors are not thrown. If
# you can make it through five rounds we'll assume you have the right
# solution!
#
# You SHOULD NOT change anything in the wordy module, instead you
# must figure out how to write the solution() function in this notebook
# to make a good guess based on the board state!

for i in range(5):
    try:
        # Get an image of the current board state from wordy.
        # Note that the image contains some number of random guesses (always less than 5 guesses).
        image = wordy.get_board_state()
        # Create a new *good* guess based on the image and rules of wordy
        new_guess = solution(image)  # your code goes in solution()!
        # Send that guess to wordy to make sure it doesn't throw any errors
        wordy.make_guess(new_guess)
    except Exception as e:
        raise e
