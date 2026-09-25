
# Tic-Tac-Toe Game
# Two-player console game

board = [" ", " ", " ", " ", " ", " ", " ", " ", " "]


def display_board():
    print()
    print(" " + board[0] + " | " + board[1] + " | " + board[2])
    print("---+---+---")
    print(" " + board[3] + " | " + board[4] + " | " + board[5])
    print("---+---+---")
    print(" " + board[6] + " | " + board[7] + " | " + board[8])
    print()


def check_winner(player):
    combinations = [
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6)
    ]

    for a, b, c in combinations:
        if board[a] == player and board[b] == player and board[c] == player:
            return True

    return False


def check_draw():
    return " " not in board


def play_game():
    current_player = "X"

    print("TIC-TAC-TOE")
    print("Player 1 = X")
    print("Player 2 = O")

    print("\nChoose positions using these numbers:")
    print(" 1 | 2 | 3")
    print("---+---+---")
    print(" 4 | 5 | 6")
    print("---+---+---")
    print(" 7 | 8 | 9")

    while True:
        display_board()

        try:
            position = int(input("Player " + current_player +
                                 ", choose a position (1-9): "))

            if position < 1 or position > 9:
                print("Please enter a number from 1 to 9.")
                continue

            index = position - 1

            if board[index] != " ":
                print("That position is already occupied!")
                continue

            board[index] = current_player

            if check_winner(current_player):
                display_board()
                print("Player " + current_player + " wins!")
                break

            if check_draw():
                display_board()
                print("It's a draw!")
                break

            if current_player == "X":
                current_player = "O"
            else:
                current_player = "X"

        except ValueError:
            print("Please enter a valid number.")


play_game()


