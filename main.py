import pygame
from copy import deepcopy
from random import choice

# переменные фигур
BlackFigure = 0
BlackKingFigure = 1
WhiteFigure = 2
WhiteKingFigure = 3
AvailableMove = 4
EmptyCell = 5
white_figures = [WhiteFigure, WhiteKingFigure]
black_figures = [BlackFigure, BlackKingFigure]
all_figures = [WhiteFigure, WhiteKingFigure, BlackFigure, BlackKingFigure]
king_figures = [WhiteKingFigure, BlackKingFigure]
free_cells = [AvailableMove, EmptyCell]

# разрешение окна
display_width = 800
display_height = 800

# переменные, нужные для отриковки
cell_size = 100
clock = pygame.time.Clock()
display = pygame.display.set_mode((display_width, display_height))

# переменные, нужные для поиска хода
max_recursion_depth = 3

pygame.init()


# переводит все клетки из состояния AvailableMove в EmptyCell (чтобы стереть подсветку возможных ходов у игрока) и
# и переводит шашки, которые этого заслуживают, в дамки
def check_board(board):
    for x in range(8):
        for y in range(8):
            if board[y][x] == AvailableMove:
                board[y][x] = EmptyCell
            if y == 0 and board[y][x] == WhiteFigure:
                board[y][x] = WhiteKingFigure
            if y == 7 and board[y][x] == BlackFigure:
                board[y][x] = BlackKingFigure


# класс отвечает за отрисовку всего на экране
class Artist:
    def __init__(self):
        self.textures = [pygame.image.load('images/black_figure.gif'),
                         pygame.image.load('images/black_king_figure.gif'),
                         pygame.image.load('images/white_figure.gif'),
                         pygame.image.load('images/white_king_figure.gif')]

    def draw(self, board):
        display.fill((255, 255, 255))
        for x in range(8):
            for y in range(8):
                if (x + y) % 2 == 1:
                    pygame.draw.rect(display, (0, 0, 0), (x * cell_size, y * cell_size, cell_size, cell_size))
                if board[y][x] in all_figures:
                    display.blit(self.textures[game_board[y][x]], (x * cell_size, y * cell_size))
        for x in range(8):
            for y in range(8):
                if board[y][x] == AvailableMove:
                    pygame.draw.rect(display, (164, 194, 54),
                                     (x * cell_size, y * cell_size, cell_size - 1, cell_size - 1), 10)


