
import os
cur_path  = os.path.abspath(__file__)
root_path = cur_path[:cur_path.find('Electroplating') + len('Electroplating')]
temporal_planning_path = os.path.join('D:', 'diandu', 'temporal-planning', 'bin', 'plan.py')
data_path = os.path.join(root_path, 'data')
line_path = os.path.join(data_path, '211')


domain_config = {
    'domain_path': os.path.join(line_path, 'domain.pddl'),
    'name': 'Electroplating',
    'interval': 4                                  # 表示天车之间需要间隔多少个槽位， 0 表示两个天车之间可以连在一起， 1 表示距离一个槽位
}

problem_config = {
    'problem_path': os.path.join(line_path, 'problem.pddl'),
    'name': 'electroplating',
    'domain': 'Electroplating',
    'is_cycle': False
}

slot_config = {
    'slots': range(1, 40),
    'empty_slot': range(1, 40),
    'blanking_slot': [1],
    'stocking_slot': [1],
    'border_slot': [1, 39],
    'disable_slot': [],
    'gears_begin_slot': [],
    'gears_end_slot': []
}

pole_config = {
    'poles': [1, 2, 3],
    'pole_region': [range(1,16), range(14, 30), range(28, 40)],
    'pole_position': [1, 16, 30],
    'pole_order_num': [1, 2, 3],
    'pole_moving_duration': 1,
    'pole_start_duration': 2,
    'pole_stop_duration': 2,
    'pole_hangon_duration': 10,
    'pole_hangoff_duration':10,
}

gear_config = {
    'gears': [],
    'gears_region': [],
    'gears_position': [],
    'gear_moving_duration': 10,
}

db_config = {
    'user': 'root',
    'password': 'winsunmes',
    'host': '127.0.0.1',
    'port': '3306',
    'database': 'ai'
}

other_config = {
    'new_problem_path': os.path.join(line_path, 'new_problem.pddl'),
    'planning_path': temporal_planning_path,
    'output_actions_path': os.path.join(line_path, 'output.txt'),
    'python2_path': 'python2.7'
}