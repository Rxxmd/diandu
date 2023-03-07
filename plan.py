from collections import defaultdict, namedtuple
import portion as P
from datainit.global_var import Line, Parser, db, _config, PLC
import re
import copy
import subprocess
import ipdb
import utils
import time

PoleSpaceTimeRange = namedtuple('PoleSpaceTimeRange',['start_time', 'end_time', 'start_tank', 'end_tank'])
class Planning:
    def __init__(self, config):
        self.init_time = time.time()
        self.time = 0    
        self.Actions = []   # 保存当前正在执行的动作
        self.products = {}  # 保存当前加入规划的物品
        self.parser = Parser
        self.Plc = PLC
        self.Line = Line
        self.output_time = time.time() #用来同步output类的时间
        self.poles_space_time_range = {}
        self.parser.state_to_tuple()


        self.pole_move_time   = config.pole_config['pole_moving_duration']
        self.pole_stop_time   = config.pole_config['pole_stop_duration']
        self.pole_start_time  = config.pole_config['pole_start_duration']
        self.pole_load_time   = config.pole_config['pole_hangon_duration']
        self.pole_unload_time = config.pole_config['pole_hangoff_duration']
        self.gear_move_time   = config.gear_config['gear_moving_duration']
        self.collision_time = 5
        self.pole_interval = 4
        self.tank_table      = {}
        self.hoist_table     = {}
        self.tank_hoist_table = defaultdict(dict)
        self.hoist_position_table = {}       
        self.init_tank_table()
        self.init_hoist_table()
        self.init_hoist_position_table()
        self.init_tank_hoist_table()

        # self.output = open(_config.other_config['output_actions_path'], 'w')
    '''
        预判模块
    '''
    def init_tank_table(self):
        for tank in self.Line.Slots.array:

            if tank not in self.tank_table:
            
                self.tank_table[tank] = P.closed(-1, -1)
    
    def init_hoist_position_table(self):
        for k, v in self.Line.Poles.dict.items():
            position = v.position
            self.hoist_position_table[k] = {0: v.position}

    def init_hoist_table(self):
        for k, v in self.Line.Poles.dict.items():
            self.hoist_table[k] = P.closed(-1, -1)

    def init_tank_hoist_table(self):
        for k, v in self.Line.Poles.dict.items():
            
            for tank in self.Line.Slots.array:
                
                self.tank_hoist_table[k][tank] = P.open(-1, -1)
    
    def gen_hoist_tank_table(self, product):
        pole_interval = -(-self.pole_interval // 2) 
        tank_table = product.tank_table
        hoist_table = product.hoist_table
        init_positiion = product.position
        for stage, data in hoist_table.items():
            if not data:
                continue
            # 确定当前槽位，下一个槽位，当前的开始时间，到达下一个槽位的结束时间
            if stage == product.stage:
                cur_tank = init_positiion
            else:
                cur_tank = tank_table[stage - 1][1]
            pole = data[1]
            start_time = data[0].lower
            next_tank = tank_table[stage][1]
            end_time = data[0].upper
            cur_tanks = [tank for tank in range(cur_tank - pole_interval, cur_tank + pole_interval + 1)]
            cur_tanks = list(set(cur_tanks) & set(self.Line.Slots.array))
            next_tanks = [tank for tank in range(next_tank - pole_interval, next_tank + pole_interval + 1)]
            next_tanks = list(set(next_tanks) & set(self.Line.Slots.array))
            for tank in cur_tanks:
                self.tank_hoist_table[pole][tank] |= P.open(start_time - self.pole_stop_time - self.pole_move_time - self.collision_time, start_time + self.pole_start_time + self.pole_move_time + self.pole_load_time + self.collision_time)
            for tank in next_tanks:
                self.tank_hoist_table[pole][tank] |= P.open(end_time - self.pole_stop_time - self.pole_move_time - self.pole_unload_time - self.collision_time, end_time + self.pole_start_time + self.pole_move_time + self.collision_time)
    
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
   
    def match_pole_tank(self, start_tank, goal_tank, sum_t, temp_ht):
        pole_interval = -(-self.pole_interval // 2)
        pole_start_time = self.pole_start_time
        pole_hangup_time = self.pole_load_time
        if start_tank < goal_tank:
            exe_tank = range(start_tank, goal_tank + 1)
            iter_tank = range(start_tank - pole_interval, goal_tank + pole_interval + 1)
        else:
            exe_tank = range(goal_tank, start_tank + 1)
            iter_tank = range(start_tank + pole_interval, goal_tank - pole_interval - 1, -1)
        end_t = sum_t
        for tank in iter_tank:
            if tank in self.Line.Slots.array:
                ocupy_time = 0

                if start_tank != goal_tank:
                    # 产看自己的邻居
                    neibor = set(range(tank - pole_interval, tank + pole_interval + 1)) & set(exe_tank)
                    neibor = len(neibor)
                    ocupy_time += neibor
                    # 是否在start组内
                    start_group = range(start_tank - pole_interval, start_tank + pole_interval + 1)
                    if tank in start_group:
                            ocupy_time += pole_start_time
                # 是否在end 组内
                end_group = range(goal_tank - pole_interval, goal_tank + pole_interval + 1)
                if tank in end_group:
                    if start_tank != goal_tank:
                        ocupy_time += pole_start_time
                    ocupy_time += pole_hangup_time
                tank_distance = abs(tank - start_tank) - pole_interval
                if tank_distance < 0:
                    tank_distance = 0
                start_t = int(sum_t + tank_distance)
                end_t = start_t + ocupy_time if start_t + ocupy_time > end_t else end_t
                intersection = set(temp_ht[tank]) & set(range(start_t, start_t + ocupy_time))
                if len(intersection) > 1:
                    # print(start_t, start_t + ocupy_time, tank,'confilict')
                    return False
                else:
                    temp_ht[tank] = temp_ht[tank] | set(range(start_t, start_t + ocupy_time))
        return temp_ht, end_t

    def get_pole_move_time(self, pole_position, tank, next_tank):
        empty_move_time = self.pole_start_time + self.pole_stop_time + abs(pole_position - tank)
        if pole_position == tank:
            empty_move_time = 0
        load_move_time = self.pole_start_time + self.pole_stop_time + abs(next_tank - tank) + self.pole_load_time + self.pole_unload_time
        
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
        pole_dis = -(-self.pole_interval // 2) 
        # 确定tank周围的所有tanks
        start_tanks = [tank for tank in range(tank - pole_dis, tank + pole_dis + 1)]
        start_tanks = list(set(start_tanks) & set(self.Line.Slots.array))
        end_tanks = [tank for tank in range(next_tank - pole_dis, next_tank + pole_dis + 1)]
        end_tanks = list(set(end_tanks) & set(self.Line.Slots.array))
        # 获取当前tank和周围tank 可用的pole interval 的交集 
        start_tank_available_intervals = pole_interval
        for k, v in self.Line.Poles.dict.items():
            if k != pole.name and set(v.interval) & set(pole.interval):
                for tank in start_tanks:
                    start_tank_available_intervals &= ~self.tank_hoist_table[k][tank]
        # 用starttank available interval - empty_time就是start tank 的可用区间
        temp = P.open(0, 0)
        
        for stai in start_tank_available_intervals:
            temp |= P.open(stai.lower - empty_move_time, stai.upper)
        
        start_tank_available_intervals = temp & pole_interval

        # 获取next tank 和周围tank 的pole interval 交集
        
        end_tank_available_intervals = pole_interval
        
        for k, v in self.Line.Poles.dict.items():
            if k != pole.name and set(v.interval) & set(pole.interval):
                for tank in end_tanks:
                    end_tank_available_intervals &= ~self.tank_hoist_table[k][tank]
        temp = P.open(0, 0)
        for etai in end_tank_available_intervals:
            temp |= P.open(etai.lower - load_move_time, etai.upper)
        end_tank_available_intervals = temp & pole_interval

        return start_tank_available_intervals & end_tank_available_intervals
        
    def update_tank_table(self, tank_table, cur_tank):
        last_tank = cur_tank
        for k, v in tank_table.items():
            # 每个工艺占据该槽位的时间除了自己的浸泡时间还要加上把物品提上来的时间
            self.tank_table[last_tank] |= P.open(v[0].lower, v[0].upper + self.pole_load_time)
            last_tank = v[1]

    def update_hoist_table(self, hoist_table):
        for k, v in hoist_table.items():
            if v:
                pole = v[1]
                if v[0].upper - v[0].lower < self.pole_start_time + self.pole_stop_time + self.pole_move_time:
                    self.hoist_table[pole] |= P.closed(v[0].lower, v[0].upper + self.pole_start_time + self.pole_stop_time + self.pole_move_time)
                else:
                    self.hoist_table[pole] |= v[0]
        
    def update_hoist_position_table(self, hoist_position_table):
        for k, v in hoist_position_table.items():
            self.hoist_position_table[k].update(v)
        pass

    def constraint_table(self, product):
        poles = copy.deepcopy(self.Line.Poles.dict)
        tank_ocupy_table = copy.deepcopy(self.tank_table)
        hoist_ocupy_table = copy.deepcopy(self.hoist_table)
        hoist_position_table = copy.deepcopy(self.hoist_position_table)
        
        cur_time = self.time
        cur_stage = product.stage
        max_stage = max(product.processes) + 1
        tank_result = {stage:False for stage in range(cur_stage, max_stage)}    # 记录每个槽位的最优解
        hoist_result = {stage:False for stage in range(cur_stage, max_stage)}   # 记录每个天车的最优解
        hoist_position_result = {k:{} for k,v in poles.items()}
        tank_flag = {stage:P.open(0, 0) for stage in range(cur_stage, max_stage)}  
        process = product.processes
        max_start = cur_time + process[cur_stage].upper_bound
        cur_tank = product.position
        next_tanks = process[cur_stage + 1].tanks
        pole = [v for k, v in poles.items() if product.position in v.interval and next_tanks[-1] in v.interval][0]
        pole_position = self.get_pole_position(cur_time, pole, hoist_position_table)
        first_empty_move_time, _ = self.get_pole_move_time(pole_position, product.position, next_tanks[-1])
        start_time = cur_time + first_empty_move_time
        max_start = cur_time + process[cur_stage].upper_bound + first_empty_move_time
        def predict(stage, start_time, end_time, max_start, tank, hoist_position_table):
            hoist_pos_table = copy.deepcopy(hoist_position_table)
            nonlocal tank_result
            nonlocal tank_flag
            nonlocal hoist_result
            nonlocal hoist_position_result
            """
            stage: 当前工艺阶段
            start_time: 当前工艺阶段开始时间
            end_time: 当前工艺阶段结束时间
            max_start: 可以使用的最晚开始时间
            tank: 当前使用的tank编号  
            """
            if stage >= max_stage - 1:  # 到达最后一个工艺阶段
                #如果找到更优的解， 清空当前解
                if not tank_flag[stage] or (tank_flag[stage] and tank_result[stage][0].lower > start_time):
                    tank_result = {stage:False for stage in range(cur_stage, max_stage)}    # 清空解
                    hoist_result = {stage:False for stage in range(cur_stage, max_stage)}
                    hoist_position_result = {k:{} for k,v in poles.items()}
                    tank_flag = {stage:P.open(0, 0) for stage in range(cur_stage, max_stage)}  
                    tank_result[stage] = (P.closed(start_time, start_time), tank)  # 记录最优解
                    tank_flag[stage] = True  # 标记tank已经被占用
                    
                    return start_time, tank  # 返回最晚完成时间和使用的tank编号
                else:
                    return None
            if tank_flag[stage]:
                return None
            lb, ub = process[stage].lower_bound,  process[stage].upper_bound, # 当前阶段的要求
            next_tanks = process[stage + 1].tanks
            pole = [v for k, v in poles.items() if tank in v.interval and next_tanks[-1] in v.interval][0]
            for ntank in next_tanks:       # 遍历下一个工艺阶段涉及的所有tank
                min_end = start_time + lb  # 完成此阶段所需的最早结束时间
                max_end = end_time + ub    # 完成此阶段所需的最晚结束时间
                
                
                # 计算可用的pole和tank时间区间
                tank_interval = P.open(start_time, max_end)               # tank可用时间区间
                pole_interval = P.open(0, max_end + 100) 
                # 计算当前可用tank的时间区间（排除了已经被占用的时间段和超出lb和ub范围的时间段。
                available_tank_interval = tank_interval - tank_ocupy_table[ntank]
                # 计算pole的实际可用时间区间（排除了已经被占用的时间段）。
                available_pole_interval = pole_interval - hoist_ocupy_table[pole.name]
                
                for ati in available_tank_interval:
                    if ati.upper - ati.lower >= lb:
                        api = P.open(ati.lower + lb - 100, ati.upper + 100) & available_pole_interval
                        
                        pole_position = self.get_pole_position(api.lower, pole, hoist_pos_table)
                        empty_move_time, load_move_time = self.get_pole_move_time(pole_position, tank, ntank)
                        api &= self.get_available_pole_interval(api, tank, ntank, pole, empty_move_time, load_move_time)
                        if api.upper - api.lower >= empty_move_time + load_move_time and ati.lower <= max_start:
                            if api.lower <= ati.lower - empty_move_time:
                                min_end = ati.lower + lb
                            else:
                                min_end = api.lower + empty_move_time
                            
                            max_end = api.upper - load_move_time
                            hoist_pos_table[pole.name][ati.lower] = tank
                            pole_position = tank
                            res = predict(stage + 1,min_end + load_move_time, max_end + load_move_time, max_end + load_move_time, ntank, hoist_pos_table) 
                            if res:
                                if not (P.open(ati.lower, res[0] - load_move_time) & tank_ocupy_table[ntank]):

                                    best_solution = (P.closed(ati.lower, res[0] - load_move_time), ntank)
                                    tank_flag[stage] = True
                                    tank_result[stage] = best_solution
                                    hoist_result[stage + 1] = (P.open(res[0] - empty_move_time - load_move_time, res[0]), pole.name)
                                    hoist_position_result[pole.name][res[0] - load_move_time] = tank
                                    hoist_position_result[pole.name][res[0]] = ntank
                                    
                                    return best_solution[0].lower, best_solution[1]
            return None
            
        res = predict(cur_stage, start_time, start_time, max_start,  cur_tank, hoist_position_table)
        if res:
            hoist_result[cur_stage] = (P.closed(self.time, self.time + first_empty_move_time), pole.name)
            product.tank_table = tank_result
            product.hoist_table = hoist_result
            self.update_hoist_position_table(hoist_position_result)
            self.update_hoist_table(hoist_result)
            self.update_tank_table(tank_result, product.position)
            self.gen_hoist_tank_table(product)
            return product
        return False



        #     res = self.match_tank(tanks, lower_bound, temp_tt, sum_t)  
        #     if not res:
        #         return False
            
        #     slc_tank, res_t = res
            
        #     res = self.match_pole(avai_poles, slc_tank, next_tank, sum_t, res_t) 
        #     if not res:
        #         return False
            
        #     pole, ts, te = res
        #     if sum_t + res_t <= ts:
                
        #         ipdb.set_trace()
        #     res = self.match_pole_tank(pole.position, slc_tank, ts, temp_ht)
        #     if not res:
        #         return False
        #     temp_ht, end_t = res
            
        #     res = self.match_pole_tank(slc_tank, next_tank,end_t, temp_ht )
        #     if not res:
        #         return False
        #     temp_ht, end_t = res
        #     pole.position = next_tank
        #     if set(tanks).issubset(self.Line.Slots.stocking) and product.stage == 0:    
        #         product.hoist_table[stage] = (pole.name, P.closed(ts, te))
        #         temp_pt[pole.name] = temp_pt[pole.name] | P.closed(ts, te)

        #         product.stage += 1
        #         sum_t += (te - ts)
                
        #     else:  
        #         product.tank_table[stage] = (slc_tank, P.closed(sum_t, sum_t + res_t)) 
        #         temp_tt[slc_tank] |= P.closed(sum_t, sum_t + res_t)
        #         product.hoist_table[stage] = (pole.name, P.closed(ts, te)) 
        #         temp_pt[pole.name] |= P.closed(ts, te)
                
        #         product.stage += 1
        #         sum_t += (te - ts + res_t)
                   
        # self.tank_table = temp_tt
        # self.hoist_table = temp_pt
        # self.hoist_tank_table = temp_ht
        # return True
    
    def add_product(self):
        for craft, products in self.Line.Products.dict.items():
            if not products:
                continue
            
            product = copy.deepcopy(products[0])
            product =  self.constraint_table(product)
            if product:
                name = self.Line.Products.dict[craft][0].name
                self.products[name] = product

                self.Line.Products.dict[craft].pop(0)
                return True

    '''
        子目标模块
    '''
    def get_exe_poles(self):
        exe_poles = []

        for time, act, status in self.Actions:

            exe_poles.append(act.parameters[0])
        
        return exe_poles

    def gen_gear_goal(self):
        goal = []
        gears = copy.deepcopy(self.Line.Gears.dict)
        for gear in gears.values():
            if gear.product and gear.position == gear.end:
                pass
            elif not gear.product and gear.position == gear.end:
                goal.append(f'(pole_position {gear.name} slot{gear.begin})')
            elif gear.product and gear.position == gear.begin:
                goal.append(f'(product_at {gear.product} slot{gear.end})')
        return goal

    def gen_pole_goal(self):
        goal = []
        state = list(self.parser.state)
        poles = copy.deepcopy(self.Line.Poles.dict)
        poles = list(poles.values())
        poles = sorted(poles, key=lambda pole: pole.order_num)
        poles.reverse()
        self.Line.Slots.set_blanking_slot_empty()
        exe_poles = self.get_exe_poles()
        ipdb.set_trace()
        for pole in poles:
            
            if pole in exe_poles:
                 
                continue

            if pole.select and pole.product and pole.up_down == 3 and pole.product in self.products: 
                
                product = self.products[pole.product]
                next_slot = 'slot' + str(product.next_slot)
                if product.position != product.next_slot and pole.position == product.next_slot:

                    state.append(('target_slot', next_slot, product.name))
                    
                    goal.append(f'(product_at {product.name} {next_slot})')
                    if product.position not in self.Line.Slots.empty:
                        
                        self.Line.Slots.empty.append(product.position)
                    
                    if product.next_slot in self.Line.Slots.empty:
                        self.Line.Slots.empty.remove(product.next_slot)
                elif pole.position != product.next_slot:
                    goal.append(f'(pole_position {pole.name} {next_slot})')

            # elif pole.select and not pole.product and not pole.mid and pole.up_down == 3:

            #     goal.append(f'(pole_have_things {pole.name} {pole.select})')

            elif not pole.select and not pole.product and pole.stopping:
                
                product, slot = self.select_product(pole)
                if product and slot:
                    if slot == pole.position:
                        goal.append(f'(pole_have_things {pole.name} {product})')
                    else:
                        goal.append(f'(pole_position {pole.name} slot{slot})')
                

            elif pole.select and pole.up_down == 1 and not pole.product:
                position = self.products[pole.select].position
                if position == pole.position:
                    goal.append(f'(pole_have_things {pole.name} {pole.select})')
                else:
                    goal.append(f'(pole_position {pole.name} slot{position})')
        state = tuple(state)
        
        self.parser.state = state
        return goal
   
    def gen_goal(self):

        gear_goal = self.gen_gear_goal()
        pole_goal = self.gen_pole_goal()
        goal = gear_goal + pole_goal
        return goal

    def add_poles_space_time_range(self, goals):
        for goal in goals:
            product = re.findall(r'p\d+', goal)[0]
            product = self.products[product]
            move_time = 0
            if 'pole_position' in goal: 
                pole = re.findall(r'pole\d+', goal)[0]
                pole = self.Line.Poles.dict[pole]
                if pole.position != product.position:
                    if pole.stopping:
                        move_time = self.pole_start_time + self.pole_stop_time + abs(pole.position - product.position)
                    else:
                        move_time = self.pole_stop_time + abs(pole.position - product.position)
            elif 'product_at' in goal:
                slot = re.findall(r'slot\d+', goal)[0]
                pole = product.pole
                pole = self.Line.Poles.dict[pole]
                if pole.position != product.position:
                    if pole.stopping:
                        move_time = self.pole_start_time + self.pole_stop_time + abs(pole.position - product.position)
                    else:
                        move_time = self.pole_stop_time + abs(pole.position - product.position)
            if move_time > 0:        
                pstr = PoleSpaceTimeRange(self.time, self.time + move_time, pole.position, product.position)
                self.poles_space_time_range[pole.name] = pstr
    
    def select_product(self, pole):
        min_t = float('inf')
        gproduct = None
        gtank = None
        
        for k ,v in self.products.items():
            # lower是预排序好的完成时间
            upper = v.tank_table[v.stage][0].upper
            move_time = abs(pole.position - v.position) + self.pole_start_time + self.pole_stop_time
            if pole.position == v.position:
                move_time = 0
            if self.time - v.process_start_time >= v.processes[v.stage].lower_bound - move_time:
                v.available = True
            if upper - self.time <= move_time and v.available:

            # if v.hoist_table[v.stage] and  v.hoist_table[v.stage][0].lower <= self.time and v.position == v.next_slot and v.available:
                # print(self.time - v.hoist_table[v.stage][0].lower)
                # if self.time - v.hoist_table[v.stage][0].lower > 10:
                #     ipdb.set_trace()
                tank = v.tank_table[v.stage][1]
                hoist = v.hoist_table[v.stage + 1][1]
                
                if hoist == pole.name and tank in self.Line.Slots.empty:
                    tl = upper
                    if min_t > tl:
                        gproduct = v
                        min_t = tl
                        gtank = tank
            
        if gproduct:
            
            self.products[gproduct.name].next_slot = gtank

            self.products[gproduct.name].stage += 1

            self.products[gproduct.name].available = False

            self.products[gproduct.name].stage_start = float('inf')

            self.Line.Slots.empty.remove(gtank)
        
            self.Line.Poles.dict[pole.name].select = gproduct.name
            
            return gproduct.name, gtank
            
        return None, None

    '''
        解析文件， 判断截断的动作
    '''

    def parser_min_time(self, actions_name, stop_time):
        
        if self.Actions:

            st = list(stop_time.values())
        
            st = sorted(st, key = lambda s: s[1])
            
            if st:
                min_end_time = min(st[0][1], self.Actions[0][0] - self.time)
            else:
                min_end_time = self.Actions[0][0] - self.time
            
            return min_end_time
        
        
        # 一个天车运行完成的at start时间点 或者 一道工艺完成的时间点
        # 如果动作是 move pole 就去 at end 时间点
        # 如果动作是 hangoff hangup 就取 at start 时间点
        for time, act_name, duration in sorted(actions_name):
            if 'pole' in act_name:
                pole = re.findall(r'(pole\d+)', act_name)[0]
                
                if 'hang' in act_name:
                    if pole not in stop_time:
                        stop_time[pole] = (time, time + duration) 
                    
        st = list(stop_time.values())
        
        st = sorted(st, key = lambda s: s[1])
        
        if actions_name and st:
            
            min_end_time = st[0][1]
            
        else:
            min_end_time = 1

        return min_end_time

    def fliter_actions(self, actions_name, min_end_time, stop_time):
        temp_acts = []
        
        for time, act_name, duration in sorted(actions_name):
            
            reg = re.findall(r'(pole\d+)', act_name)
            
            if reg:
                
                pole = reg[0]
                
                if pole and pole in stop_time:
                    
                    if time <= stop_time[pole][0]:
                        
                        temp_acts.append((time, act_name, duration)) 
            else:
                
                if time <= min_end_time:
                    
                    temp_acts.append((time, act_name, duration))
        return temp_acts
    
    def parser_stop_time(self, actions_name):

        forward = {}
        inverse = {}
        stop_time = {}

        for time, act_name, duration in sorted(actions_name):
            
            if 'move-pole' in act_name:
                
                pole = re.findall(r'(pole\d+)', act_name)[0]
                
                begin_t = time
                
                end_t = time + duration
                
                if 'move-pole-forward' in act_name:
                    
                    if pole in inverse and pole not in stop_time:
                    
                        stop_time[pole] = inverse[pole]

                        stop_time[pole] = (stop_time[pole][0], stop_time[pole][1] + self.pole_stop_time)

                    
                    if pole not in forward:
                        
                        forward[pole] = (begin_t, end_t)
                    
                    else:
                    
                        if forward[pole][0] < begin_t:
                    
                            forward[pole] = (begin_t, end_t)
                
                elif 'move-pole-inverse' in act_name:
                    
                    if pole in forward and pole not in stop_time:
                    
                        stop_time[pole] = forward[pole]
                    
                        stop_time[pole] = (stop_time[pole][0], stop_time[pole][1] + self.pole_stop_time)

                    
                    if pole not in inverse:
                        
                        inverse[pole] = (begin_t, end_t)
                
                    else:
                        if inverse[pole][0] < begin_t:
                
                            inverse[pole] = (begin_t, end_t)

        for time, act_name, duration in sorted(actions_name):
            
            if 'move-pole' in act_name:
                
                pole = re.findall(r'(pole\d+)', act_name)[0]
                
                if pole not in stop_time:
                 
                    stop_time[pole] = forward[pole] if pole in forward else inverse[pole]
                    
                    stop_time[pole] = (stop_time[pole][0], stop_time[pole][1] + self.pole_stop_time)
        return stop_time

    def change_move_time(self, actions_name, stop_time, min_end_time):
        add = []
        rem = []
        if stop_time:
            for time, act_name, duration in sorted(actions_name):
                if 'move-pole' in act_name:
                    
                    pole = re.findall(r'(pole\d+)', act_name)[0]
                    
                    if pole in stop_time and time == stop_time[pole][0]:
                        
                        rem.append((time, act_name, duration))
                        
                        add.append((time, act_name, duration + self.pole_stop_time))

            actions_name = list(set(actions_name).difference(rem).union(add))
        return actions_name

    def remove_action(self, actions_name, stop_time):
        rem = []
        for time, act_name, duration in sorted(actions_name):

            pole = re.findall(r'(pole\d+)', act_name)[0]
            
            if 'hang' in act_name:

                pole = re.findall(r'(pole\d+)', act_name)[0]
                
                if pole in stop_time:

                    rem.append((time, act_name, duration))

        actions_name = list(set(actions_name).difference(rem))

        return actions_name

    '''
        更新物品
    '''

    def update_products(self, actions_name, min_end_time):
        
        output_actions = []

        delete = []   
        
        replace = []
        
        for time, act_name, duration in sorted(actions_name):
            
            sp = re.split('[( )]', act_name)
            
            product = sp[-2]
            
            if product in self.products:
                cur_stage = self.products[product].stage

            if time <= min_end_time:

                output_actions.append((time, act_name, duration))
            
            if time <= min_end_time and ('hangup' in act_name or 'move-gear-equip' in act_name):
                pass

            if time <= min_end_time and ('hangoff' in act_name or 'move-gear-equip' in act_name):

                self.products[product].process_start_time = self.time + time + duration
                self.products[product].available = False
                    
        actions_name.extend(replace)

        output_actions.extend(replace)
        
        actions_name = list(set(actions_name) - set(delete))

        output_actions = list(set(output_actions) - set(delete))
            

        return output_actions

    def output_actions(self, actions_name, min_end_time):
   
        for time, act, d in sorted(actions_name):
            
            sp = re.split('[( )]', act)
        
            line = act

            if 'hang-off-up' in act:
                line = 'hangup-pole'
                line = f'{float(time + self.time) : 9.3f}  {line:40}  {self.pole_load_time:10}'
                print(line, file = self.output_actions_file)
                line = 'hangoff-pole'
                line = f'{float(time + self.time + d - self.pole_unload_time) : 9.3f}  {line:40}  {self.pole_unload_time:10}'
                print(line, file = self.output_actions_file)
                continue

            if 'move-pole' in act:
                
                if 'move-pole-forward' in act:
        
                    line = f'(move-pole-forward {sp[2]} {sp[3]} {sp[4]})'
        
                else:
        
                    line = f'(move-pole-inverse {sp[2]} {sp[4]} {sp[3]})'

            print(f'{float(time + self.time) : 9.3f}  {line:40}   {float(d):10.1f}',file = self.output_actions_file)              # 把结果输出到文件
            
            if 'move-pole' in act and d == self.pole_stop_time + self.pole_move_time:
                # if self.time + time >= 78:
                #     ipdb.set_trace()
                position = self.Line.Poles.dict[sp[2]].position
                print(f'{float(time + self.time + self.pole_move_time) : 9.3f} (stop-moving-pole {sp[2]} position{position}) {self.pole_stop_time : 10}', file = self.output_actions_file)
    
    def del_end_products(self):
        # 删除已经执行完最后一道 craft 的 product
        delete = {}
        for k, v in self.products.items():
            if v.stage == max(v.processes) and  v.position in self.Line.Slots.blanking:
                print(self.time)
                delete[k] = v

        self.products = dict(self.products.items() - delete.items())

    '''
        更新状态
    '''
    def add_action(self, actions_name, min_end_time):
        template_actions = self.parser.actions
        
        for time, act, duration in sorted(actions_name):
            
            if time <= min_end_time:
                if 'drip' in act or 'basin' in act:
                    continue
                sp = re.split('[( )]', act)
                sp = sp[1:-1]
                
                for action in template_actions:
                    
                    if action.name == sp[0]:
                        
                        tem_act = copy.deepcopy(action)
                        tem_act = utils.replace_param(tem_act, sp[1:])
                        
                        self.Actions.append((self.time + time, tem_act, 'at start'))
                        self.Actions.append((self.time + time + duration, tem_act, 'at end'))
                        break
    
    def update_state(self, actions_name, min_end_time, stop_time):
        
        self.add_action(actions_name, min_end_time)
        
        for time, act, status in sorted(self.Actions, key = lambda action: action[0]):
                if time <= self.time + min_end_time:
                    print(f'{time} {act.name} {act.parameters}')
                    # with open('../data/211/actions.txt') as f:
                    #     f.write(f'{time} {act.name} {act.parameters}')
                    self.parser.state = utils.apply(act, status, self.parser.state)
                    
                    if 'hangoff' in act.name or 'hangup' in act.name or 'move-gear-equip' in act.name or 'start-moving' in act.name: 

                        self.update_pole_and_product(act, status)

                    if 'move-pole' in act.name:

                        pole = act.parameters[0]

                        if pole in stop_time and status == 'at start' and self.time + stop_time[pole][0] == time:
                            
                            self.Line.Poles.dict[pole].stop_time = self.time + stop_time[pole][1]

                        elif self.Line.Poles.dict[pole].stop_time == time:
                            
                            state = list(self.parser.state)
                            
                            self.Line.Poles.dict[pole].stopping = True

                            # state.remove(('pole_start_moving', pole))
                            
                            # state.append(('pole_stop_moving',pole))
                            
                            self.parser.state = tuple(state)
        
        for i in range(len(self.Actions) - 1, -1, -1):
            
            if self.Actions[i][0] <= self.time + min_end_time:
                
                self.Actions.pop(i)
        
        self.Actions = sorted(self.Actions, key = lambda act: act[0])
        
    def update_products_position(self):
        
        for s in self.parser.state:
            
            if 'product_at' in s:
                
                product = s[1]
                
                if product in self.products:
                    
                    position = int(s[2][4:])
                    
                    self.products[product].position = position
               
    def update_pole_and_product(self, action, status):
        pole = action.parameters[0]
        product = action.parameters[-1]
        if 'start-moving' in action.name and status == 'at start':
            
            self.Line.Poles.dict[pole].stopping = False
        if product in self.products:
            if 'hangoff' in action.name and status == 'at start':
                
                self.products[product].mid = True
                self.Line.Poles.dict[pole].mid = True
            
            elif 'hangoff' in action.name and status == 'at end':
                self.products[product].mid = False
                self.products[product].pole = None
                self.products[product].select = False
                
                self.Line.Poles.dict[pole].mid = False
                self.Line.Poles.dict[pole].product = None
                self.Line.Poles.dict[pole].select = False
                self.Line.Poles.dict[pole].up_down = 1
                
            
            elif 'hangup' in action.name and status == 'at start':
                self.products[product].mid = True
                self.products[product].pole = pole
                
                self.Line.Poles.dict[pole].mid = True
                self.Line.Poles.dict[pole].product = product
                   

            elif 'hangup' in action.name and status == 'at end':
                self.products[product].mid = False
                self.Line.Poles.dict[pole].up_down = 3
                
                self.Line.Poles.dict[pole].mid = False
                
            # elif 'hang-off-up' in action.name and status == 'at start':
            #     self.products[product].mid = True
            #     self.products[product].pole = pole

            #     self.Line.Poles.dict[pole].product = product
            #     self.Line.Poles.dict[pole].mid = True

            # elif 'hang-off-up' in action.name and status == 'at end':
            #     self.products[product].mid = False
                
            #     self.Line.Poles.dict[pole].mid = False
            
            elif 'stop-moving' in action.name and status == 'at end':

                self.Line.Poles.dict[pole].stopping = True   
            
            if 'hangoff-pole-exchanging' in action.name and status == 'at end':
                gear = action.parameters[1]
                # self.products[product].pole = gear
                # self.products[product].select = True
                
                self.Line.Poles.dict[gear].product = product
                # self.Line.Poles.dict[gear].select = True
           
            # elif ' move-gear-equip' in action.name and status == 'at end':
            #     gear = action.parameters[0]
                
            #     self.products[product].pole = None
            #     self.products[product].select = False

            #     # self.Line.Poles.dict[gear].select = False
            #     # self.Line.Poles.dict[gear].product = None
            elif 'hangup-pole-exchanging' in action.name and status == 'at end':
                gear = action.parameters[1]
                self.Line.Poles.dict[gear].select = None
                self.Line.Poles.dict[gear].product = None
        else:
            if 'hangoff' in action.name and status == 'at end':

                self.Line.Poles.dict[pole].mid = False
                self.Line.Poles.dict[pole].product = None
                self.Line.Poles.dict[pole].select = False
           
    def sort_actions_name(self, actions_name):
        temp = []
        for act in sorted(actions_name):
            act = list(act)
            act[0] += self.time
            temp.append(act)
        return temp
    '''
        总的plan
    '''
    def execute(self):
        self.Line.Products.add_product(self.parser, 1, 'craft211', db)
        self.Line.Products.add_product(self.parser, 1, 'craft211', db)
        self.Line.Products.add_product(self.parser, 1, 'craft211', db)
        self.Line.Products.add_product(self.parser, 1, 'craft211', db)
        self.Line.Products.add_product(self.parser, 1, 'craft211', db)
        self.Line.Products.add_product(self.parser, 1, 'craft211', db)
        self.Line.Products.add_product(self.parser, 1, 'craft211', db)
        Actual_time = {}
        while True:
            self.add_product()

            goal = self.gen_goal() 
            utils.state2pddl(self.parser, goal, _config.other_config['new_problem_path'])
            if goal:
                subprocess.run(f'D:/cygwin64/bin/python2.7  {_config.other_config["planning_path"]} she {_config.domain_config["domain_path"]} {_config.other_config["new_problem_path"]} --no-iterated  --time 5 > console_output.txt', shell=True)
            actions_name = utils.parser_sas(goal)   
            stop_time = self.parser_stop_time(actions_name) 

            min_end_time = self.parser_min_time(actions_name, stop_time)

            actions_name = self.fliter_actions(actions_name, min_end_time, stop_time)

            actions_name = self.change_move_time(actions_name, stop_time, min_end_time)
            
            self.update_products(actions_name, min_end_time)
            
            actions_name = self.sort_actions_name(actions_name)
            # poles = self.Line.Poles.dict
            # plan2out.put({'actions': actions_name, 'poles': poles, 'time': self.time})
            # utils.output(actions_name, self.Line.Poles.dict,  self.time, self.init_time, self.output)
            self.update_state(actions_name, min_end_time, stop_time)                            
            
            self.update_products_position()

            self.del_end_products()

            self.Line.Poles.update_pole_position(self.parser.state)
            
            self.time += min_end_time

            if not self.products: 
                return

plan = Planning(_config)
plan.execute()
# finally:
#     subprocess.run(f'rm *.pddl output output.sas plan.validation *sas_plan ', shell=True)
#     plan.output.close()