# главный игровой цикл
def run_game():
    game_runs = True
    player_move = True
    initialize_game()
    artist = Artist()
    list_of_moves = []
    while game_runs:
        if not player_move:
            make_move(find_best_move(game_board), game_board)
            check_board(game_board)
            player_move = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                curr_cell = (event.pos[0] // cell_size, event.pos[1] // cell_size)
                if event.button == 1:
                    if game_board[curr_cell[1]][curr_cell[0]] in white_figures:
                        check_board(game_board)
                        chosen_cell = curr_cell
                        list_of_moves = find_available_moves([chosen_cell], game_board)
                        for move in list_of_moves:
                            ready_board_for_move(move, game_board)
                    elif game_board[curr_cell[1]][curr_cell[0]] == AvailableMove:
                        suitable_move = find_suitable_move_for_kings(curr_cell, list_of_moves)
                        if suitable_move:
                            make_move(suitable_move, game_board)
                            player_move = False
                        check_board(game_board)

        artist.draw(game_board)
        pygame.display.update()
        clock.tick(8.3)


# функция нужна, чтобы отметить игроку клетки, которые участвуют в ходе
# под ходом подразумевается полная последовательность клеток, которые пройдет шашка, начиная с клетки,
# на которой она стоит в данный момент, заканчивая ее финальной позицией на доске
def ready_board_for_move(move, board):
    for cells in move:
        if board[cells[1]][cells[0]] == EmptyCell:
            board[cells[1]][cells[0]] = AvailableMove


# ищет наилучший ход из всех возможных, пока что ищет только для черных фигур, но это легко исправляется
# критерий определения наилучшего хода, если говорить грубо, - количество убитых (полее подробное объяснение далее)
# если существует несколько одинаково хороших ходов, выбирает случайный
def find_best_move(board):
    list_of_moves = find_all_available_moves(black_figures, board)
    ratings = [rate_move_recursively(move, board) for move in list_of_moves]
    num_of_moves = len(list_of_moves)
    if num_of_moves == 0:
        return []
    best_moves = []
    best_i = 0
    for i in range(num_of_moves):
        if ratings[i] > ratings[best_i]:
            best_i = i
            best_moves = [list_of_moves[i]]
        elif ratings[i] == ratings[best_i]:
            best_moves.append(list_of_moves[i])
    return choice(best_moves)


# оценивает один ход количеством убитых врагов
def rate_one_move(allied_figures, enemy_types, move, board):
    new_board = deepcopy(board)
    make_move(move, new_board)
    check_board(new_board)
    return count_figures_on_board(enemy_types, board) - count_figures_on_board(enemy_types, new_board) + \
           count_figures_on_board(allied_figures, new_board) - count_figures_on_board(allied_figures, board)


# функция рекурсивно оценивает ходы по алгоритму minimax с отсечениями, кроме того, чем дальше в рекурсии найден ход,
# тем меньше его стоимость (происходит деление на глубину рекурсии // 2),
# чтобы программа не изображала из себя предсказателя слишком самоуверенно
def rate_move_recursively(move, board,
                          curr_rating=None, recursion_level=1, enemy_move=False, top_clipping=13, lower_clipping=-13):
    allied_figures = white_figures if board[move[-1][1]][move[-1][0]] in white_figures else black_figures
    enemy_figures = black_figures if board[move[-1][1]][move[-1][0]] in white_figures else white_figures
    if curr_rating is None:
        curr_rating = rate_one_move(allied_figures, enemy_figures, move, board) if not enemy_move else \
            -rate_one_move(allied_figures, enemy_figures, move, board)
    all_moves = find_all_available_moves(enemy_figures, board)
    num_of_moves = len(all_moves)
    if enemy_move:
        curr_move_rating = [curr_rating + rate_one_move(allied_figures, enemy_figures, move, board)
                            for move in all_moves]
    else:
        curr_move_rating = [curr_rating - rate_one_move(allied_figures, enemy_figures, move, board)
                            for move in all_moves]
    if enemy_move:
        lower_clipping = lower_clip(curr_move_rating, all_moves, num_of_moves, lower_clipping)
    else:
        top_clipping = top_clip(curr_move_rating, all_moves, num_of_moves, top_clipping)
    if recursion_level < max_recursion_depth:
        for i in range(num_of_moves):
            new_board = deepcopy(board)
            make_move(move, new_board)
            check_board(new_board)
            curr_move_rating[i] = rate_move_recursively(all_moves[i], new_board,
                                                        curr_move_rating[i], recursion_level + 1,
                                                        not enemy_move, top_clipping, lower_clipping)
    if num_of_moves == 0:
        return curr_rating
    if not curr_move_rating:
        return 0
    elif enemy_move:
        return max(curr_move_rating)
    else:
        return min(curr_move_rating)


def top_clip(curr_move_rating, all_moves, num_of_moves, old_top_clipping):
    new_top_clipping = old_top_clipping
    max_i = i = 0
    while i < num_of_moves:
        if curr_move_rating[i] > old_top_clipping:
            curr_move_rating.pop(i)
            all_moves.pop(i)
            i -= 1
            num_of_moves -= 1
        if num_of_moves > 0 and curr_move_rating[i] > curr_move_rating[max_i]:
            max_i = i
        i += 1
    if num_of_moves > 0:
        new_top_clipping = curr_move_rating[max_i]
    return new_top_clipping


def lower_clip(curr_move_rating, all_moves, num_of_moves, old_lower_clipping):
    new_lower_clipping = old_lower_clipping
    min_i = i = 0
    while i < num_of_moves:
        if curr_move_rating[i] < old_lower_clipping:
            curr_move_rating.pop(i)
            all_moves.pop(i)
            i -= 1
            num_of_moves -= 1
        if num_of_moves > 0 and curr_move_rating[i] < curr_move_rating[min_i]:
            min_i = i
        i += 1
    if num_of_moves > 0:
        new_lower_clipping = curr_move_rating[min_i]
    return new_lower_clipping


# ищет все возможные ходы для фигур из списка figure_types (см. find_available_moves)
def find_all_available_moves(figure_types, board):
    list_of_moves = []
    for x in range(8):
        for y in range(8):
            if board[y][x] in figure_types:
                new_moves = find_available_moves([(x, y)], board)
                for move in new_moves:
                    if len(move) == 1:
                        new_moves.remove(move)
                list_of_moves += new_moves
    return list_of_moves


# считает количество фигур определенного типа (figure_types - либо BlackFigures, либо WhiteFigures
def count_figures_on_board(figure_types, board):
    number = 0
    for x in range(8):
        for y in range(8):
            if board[y][x] in figure_types:
                if board[y][x] == figure_types[0]:
                    number += 1
                elif board[y][x] == figure_types[1]:
                    number += 6
    return number


# специализированный варинт следующей функции, нужный для работы с дамками
def find_suitable_move_for_kings(cell, list_of_moves):
    for move in list_of_moves:
        if move[-1] == cell:
            return move
    return []


# если по клетке cell можно однозначно определить ход из списка list_of_moves, функция вернет этот ход
# figure_type - тип фигуры, стоящей на клетке cell, т.е. один элемент списка all_figures (см. начало кода), вводится,
# потому что логика определения хода у дамок немного иная
def find_suitable_move(figure_type, cell, list_of_moves):
    if figure_type in king_figures:
        return find_suitable_move_for_kings(cell, list_of_moves)
    num_of_suitable_moves = 0
    for move in list_of_moves:
        if cell in move:
            num_of_suitable_moves += 1
            suitable_move = move
    if num_of_suitable_moves == 1:
        return suitable_move
    else:
        return []


# проделывает поданный на вход ход на поданной на вход доске
def make_move(move, board):
    if len(move) > 0:
        if board[move[0][1]][move[0][0]] != EmptyCell and board[move[0][1]][move[0][0]] != AvailableMove:
            figure = board[move[0][1]][move[0][0]]
            for cell in move:
                board[cell[1]][cell[0]] = EmptyCell
            board[move[-1][1]][move[-1][0]] = figure


# специализированный вариант следующей функции для случая, когда на исследумой позиции стоит дамка
def find_available_moves_for_kings(previous_move, board, recursive_call=False):
    # recursive_call: в случае рекурсивного вызова функция не будет возвращать небьющие ходы,
    # напрвления которых не совпадают с направлением previous_move
    curr_x = previous_move[-1][0]
    curr_y = previous_move[-1][1]
    figure = board[curr_y][curr_x]
    list_of_moves = []
    beating_move = False
    if figure == BlackKingFigure:
        enemies = white_figures
    elif figure == WhiteKingFigure:
        enemies = black_figures
    dir1 = 0
    dir2 = 1
    dir3 = 2
    dir4 = 3
    moves_in_dirs = [[previous_move[-1]] for i in range(4)]
    block_dirs = [False for i in range(4)]
    for i in range(1, 8):
        if block_dirs == [True for j in range(4)]:
            break
        for dx, dy in (1, 1), (-1, 1), (1, -1), (-1, -1):
            if dx == 1 and dy == 1:
                curr_dir = dir1
            elif dx == -1 and dy == 1:
                curr_dir = dir2
            elif dx == 1 and dy == -1:
                curr_dir = dir3
            elif dx == -1 and dy == -1:
                curr_dir = dir4
            if 0 <= curr_y + dy * (i + 1) <= 7 and 0 <= curr_x + dx * (i + 1) <= 7 and not block_dirs[curr_dir]:
                if board[curr_y + dy * i][curr_x + dx * i] in enemies and \
                        board[curr_y + dy * (i + 1)][curr_x + dx * (i + 1)] in free_cells:
                    beating_move = True
                    sub_board = deepcopy(board)
                    moves_in_dirs[curr_dir] += [(curr_x + j * dx, curr_y + j * dy) for j in range(i, i + 2)]
                    make_move(moves_in_dirs[curr_dir], sub_board)
                    next_moves = find_available_moves_for_kings(previous_move[:-1] + moves_in_dirs[curr_dir],
                                                                sub_board, True)
                    for move in next_moves:
                        list_of_moves.append(move)
                    moves_in_dirs[curr_dir] = [previous_move[-1]]
            if 0 <= curr_y + dy * i <= 7 and 0 <= curr_x + dx * i <= 7:
                if board[curr_y + dy * i][curr_x + dx * i] in free_cells and not block_dirs[curr_dir]:
                    moves_in_dirs[curr_dir].append((curr_x + dx * i, curr_y + dy * i))
                if board[curr_y + dy * i][curr_x + dx * i] in all_figures:
                    block_dirs[curr_dir] = True
            else:
                block_dirs[curr_dir] = True
    tie_continious_moves(moves_in_dirs, previous_move, list_of_moves, beating_move, recursive_call)
    return list_of_moves


def tie_continious_moves(moves_in_dirs, previous_move, list_of_moves, beating_move, recursive_call):
    len1 = len(moves_in_dirs[0])
    len2 = len(moves_in_dirs[1])
    len3 = len(moves_in_dirs[2])
    len4 = len(moves_in_dirs[3])
    if recursive_call and not beating_move:
        previous_dx = previous_move[-1][0] - previous_move[-2][0]
        previous_dy = previous_move[-1][1] - previous_move[-2][1]
        if previous_dx == 1 and previous_dy == 1:
            for i in range(1, len1 + 1):
                list_of_moves.append(previous_move[:-1] + moves_in_dirs[0][:i])
        elif previous_dx == -1 and previous_dy == 1:
            for i in range(1, len2 + 1):
                list_of_moves.append(previous_move[:-1] + moves_in_dirs[1][:i])
        elif previous_dx == 1 and previous_dy == -1:
            for i in range(1, len3 + 1):
                list_of_moves.append(previous_move[:-1] + moves_in_dirs[2][:i])
        elif previous_dx == -1 and previous_dy == -1:
            for i in range(1, len4 + 1):
                list_of_moves.append(previous_move[:-1] + moves_in_dirs[3][:i])
    elif not beating_move:
        for i in range(1, len1 + 1):
            list_of_moves.append(moves_in_dirs[0][:i])
        for i in range(1, len2 + 1):
            list_of_moves.append(moves_in_dirs[1][:i])
        for i in range(1, len3 + 1):
            list_of_moves.append(moves_in_dirs[2][:i])
        for i in range(1, len4 + 1):
            list_of_moves.append(moves_in_dirs[3][:i])
    if not list_of_moves:
        list_of_moves = [previous_move]


# поикс всех возможных ходов, продолжающий поданный на вход previous_move
# (в т.ч. всех ходов с заданной клетки) - возвращает список этих ходов
# ход - список всех клеток, по которым двигается шашка, включая клетку, с которой она стартует, заканчивая той,
# на которой окажется в итоге
def find_available_moves(previous_move, board):
    curr_x = previous_move[-1][0]
    curr_y = previous_move[-1][1]
    figure = board[curr_y][curr_x]
    if figure in king_figures:
        return find_available_moves_for_kings(previous_move, board)
    list_of_moves = []
    if figure in black_figures:
        enemies = white_figures
    elif figure in white_figures:
        enemies = black_figures
    else:
        return [previous_move]
    beating_move = False
    # beating_move - отвечает за возможность сделать бьющий ход
    for dx, dy in (1, 1), (-1, 1), (1, -1), (-1, -1):
        if 0 <= curr_y + 2 * dy <= 7 and 0 <= curr_x + 2 * dx <= 7:
            if board[curr_y + dy][curr_x + dx] in enemies and \
                    board[curr_y + 2 * dy][curr_x + 2 * dx] in free_cells:
                beating_move = True
                new_sub_board = deepcopy(board)
                make_move([(curr_x, curr_y),
                           (curr_x + dx, curr_y + dy),
                           (curr_x + dx * 2, curr_y + dy * 2)],
                          new_sub_board)
                next_moves = find_available_moves(
                    previous_move + [(curr_x + dx, curr_y + dy),
                                     (curr_x + dx * 2, curr_y + dy * 2)], new_sub_board)
                for move in next_moves:
                    list_of_moves.append(move)
    if not beating_move and len(previous_move) == 1:
        if figure == WhiteFigure:
            directions = [(1, -1), (-1, -1)]
        elif figure == BlackFigure:
            directions = [(1, 1), (-1, 1)]
        for dx, dy in directions:
            if 0 <= curr_y + dy <= 7 and 0 <= curr_x + dx <= 7 and \
                    board[curr_y + dy][curr_x + dx] == EmptyCell:
                list_of_moves.append(previous_move + [(curr_x + dx, curr_y + dy)])
    for first_move in list_of_moves:
        for second_move in list_of_moves:
            if first_move == second_move[::-1]:
                list_of_moves.remove(first_move)
    if not list_of_moves:
        list_of_moves = [previous_move]
    return list_of_moves


# построение начального игрового поля
def initialize_game():
    global game_board
    game_board = [[EmptyCell for i in range(8)] for j in range(8)]
    for i in range(8):
        for j in range(8):
            if (i + j) % 2 == 1:
                if i < 3:
                    game_board[i][j] = BlackFigure
                elif i > 4:
                    game_board[i][j] = WhiteFigure


run_game()
