"""图片标识与输出子目录。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FigureSpec:
    identifier: str
    folder: str


def specifications() -> list[FigureSpec]:
    return [
        FigureSpec('01_maze_search', 'problem1_maze'),
        FigureSpec('02_maze_frontier', 'problem1_maze'),
        FigureSpec('03_maze_efficiency', 'problem1_maze'),
        FigureSpec('04_weighted_path_cost', 'problem2_weighted_terrain'),
        FigureSpec('05_weighted_heuristic', 'problem2_weighted_terrain'),
        FigureSpec('06_weighted_efficiency', 'problem2_weighted_terrain'),
        FigureSpec('07_minimax_backup', 'problem3_game_tree'),
        FigureSpec('08_alpha_beta_pruning', 'problem3_game_tree'),
        FigureSpec('09_game_tree_efficiency', 'problem3_game_tree'),
        FigureSpec('10_treasure_map_matrix', 'problem4_treasure_game'),
        FigureSpec('11_treasure_state', 'problem4_treasure_game'),
        FigureSpec('12_treasure_root_choices', 'problem4_treasure_game'),
        FigureSpec('13_treasure_scores', 'problem4_treasure_game'),
        FigureSpec('14_treasure_routes', 'problem4_treasure_game'),
        FigureSpec('15_treasure_efficiency', 'problem4_treasure_game'),
        FigureSpec('16_treasure_pruning_depth', 'problem4_treasure_game'),
        FigureSpec('17_treasure_runtime', 'problem4_treasure_game'),
    ]
