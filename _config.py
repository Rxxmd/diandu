
import os
from datainit import plcApi
import ipdb

BLANKING_SLOT = [1]    # 下料槽位    
STOCKING_SLOT = [1]     # 上料槽位
BORDER_SLOT = [1, 39]   # 边界槽位
HOIST_INTERVAL = 4      # 天车间隔
IS_CYCLE = False        # 流水线是否是循环的
HOIST_REGION = [range(1,16), range(14, 30), range(28, 40)] #天车的区间

HOIST_MOVE_DURATION = 1
HOIST_RISE_DURATION = 10
HOIST_DOWN_DURATION = 10
HOIST_STOP_DURATION = 2
HOIST_START_DURATION = 2
GEAR_MOVE_DURATION = 16

# 配置文件路径
cur_path  = os.path.abspath(__file__)
root_path = cur_path[:cur_path.find('Electroplating') + len('Electroplating')]
temporal_planning_path = os.path.join('D:', 'diandu', 'temporal-planning', 'bin', 'plan.py')
data_path = os.path.join(root_path, 'data')
line_path = os.path.join(data_path, '211')

# 读取产线状态
# 读取槽位
while True:
    slots = plcApi.get_tank_status()
    if slots:
        break
empty_slots = [k for k, v in slots.items() if v == 1]
slots = range(empty_slots[0], empty_slots[-1] + 1) 
    # 读取天车位置
while True:
    pole_positions = plcApi.get_hoist_position()
    if pole_positions:
        break
poles = [k for k, v in pole_positions.items() if v > 0 and k > 0]
pole_positions = [v for k, v in pole_positions.items() if v > 0 and k > 0]


domain_config = {
    'domain_path': os.path.join(line_path, 'domain.pddl'),
    'name': 'Electroplating',
    'interval': HOIST_INTERVAL                                  # 表示天车之间需要间隔多少个槽位， 0 表示两个天车之间可以连在一起， 1 表示距离一个槽位
}

problem_config = {
    'problem_path': os.path.join(line_path, 'problem.pddl'),
    'name': 'electroplating',
    'domain': 'Electroplating',
    'is_cycle': IS_CYCLE
}

slot_config = {
    'slots': slots,
    'empty_slot': empty_slots,
    'blanking_slot': BLANKING_SLOT,
    'stocking_slot': STOCKING_SLOT,
    'border_slot': BORDER_SLOT,
    'disable_slot': [],
    'gears_begin_slot': [],
    'gears_end_slot': []
}

pole_config = {
    'poles': poles,
    'pole_region': HOIST_REGION,
    'pole_position': pole_positions,
    'pole_order_num': poles,
    'pole_moving_duration': HOIST_MOVE_DURATION,
    'pole_start_duration': HOIST_START_DURATION,
    'pole_stop_duration': HOIST_STOP_DURATION,
    'pole_hangon_duration': HOIST_RISE_DURATION,
    'pole_hangoff_duration':HOIST_DOWN_DURATION,
}

gear_config = {
    'gears': [],
    'gears_region': [],
    'gears_position': [],
    'gear_moving_duration': 16,
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