    
import time
import copy
import ipdb
import portion as P
from collections import defaultdict
COLI_RELAX_TIME = 5
MOVE_RELAX_TIME = 10
class Predict:
    def __init__(self, config, Line):
        self.Actions = []   # 保存当前正在执行的动作
        self.products = {}  # 保存当前加入规划的物品
        self.Line = Line

        self.pole_move_time   = config.pole_config['pole_moving_duration']
        self.pole_stop_time   = config.pole_config['pole_stop_duration']
        self.pole_start_time  = config.pole_config['pole_start_duration']
        self.pole_load_time   = config.pole_config['pole_hangon_duration']
        self.pole_unload_time = config.pole_config['pole_hangoff_duration']
        self.gear_move_time   = config.gear_config['gear_moving_duration']
        self.basin_time = config.pole_config['basin_time']
        self.pole_up_down_time = config.HOIST_UP_DOWN_DURATION

        self.pole_interval = config.domain_config['interval'] # 天车之间的间隔
        self.tank_table      = {}   # 保存槽位被占据的时间段
        self.hoist_table     = {}   # 保存天车被占据的时间段
        self.tank_hoist_table = defaultdict(dict) # 保存天车和槽位的对应关系， 用于判断天车是否会碰撞
        self.hoist_position_table = {}   # 保存天车的位置
        self.tank_select = {} # 保存槽位被选中的次数
        self.init_tank_select()    
        self.init_tank_table()
        self.init_hoist_table()
        self.init_hoist_position_table()
        self.init_tank_hoist_table()
    '''
        预判模块
    '''
    def update_Line(self, Line):
        # 更新产线信息
        self.Line = Line

    def init_tank_select(self):
        # tank_select 是用来检测槽位被选过多少次的
        for tank in self.Line.Slots.array:
            self.tank_select[tank] = 0

    def init_tank_table(self):
        # tank_table 是用来检测槽位被占用的时间段的
        for tank in self.Line.Slots.array:

            if tank not in self.tank_table:
            
                self.tank_table[tank] = P.closed(-1, -1)
    
    def init_hoist_position_table(self):
        # hoist_position_table 是用来检测天车的位置的
        for k, v in self.Line.Poles.dict.items():
            position = v.position
            self.hoist_position_table[k] = {0: position}
        # 交换车的位置
        for k, v in self.Line.Gears.dict.items():
            position = v.position
            self.hoist_position_table[k] = {0: position}

    def init_hoist_table(self):
        # hoist_table 是用来检测天车被占用的时间段的
        for k, v in self.Line.Poles.dict.items():
            self.hoist_table[k] = P.closed(-1, -1)
        for k, v in self.Line.Gears.dict.items():
            self.hoist_table[k] = P.closed(-1 ,-1)

    def init_tank_hoist_table(self):
        # tank_hoist_table 是用来检测天车和槽位的对应关系的
        for k, v in self.Line.Poles.dict.items():
            for tank in self.Line.Slots.array:
                self.tank_hoist_table[k][tank] = P.open(-1, -1)

        for k, v in self.Line.Gears.dict.items():
            for tank in self.Line.Slots.array:
                self.tank_hoist_table[k][tank] = P.open(-1, -1)
    
    def gen_hoist_tank_table(self, product):
        pole_interval = self.pole_interval
        tank_table = product.tank_table
        hoist_table = product.hoist_table
        init_positiion = product.position
        process = product.processes
        # 生成天车和槽位的对应关系
        for stage, data in hoist_table.items():
            # 如果天车没有被占用，跳过
            if not data:
                continue

            # 确定当前槽位，下一个槽位，当前的开始时间，到达下一个槽位的结束时间
            if stage == product.stage:
                cur_tank = init_positiion
            else:
                cur_tank = tank_table[stage - 1][1]
            drip_time, wait_time = self.get_wait_drip_time(stage, process)
            pole = data[1]
            start_time = data[0].lower
            next_tank = tank_table[stage][1]
            end_time = data[0].upper
            cur_tanks = [tank for tank in range(cur_tank - pole_interval, cur_tank + pole_interval + 1)]
            cur_tanks = list(set(cur_tanks) & set(self.Line.Slots.array))
            next_tanks = [tank for tank in range(next_tank - pole_interval, next_tank + pole_interval + 1)]
            next_tanks = list(set(next_tanks) & set(self.Line.Slots.array))
            for tank in cur_tanks:
                self.tank_hoist_table[pole][tank] |= P.open(start_time - self.pole_stop_time - self.pole_move_time - COLI_RELAX_TIME, start_time + self.pole_start_time + self.pole_move_time + drip_time + COLI_RELAX_TIME)
            for tank in next_tanks:
                self.tank_hoist_table[pole][tank] |= P.open(end_time - self.pole_stop_time - self.pole_move_time - self.pole_unload_time - wait_time - COLI_RELAX_TIME, end_time + self.pole_start_time + self.pole_move_time + COLI_RELAX_TIME)
    
    def gen_tank_table(self, product):
        self.init_tank_table()
        self.init_hoist_table()
        for k, v in self.products.items():
            if k != product.name:
                for stage, data in v.tank_table:
                    tank, interval = data
                    self.tank_table[tank] |= interval
                
                for stage, data in v.hoist_table:
                    hoist, interval = data
                    self.hoist_table[hoist] |= interval
    
    def get_wait_drip_time(self, stage, process):
        # 判断是否是交换车， 如果时间换车的话就不需要滴水合等待
        tanks = process[stage].tanks
        if stage + 1 in process:
            next_tanks = process[stage + 1].tanks
            if set(tanks) < set(self.Line.Slots.gear_slot) and set(next_tanks) < set(self.Line.Slots.gear_slot):
                drip_time = 0
                wait_time = self.gear_move_time
                return drip_time, wait_time
        # drip_Time N次上升，滴水， 合水盆时间, 滴水用的是当前stage的滴水时间
        drip, basin, up_num= process[stage].drip, process[stage].basin, process[stage].up_num
        drip_time = self.pole_load_time + up_num * self.pole_up_down_time + basin * self.basin_time + drip
        # wait_time N次下降，滴水， 开水盆时间， 等待时间用的是下一个阶段的等待时间
        if stage + 1 in process:
            wait = process[stage + 1].wait
            down_num = process[stage + 1].down_num
        else:
            wait = 0
            down_num = 0
        wait_time = self.pole_unload_time + down_num * self.pole_up_down_time + basin * self.basin_time + wait
        return drip_time, wait_time
   
    def get_pole_move_time(self, pole_position, tank, next_tank, stage, process):
        # 如果是交换车移动直接给出empty move = 0， load_move_time = 交换车在两个槽位的移动时间 
        if tank in self.Line.Slots.gear_slot and next_tank in self.Line.Slots.gear_slot:
            empty_move_time = 0
            load_move_time = self.gear_move_time
            return empty_move_time, load_move_time
        drip_time, wait_time = self.get_wait_drip_time(stage, process)
        
        empty_move_time = self.pole_start_time + self.pole_stop_time + abs(pole_position - tank)
        # if empty_move_time <= 5:
            # empty_move_time = 10
        if pole_position == tank:
            empty_move_time = 0
        load_move_time = self.pole_start_time + self.pole_stop_time + abs(next_tank - tank) + wait_time + drip_time
        
        return empty_move_time, load_move_time
    
    def get_pole_position(self, cur_time, pole, hoist_position_table):
        # 二分查找pole_position
        pole_name = pole.name
        table = hoist_position_table[pole_name]
        if len(table) == 1:
            return tuple(table.values())[0]
        if cur_time in table:
            return table[cur_time]
        
        times = sorted(table.keys())
        left = 0 
        right = len(times) - 1
        while(left <= right):
            mid = (left + right) // 2
            if times[mid] == cur_time:
                return table[times[mid]]
            if times[mid] > cur_time:
                right = mid - 1
            else:
                left = mid + 1
        

        if mid == len(times) - 1:
            return table[times[mid]]
        else:
            if times[mid] < cur_time:
                return table[times[mid - 1]]
            else:
                return table[times[mid + 1]]

    def get_available_pole_interval(self, pole_interval, tank, next_tank, pole, empty_move_time, load_move_time):
        # pole_dis = -(-self.pole_interval // 2) 
        pole_dis = self.pole_interval
        # 确定tank周围的所有tanks
        start_tanks = [tank for tank in range(tank - pole_dis, tank + pole_dis + 1)]
        start_tanks = list(set(start_tanks) & set(self.Line.Slots.array))
        end_tanks = [tank for tank in range(next_tank - pole_dis, next_tank + pole_dis + 1)]
        end_tanks = list(set(end_tanks) & set(self.Line.Slots.array))
        # 获取当前tank和周围tank 可用的pole interval 的交集 
        start_tank_available_intervals = pole_interval
        for kp in self.Line.Poles.dict.keys():
            if kp != pole.name:
                for tank in start_tanks:
                    start_tank_available_intervals &= ~self.tank_hoist_table[kp][tank]
        # 用starttank available interval - empty_time就是start tank 的可用区间
        temp = P.open(0, 0)
        for stai in start_tank_available_intervals:
            temp |= P.open(stai.lower - empty_move_time, stai.upper)
        
        start_tank_available_intervals = temp & pole_interval

        # 获取next tank 和周围tank 的pole interval 交集
        
        end_tank_available_intervals = pole_interval
        for kp in self.Line.Poles.dict.keys():
            if kp != pole.name:
                for tank in end_tanks:
                    end_tank_available_intervals &= ~self.tank_hoist_table[kp][tank]
        temp = P.open(0, 0)
        for etai in end_tank_available_intervals:
            temp |= P.open(etai.lower - load_move_time, etai.upper)
        end_tank_available_intervals = temp & pole_interval

        return start_tank_available_intervals & end_tank_available_intervals
        
    def update_tank_select(self, tank_table, cur_tank):
        self.tank_select[cur_tank] += 1
        for k, v in tank_table.items():
            self.tank_select[v[1]] += 1

    def update_tank_table(self, tank_table, cur_tank, process):
        last_tank = cur_tank

        for stage, v in tank_table.items():
            drip_time, wait_time = self.get_wait_drip_time(stage, process)
            # 如果是交换槽，那么占据的时间等于从当前槽位开始，到下一个槽位结束的时间
            if last_tank in self.Line.Slots.gear_slot:
                next_stage = stage + 1
                if next_stage in tank_table:
                    next_stage_end = tank_table[next_stage][0].upper
                else:
                    next_stage_end = v[0].upper
                self.tank_table[last_tank] |= P.open(v[0].lower - wait_time, next_stage_end + drip_time + self.gear_move_time)
                last_tank = v[1]
            else:
                # 每个工艺占据该槽位的时间除了自己的浸泡时间还要加上把物品提上来的时间
                self.tank_table[last_tank] |= P.open(v[0].lower - wait_time, v[0].upper + drip_time)
                last_tank = v[1]

    def update_hoist_table(self, hoist_table):
        for k, v in hoist_table.items():
            if v:
                if 'pole' in v[1]:
                    pole = v[1]
                    # 如果是天车
                    if v[0].upper - v[0].lower < self.pole_start_time + self.pole_stop_time + self.pole_move_time:
                        self.hoist_table[pole] |= P.closed(v[0].lower - MOVE_RELAX_TIME, v[0].upper)
                    
                    else:
                        self.hoist_table[pole] |= v[0]
                # 如果是交换车， 那么它占据下一个天车把物品从交换车拿走， 然后移动回去gear begin的时间
                elif 'gear' in v[1]:
                    next_stage = k + 1
                    if next_stage in hoist_table:
                        next_stage_start = hoist_table[next_stage][0].lower
                    else:
                        next_stage_start = v[0].upper 
                    self.hoist_table[pole] |= P.closed(v[0].lower - MOVE_RELAX_TIME, next_stage_start + self.gear_move_time)
        
    def update_hoist_position_table(self, hoist_position_table):
        for k, v in hoist_position_table.items():
            self.hoist_position_table[k].update(v)
        pass

    def pre_sort_product(self, product, cur_time, max_start):
        
        poles = copy.deepcopy(self.Line.Poles.dict)
  
        hoist_position_table = copy.deepcopy(self.hoist_position_table)
        cur_stage = product.stage           # 当前stage
        max_stage = max(product.processes) + 1 # 最大的stage

        self.tank_result = {stage:False for stage in range(cur_stage, max_stage)}    # 记录每个槽位的最优解
        self.hoist_result = {stage:False for stage in range(cur_stage, max_stage)}   # 记录每个天车的最优解

        # self.hoist_position_result = {k:{} for k,v in poles.items()}  # 实时记录天车的位置，用来求天车的移动时间
        self.tank_flag = {stage:P.open(0, 0) for stage in range(cur_stage, max_stage)} # 记录槽位是否被访问过

        process = product.processes # 流程

        cur_tank = product.position    # 当前的tank

        # 求出可用的天车
        next_tanks = process[cur_stage + 1].tanks
        try:
            pole = [v for k, v in poles.items() if product.position in v.interval and next_tanks[-1] in v.interval][0]
        except:
            ipdb.set_trace()
        
        # 获取天车的位置
        pole_position = self.get_pole_position(cur_time, pole, hoist_position_table)
        # 求天车移动到物品当前所在槽位的empty move 的时间
        first_empty_move_time, _ = self.get_pole_move_time(pole_position, product.position, next_tanks[-1], cur_stage, process)
        # 求第一个空空移动的可用区间
        start_time = cur_time
        max_start = max_start + cur_time
       
        res = self.predict(cur_stage, cur_time, max_start, max_start,  cur_tank, hoist_position_table, max_stage, cur_stage, process, cur_time, product.process_start_time)
        if res:
            self.hoist_result[cur_stage] = (P.closed(start_time - first_empty_move_time, start_time), pole.name)
            product.tank_table = self.tank_result
            product.hoist_table = self.hoist_result
            self.update_tank_table(self.tank_result, cur_tank, process)
            self.update_hoist_position_table(hoist_position_table)
            self.update_hoist_table(self.hoist_result)
            self.update_tank_select(self.tank_result, cur_tank)
            self.gen_hoist_tank_table(product)
            print(product.tank_table)
            return product
        return False
        
    def predict(self,stage, start_time, end_time, max_start, tank, hoist_pos_table, max_stage, first_stage, process, cur_time, process_start_time):
        '''
            在predict方法中,它首先判断当前阶段是否为最后一个阶段，如果是，
            则记录最优解并返回最晚完成时间和使用的tank编号。如果不是,则计
            算可用的pole和tank时间区间,并选一个next_tank。然后,它遍历
            可用的tank时间区间和pole时间区间,计算空载和装载时间，并计算可
            用的pole时间区间。最后,它判断当前时间区间是否满足要求，如果满足，
            则递归调用predict方法,否则继续遍历下一个时间区间。
            stage: 当前工艺阶段
            start_time: 当前工艺阶段开始时间
            end_time: 当前工艺阶段结束时间
            max_start: 可以使用的最晚开始时间
            tank: 当前使用的tank编号  
            hoist_position_table: 用来实时记录天车位置的表
        '''
     
        if stage >= max_stage - 1:  # 到达最后一个工艺阶段
            #如果找到更优的解， 清空当前解
            if not self.tank_flag[stage] or (self.tank_flag[stage] and self.tank_result[stage][0].lower > start_time):
                self.tank_result = {stage:False for stage in range(first_stage, max_stage)}    # 清空解
                self.hoist_result = {stage:False for stage in range(first_stage, max_stage)}
                # self.hoist_position_result = {k:{} for k,v in self.Line.Poles.dict.items()}
                self.tank_flag = {stage:P.open(0, 0) for stage in range(first_stage, max_stage)}  
                self.tank_result[stage] = (P.closed(start_time, start_time +process[stage].lower_bound), tank)  # 记录最优解
                self.tank_flag[stage] = True  # 标记tank已经被占用
                
                return start_time, tank  # 返回最晚完成时间和使用的tank编号
            else:
                return None
        if self.tank_flag[stage]:
            return None
        if stage == first_stage:
            lb = process[stage].lower_bound - (cur_time - process_start_time)
            ub = process[stage].upper_bound - (cur_time - process_start_time)
            if lb < 0:
                lb = 0
            if ub < 1:
                ub = 1
        else:
            lb, ub = process[stage].lower_bound,  process[stage].upper_bound, # 当前阶段的要求
        next_tanks = process[stage + 1].tanks
        if tank in self.Line.Slots.gear_slot and set(next_tanks) < set(self.Line.Slots.gear_slot):

            pole = None
            for _, gear in self.Line.Gears.dict.items():
                if gear.begin == tank:
                    pole = gear
        else:
            try:
                pole = [v for k, v in self.Line.Poles.dict.items() if tank in v.interval and next_tanks[-1] in v.interval][0]
            except:
                ipdb.set_trace()
        min_end = start_time + lb  # 完成此阶段所需的最早结束时间
        max_end = end_time + ub    # 完成此阶段所需的最晚结束时间
        # 计算可用的pole和tank时间区间
        tank_interval = P.open(start_time, max_end)         # tank可用时间区间
        pole_interval = P.open(min_end - 50, max_end + 50)  # pole可用时间区间
        # 计算当前可用tank的时间区间（排除了已经被占用的时间段和超出lb和ub范围的时间段。
        available_tank_interval = tank_interval - self.tank_table[tank]
        # 计算pole的实际可用时间区间（排除了已经被占用的时间段。
        available_pole_interval = pole_interval - self.hoist_table[pole.name]
       
        # 选一个next_tank
        next_tank = None
        min_num = float('inf')
        for ntank in next_tanks:
            if min_num > self.tank_select[ntank] and ntank in self.Line.Slots.array:
                next_tank = ntank
                min_num = self.tank_select[ntank]
        
        for ati in available_tank_interval:  # available_tank_interval 指的是当前的tank的available interval
            if ati.upper - ati.lower >= lb:  # ati.uppper 相当与max_end, ati.lower相当于start_time
                apis = P.open(ati.lower + lb - 20, ati.upper + 100) & available_pole_interval
                for api in apis:
                    pole_position = self.get_pole_position(api.lower, pole, hoist_pos_table)
                    empty_move_time, load_move_time = self.get_pole_move_time(pole_position, tank, next_tank, stage, process)
                    api &= self.get_available_pole_interval(api, tank, next_tank, pole, empty_move_time, load_move_time)
                    for ap in api:
                             
                        if ap.upper - ap.lower >= empty_move_time + load_move_time: 

                            if ap.lower <= ati.lower +lb - empty_move_time:
                                min_end = ati.lower + lb
                            else:
                                min_end = ap.lower + empty_move_time
                            max_end = min(ap.upper - load_move_time, ati.upper)
                            if min_end - ub > max_start or max_end < min_end:
                                continue
                            hoist_pos_table[pole.name][ati.lower] = tank
                            pole_position = tank
                            res = self.predict(stage + 1, min_end + load_move_time, max_end + load_move_time, max_end + load_move_time, next_tank, hoist_pos_table, max_stage, first_stage, process, cur_time, process_start_time) 
                            
                            if res:
                                upper = res[0] - load_move_time
                                lower = max(ati.lower, upper - ub)
                                if not (P.open(lower, upper) & self.tank_table[tank]):
                                    best_solution = (P.closed(lower, upper), next_tank)
                                    self.tank_flag[stage] = True
                                    self.tank_result[stage] = best_solution
                                    self.hoist_result[stage + 1] = (P.open(res[0] - empty_move_time - load_move_time, res[0]), pole.name)

                                    # self.hoist_position_result[pole.name][res[0] - load_move_time] = tank
                                    # self.hoist_position_result[pole.name][res[0]] = next_tank
                                    
                                    return best_solution[0].lower, best_solution[1]  
        
        return None
        
    


