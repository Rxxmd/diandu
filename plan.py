from collections import defaultdict, namedtuple
import portion as P
from datainit.global_var import Line, Parser, _config, PLC
import pandas as pd
import re
import copy
import subprocess
import ipdb
import utils
import time
import sys
from algorithm.predict import Predict

class Planning:
    def __init__(self, config):
        self.out_time = 0
        self.time = 0    
        self.predict = Predict(config, Line)  # 预判模块
        self.Actions = []   # 保存当前正在执行的动作
        self.products = {}  # 保存当前加入规划的物品
        self.parser = Parser
        self.Plc = PLC
        self.Line = Line
        self.output_time = time.time() #用来同步output类的时间
        self.parser.state_to_tuple()
        self.lock_stocking_slot = {slot:False for slot in self.Line.Slots.stocking} #读取上料槽

        self.pole_next_start_time = {}
        self.pole_min_end_times = {}   # 用来记录每个天车的下一次规划的时间点
        self.tank_ocupy_time = defaultdict(dict)
        self.pole_move_time   = config.pole_config['pole_moving_duration']
        self.pole_stop_time   = config.pole_config['pole_stop_duration']
        self.pole_start_time  = config.pole_config['pole_start_duration']
        self.pole_load_time   = config.pole_config['pole_hangon_duration']
        self.pole_unload_time = config.pole_config['pole_hangoff_duration']
        self.gear_move_time   = config.gear_config['gear_moving_duration']
        self.basin_time = config.pole_config['basin_time']
        self.pole_up_down_time = config.HOIST_UP_DOWN_DURATION
        self.pole_interval = config.HOIST_INTERVAL
        self.cut_pole = None
        self.predict_table = defaultdict(list)
        self.init_pole_min_end_time()
        self.record_time = defaultdict(list)  # 记录产品处理时间
    
    def init_pole_min_end_time(self):
        for pole in self.Line.Poles.dict:
            self.pole_min_end_times[pole] = float('inf')

    def update_predict_table(self, product):
        name = product.name
        for stage, time_tank in product.tank_table.items():
            if stage + 1 in product.hoist_table:
                pole = product.hoist_table[stage + 1][1]
                LB = time_tank[0].upper
                self.predict_table[pole].append((LB, (name, stage)))
        for pole in self.predict_table:
            self.predict_table[pole].sort(key = lambda x:x[0])

    def error_init(self):
        '''
            发生错误之后重启的处理方法
        '''
        slots = list(set(self.Line.Slots.array) - set(self.Line.Slots.stocking))
        bar_positions = PLC.get_bar_position(slots)
        craft_numbers = PLC.get_products_craft(slots) 
        stage_numbers = PLC.get_products_stage(slots)
        actual_times = PLC.get_actual_time(slots)
        # 临时记录stage 和craft 排序用
        temp = []
        if bar_positions and any(bar_positions.values()):
            positions = [k for k ,v in bar_positions.items() if v == 1]
            for pos in positions :
                print(f'检测到第{pos}号槽位有物品')
                stage = stage_numbers[pos]
                craft_number = craft_numbers[pos]
                actual_time = actual_times[pos]
                start_time = self.time - actual_time
                temp.append((stage, actual_time, craft_number))
                is_stocking = True
                if pos not in self.Line.Slots.stocking:
                    is_stocking = False
                self.Line.Products.add_product(self.parser, pos, craft_number, stage, start_time, is_stocking)
        temp = sorted(temp, key=lambda x:(x[0], x[1]), reverse=True)
        for craft, products in self.Line.Products.dict.items():
            self.Line.Products.dict[craft] = sorted(self.Line.Products.dict[craft], key=lambda x:(x.stage, x.process_start_time), reverse=True)
        # 按照stage的大小和反应时间排序，stage 大的排前面， 反应时间大的排前面
        for stage, actual_time, craft in temp:
            max_start = 100
            products = self.Line.Products.dict[craft]
            products = [p for p in products if p.stage == stage and p.process_start_time == self.time - actual_time] 
            product = copy.deepcopy(products[0])
            product =  self.predict.pre_sort_product(product,self.time, max_start)
            while not product:
                max_start += 1000
                product = copy.deepcopy(products[0])
                product =  self.predict.pre_sort_product(product,self.time, max_start)
            print(self.time, '添加物品成功')
            name = self.Line.Products.dict[craft][0].name
            self.products[name] = product
            self.Line.Products.dict[craft].pop(0)
            self.update_predict_table(product)

    def add_product(self):
        '''
            这个函数用来添加物品， 如果检测到上料槽位有物品， 那么就
            把物品加入到 slef.Line.Products
        '''
        # 从PLC 读取飞巴的位置, 工艺流程号， 步序
        bar_positions = PLC.get_bar_position(self.Line.Slots.stocking)
        craft_numbers = PLC.get_products_craft(self.Line.Slots.stocking) 
        stage_numbers = PLC.get_products_stage(self.Line.Slots.stocking)
        
        # 把每个位置的飞巴都加入 self.Line.Products
        if bar_positions and any(bar_positions.values()):
            positions = [k for k ,v in bar_positions.items() if v == 1]
            for pos in positions :
                if not self.lock_stocking_slot[pos]:
                    print(f'检测到第{pos}号槽位有物品')
                    stage = stage_numbers[pos]
                    craft_number = craft_numbers[pos]
                    self.lock_stocking_slot[pos] = True
                    self.Line.Products.add_product(self.parser, pos, craft_number, stage)
        # 对每个物品都进行预排序
        for craft, products in self.Line.Products.dict.items():
            if not products:
                continue
            product = copy.deepcopy(products[0])
            product =  self.predict.pre_sort_product(product,self.time, max_start = 1000)
            # 如果与排序成功了则从 self.Line.Products 中删除物品， 把物品加入self.products
            if product:
                name = self.Line.Products.dict[craft][0].name
                self.products[name] = product
                self.Line.Products.dict[craft].pop(0)
                self.update_predict_table(product)
                return True

    def accept_output_data(self, out2plan):
        '''
            接收output模块传过来的数据
        '''
        while not out2plan.empty():
            data = out2plan.get()
            if 'empty_slot' in data:
                empty_slot = data['empty_slot']
                self.check_product(empty_slot)
            elif 'out_time' in data:
                self.out_time = data['out_time']
            elif 'stop' in data:
                sys.exit()
                
    def check_product(self, empty_slot):
        '''
            接受output进程传过来的数据，看上料槽位的物品是否被拿走了
        '''
        for slot in empty_slot:
            if slot in self.lock_stocking_slot:
                self.lock_stocking_slot[slot] = False

    '''
        子目标模块
    '''
    def get_exe_poles(self):
        '''
            此函数用来检测执行了 at start 但是还没有
            at end 的动作的天车
        '''
        exe_poles = []

        for _, act, _ in self.Actions:

            exe_poles.append(act.parameters[0])
        
        return exe_poles

    def gen_gear_goal(self):
        '''
            此函数生成交换车的子目标
        '''
        goal = []
        gears = copy.deepcopy(self.Line.Gears.dict)
        exe_poles = self.get_exe_poles()
        for gear in gears.values():
            if gear.name in exe_poles:
                continue
            if gear.product and gear.position == gear.end:
                pass
            elif not gear.product and gear.position == gear.end:
                goal.append(f'(pole_position {gear.name} slot{gear.begin})')
            elif gear.product and gear.position == gear.begin:
                state = list(self.parser.state)
                product = self.products[gear.product]
                next_slot = 'slot' + str(gear.end)
                state.append(('target_slot', next_slot, product.name))
                
                goal.append(f'(product_at {gear.product} {next_slot})')
                
                tank = product.tank_table[product.stage][1]
                
                self.predict_table[gear.name].pop(0)
               
                self.products[product.name].next_slot = tank

                self.products[product.name].stage += 1

                self.products[product.name].available = False

                self.products[product.name].stage_start = float('inf')

                self.Line.Slots.empty.remove(tank)
        
        return goal

    def gen_pole_goal(self):
        '''
            此函数生成天车的子目标
        '''
        goal = []
        state = list(self.parser.state)

        self.Line.Slots.set_blanking_slot_empty()
        exe_poles = self.get_exe_poles()
        
        # 对每个天车按照预排序的时间先后顺序执行
        pole_goals = {}
        for pole, table in self.predict_table.items():
            if table:
                pole_goals[pole] = table[0]
                
        poles = sorted(pole_goals, key = lambda x:x[1][0])
        for pole in self.Line.Poles.dict:
            if pole not in poles:
                poles.append(pole)

        for pole in poles:
            
            if pole in self.Line.Gears.dict or pole in exe_poles:
                continue
            pole = self.Line.Poles.dict[pole]
          
            # 如果天车已经拿到物品了，子目标就是把物品放到下一个槽位
            if pole.select and pole.product and pole.up_down == 3 and pole.product in self.products: 
                
                product = self.products[pole.product]
                
                if product.position != product.next_slot:
                    next_slot = 'slot' + str(product.next_slot)

                    state.append(('target_slot', next_slot, product.name))
                    
                    goal.append(f'(product_at {product.name} {next_slot})')
                    if product.position not in self.Line.Slots.empty:
                        
                        self.Line.Slots.empty.append(product.position)
                    
                    if product.next_slot in self.Line.Slots.empty:
                        self.Line.Slots.empty.remove(product.next_slot)

            # 如果天车还没拿到物品， 但是已经选中物品了，子目标就是拿到物品
            elif pole.select and not pole.product and not pole.mid:
                goal.append(f'(pole_have_things {pole.name} {pole.select})')
            # 如果天车还没选择物品，即空闲状态
            elif not pole.select and not pole.product and pole.stopping and not pole.mid:
                # 如果天车需要空闲很久，那就移动到中间点
                if pole.name in pole_goals:
                    load_start_time = pole_goals[pole.name][0]
                    if load_start_time - self.time > self.pole_start_time + self.pole_stop_time + 2 * len(pole.interval) * self.pole_move_time:
                        mid_position = len(pole.interval)//2 + pole.interval[0]
                        if pole.position != mid_position:
                            goal.append(f'(pole_position {pole.name} slot{mid_position})')
                    else: 
                        product = self.select_product(pole, pole_goals)

                        if product:
                            goal.append(f'(pole_have_things {pole.name} {product})')
            elif not pole.select and not pole.product and not pole.stopping and not pole.mid:
                mid_position = len(pole.interval)//2 + pole.interval[0]
                if pole.position != mid_position:
                    goal.append(f'(pole_position {pole.name} slot{mid_position})')
                
        state = tuple(state)
        self.parser.state = state
        return goal
   
    def gen_goal(self):
        
        gear_goal = self.gen_gear_goal()
        pole_goal = self.gen_pole_goal()
        goal = gear_goal + pole_goal
        return goal

    def record_ocupy_tank_time(self, tank, start_time, pole):
        self.tank_ocupy_time[pole.name][tank] = P.closed(start_time, start_time + self.pole_load_time)

    def is_collision(self, tank, start_time, pole):
        '''
            判断天车在start_time + self.pole_load_time 
            区间是否会和别的天车碰撞
        '''
        # pole_interval = -(-self.pole_interval // 2)
        pole_interval = self.pole_interval
        
        tanks = list(range(tank - pole_interval, tank + pole_interval + 1))
        for k, v in self.tank_ocupy_time.items():
            if k != pole.name:
                if set(tanks) & set(v.keys()):
                    for tank in (set(tanks) & set(v.keys())):
                        if P.closed(start_time, start_time + self.pole_load_time) & v[tank]:
                            return True
                        
        return False
        
    def select_product(self, pole, pole_goals):
       
        # 确定pole的下一个物品
        upper = pole_goals[pole.name][0] - 3
        pname = pole_goals[pole.name][1][0]
        pstage = pole_goals[pole.name][1][1]
        product = self.products[pname]
        tank = product.tank_table[product.stage][1]
        hoist = product.hoist_table[product.stage + 1][1]
        # 计算移动的时间
        move_time = abs(pole.position - product.position) + self.pole_start_time + self.pole_stop_time
        if pole.position == product.position:
            move_time = 0
        # 如果物品反应的时间已经达到最低要求了， 那么就是available
        if self.time - product.process_start_time >= product.processes[product.stage].lower_bound - move_time:
            product.available = True
        if upper - self.time <= move_time and product.available and product.position == product.next_slot and tank in self.Line.Slots.empty:
            # 计算移动到目标槽位的时间
            end_move_time = self.time + move_time + self.pole_load_time + self.pole_start_time + self.pole_stop_time + abs(tank - product.position)
            # 判断是否会和别的天车碰撞 
            cols1 = self.is_collision(product.position,self.time + move_time, pole)
            cols2 = self.is_collision(tank, end_move_time, pole)
        
            if cols1 or cols2:
                return None
            self.record_ocupy_tank_time(product.position, self.time + move_time, pole)
            self.record_ocupy_tank_time(tank, end_move_time, pole)
            self.predict_table[pole.name].pop(0)
            self.products[product.name].next_slot = tank

            self.products[product.name].stage += 1

            self.products[product.name].available = False

            self.products[product.name].stage_start = float('inf')

            self.Line.Slots.empty.remove(tank)
        
            self.Line.Poles.dict[pole.name].select = product.name
        
            return product.name
            
        return None


        ipdb.set_trace()
        # for k ,v in self.products.items():
        #     # upper是预排序好的完成时间
        #     try:
        #         hoist = v.hoist_table[v.stage + 1][1]
        #     except:
        #         hoist = v.hoist_table[v.stage][1]
        #     if hoist == pole.name:
                
        #         upper = v.tank_table[v.stage][0].upper
                
        #         move_time = abs(pole.position - v.position) + self.pole_start_time + self.pole_stop_time
        #         if pole.position == v.position:
        #             move_time = 0
        #         #          已经反应的时间                         反应时间的下界
        #         if self.time - v.process_start_time >= v.processes[v.stage].lower_bound - move_time:
        #             v.available = True
                
        #         if upper - self.time <= move_time and v.available and v.position == v.next_slot:
                
        #             tank = v.tank_table[v.stage][1]
        #             hoist = v.hoist_table[v.stage + 1][1]
        #             end_move_time = self.time + move_time + self.pole_load_time + self.pole_start_time + self.pole_stop_time + abs(tank - v.position)
                    
        #             cols1 = self.is_collision(v.position,self.time + move_time, pole)
        #             cols2 = self.is_collision(tank, end_move_time, pole)
                    
        #             if cols1 or cols2:
        #                 return None
                   
        #             if hoist == pole.name and tank in self.Line.Slots.empty:
        #                 tl = upper
        #                 if min_t >= tl:
        #                     gproduct = v
        #                     min_t = tl
        #                     gtank = tank
                
        #         else:
        #             self.pole_next_start_time[pole.name] = upper - move_time
        if gproduct:
            self.record_ocupy_tank_time(v.position, self.time + move_time, pole)
            self.record_ocupy_tank_time(gtank, end_move_time - self.pole_unload_time, pole)
            self.products[gproduct.name].next_slot = gtank

            self.products[gproduct.name].stage += 1

            self.products[gproduct.name].available = False

            self.products[gproduct.name].stage_start = float('inf')

            self.Line.Slots.empty.remove(gtank)
        
            self.Line.Poles.dict[pole.name].select = gproduct.name
            
            return gproduct.name
            
        return None

    '''
        解析文件， 判断截断的动作
    '''

    def parser_min_time(self, actions_name, stop_time):
        # 计算下一次规划的时间点
        # 1. 移动的最后一个动作
        # 2. hangoff hangup 的开始时间， 结束时间
        #    在hangoff 开始时就登记他的结束时间
        # Actions_min_end_time = -1
        amet_pole = None
        act_min_end_time = float('inf')
        if self.Actions:
            act_min_end_time = self.Actions[0][0] - self.time
            amet_pole = self.Actions[0][1].parameters[0]
            
        # 一个天车运行完成的at start时间点 或者 一道工艺完成的时间点
        # 如果动作是 move pole 就去 at end 时间点
        # 如果动作是 hangoff hangup 就取 at start 时间点
        for time, act_name, duration in sorted(actions_name):
            if 'pole' in act_name:
                pole = re.findall(r'(pole\d+)', act_name)[0]
                
                if 'hang' in act_name and pole not in stop_time:
                    stop_time[pole] = (time, time) 

        # pmets = sorted(self.pole_min_end_times.items(), key = lambda s: s[1])
        
        # pmet_pole, pole_min_end_time = pmets[0][0], pmets[0][1] - self.time
        # if pole_min_end_time < 0:
        #     pole_min_end_time = float('inf')
        # elif pole_min_end_time == 0:
        #     self.pole_min_end_times[pmet_pole] = float('inf')
        pole_min_end_time = float('inf')
        pmet_pole = None
        st = sorted(stop_time.items(), key = lambda s: s[1][0])
        st_min_end_time = float('inf')
        if actions_name and st:
            smet_pole, st_min_end_time = st[0][0], st[0][1][0]
            if st[0][1][1] - st[0][1][0] == self.pole_start_time + self.pole_move_time:
                self.pole_min_end_times[smet_pole] = self.time +  st[0][1][0]
            else:
                self.pole_min_end_times[smet_pole] = self.time +  st[0][1][1] + self.pole_load_time
        min_end_time = min(st_min_end_time, pole_min_end_time, act_min_end_time)
        if min_end_time == act_min_end_time:
            self.cut_pole = amet_pole
        elif min_end_time == pole_min_end_time:
            self.cut_pole = pmet_pole
        else:
            self.cut_pole = smet_pole
        if float('inf') == min_end_time:
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
        hangoff_stop_time = {}
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
            
            if 'hang' in act_name:
                pole = re.findall(r'(pole\d+)', act_name)[0]
                hangoff_stop_time[pole] = time
            elif 'move-pole' in act_name:
                
                pole = re.findall(r'(pole\d+)', act_name)[0]
                
                if pole not in stop_time:
                    
                    stop_time[pole] = forward[pole] if pole in forward else inverse[pole]
                    
                    stop_time[pole] = (stop_time[pole][0], stop_time[pole][1] + self.pole_stop_time)
        # 如果是先hangoff 然后在移动的话就把最小的时间设置为hangoff 的开始时间
        for pole in hangoff_stop_time:
            if pole in stop_time:
                if hangoff_stop_time[pole] < stop_time[pole][0]:
                    stop_time[pole] = (hangoff_stop_time[pole], hangoff_stop_time[pole])
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
                stage = self.products[product].stage
                process = self.products[product].processes
            if time <= min_end_time:
                
                if time <= min_end_time and 'hangup' in act_name:
                    # drip_Time N次上升，滴水， 合水盆时间, 滴水用的是当前stage的滴水时间
                    drip, basin, up_num= process[stage - 1].drip, process[stage - 1].basin, process[stage - 1].up_num
                    drip_time = self.pole_load_time + up_num * self.pole_up_down_time + basin * self.basin_time + drip
                    output_actions.append((time, act_name, drip_time))

                    # 记录浸泡时间
                    if product not in self.record_time or not self.record_time[product]:
                        self.record_time[product].append(self.time)
                    else:
                        self.record_time[product][-1] = self.time - self.record_time[product][-1]
                
                elif time <= min_end_time and 'hangoff' in act_name:
                    # wait_time N次下降，滴水， 开水盆时间， 等待时间用的是下一个阶段的等待时间
                    basin = process[stage - 1].basin
                    if stage + 1 in process:
                        wait = process[stage + 1].wait
                        down_num = process[stage + 1].down_num
                    else:
                        wait = 0
                        down_num = 0
                    wait_time = self.pole_unload_time + down_num * self.pole_up_down_time + basin * self.basin_time + wait
                    output_actions.append((time, act_name, wait_time))
                    #记录浸泡时间
                    self.record_time[product].append(self.time + time + duration)

                    self.products[product].process_start_time = self.time + time + duration
                    self.products[product].available = False
                
                else:
                    output_actions.append((time, act_name, duration))
                    
        return output_actions

    def del_end_products(self):
        # 删除已经执行完最后一道 craft 的 product
        delete = {}
        # df = pd.DataFrame()
        for k, v in self.products.items():
            # df = pd.concat([df, pd.DataFrame(self.record_time[k])])
            if v.stage == max(v.processes) and  v.position in self.Line.Slots.blanking:
                delete[k] = v
                print(self.record_time[k])
                print(self.record_time[k], file = open('../data/211/output.txt', 'a'))
        # df.to_excel('../data/211/output.xlsx')
        self.products = dict(self.products.items() - delete.items())

    '''
        更新状态
    '''
    def add_action(self, actions_name, min_end_time, plan2out):
        '''
            这个函数把小于min_end_time的action加入到plan2out队列中和加入到self.Actions中
            actions_name: [(time, act_name, duration), ...]
            min_end_time: 最小结束时间
            plan2out: plan2out队列
        '''
        # template_actions 指的是没有特定参数的action
        template_actions = self.parser.actions
        poles = self.Line.Poles.dict
        for time, act, duration in sorted(actions_name):
            
            if time <= min_end_time:
                # 把act中的参数提取出来
                sp = re.split('[( )]', act)
                sp = sp[1:-1]
                
                for action in template_actions:
                    
                    if action.name == sp[0]:
                        # 把action中的参数替换成具体的参数
                        tem_act = copy.deepcopy(action)
                        tem_act = utils.replace_param(tem_act, sp[1:])
                        # 把action加入到self.Actions中
                        self.Actions.append((self.time + time, tem_act, 'at start'))
                        self.Actions.append((self.time + time + duration, tem_act, 'at end'))
                        # 把action加入到plan2out队列中
                        if 'hang' in act:
                            # 如果是hangup或者hangoff，需要传入stage和craft
                            product = tem_act.parameters[-1]
                            stage = self.products[product].stage
                            craft = self.products[product].craft
                            plan2out.put({'action': (self.time + time, act, duration), 'poles': poles, 'stage': stage, 'craft': craft})
                        else:
                            plan2out.put({'action': (self.time + time, act, duration), 'poles': poles})
                        break
    
    def update_state(self, actions_name, min_end_time, stop_time, plan2out):
        '''
            这个函数更新状态
            参数:
                actions_name: [(time, act_name, duration), ...]
                min_end_time: 最小结束时间
                stop_time: 停止时间
                plan2out: plan2out队列
        '''
        # 把actions_name中的action加入到plan2out队列中和加入到self.Actions中
        self.add_action(actions_name, min_end_time, plan2out)
        # 把self.Actions中的action按照时间排序
        for time, act, status in sorted(self.Actions, key = lambda action: action[0]):
                # 如果action的时间小于等于min_end_time，就更新状态
                if time <= self.time + min_end_time:
                    print(f'{time} {act.name} {act.parameters}')
                    # 更新状态
                    self.parser.state = utils.apply(act, status, self.parser.state)
                    
                    if 'hangoff' in act.name or 'hangup' in act.name or 'move-gear-equip' in act.name or 'start-moving' in act.name:
                        # 如果是hangoff或者hangup，需要调用update_pole_and_product函数
                        self.update_pole_and_product(act, status)
                     
                    if 'move-pole' in act.name:
                        # 如果是move-pole，需要根据stop_time字典来更新状态
                        pole = act.parameters[0]

                        if pole in stop_time and status == 'at start' and self.time + stop_time[pole][0] == time:
                            # 如果是move-pole的开始动作，且在stop_time字典中，且时间等于stop_time字典中的时间，就往pole中写入stop_time
                            self.Line.Poles.dict[pole].stop_time = self.time + stop_time[pole][1]

                        elif self.Line.Poles.dict[pole].stop_time == time:
                            # 如果是move-pole的结束动作，且时间等于stop_time字典中的时间，
                            # 就把pole的stop_time设置为True
                            # 并且更新state中pole为stop的状态
                            if not self.Line.Poles.dict[pole].select:
                                state = list(self.parser.state)
                                self.Line.Poles.dict[pole].stopping = True
                                state.remove(('pole_start_moving', pole))
                                state.append(('pole_stop_moving',pole))
                                
                                self.parser.state = tuple(state)
        
        for i in range(len(self.Actions) - 1, -1, -1):
            
            if self.Actions[i][0] <= self.time + min_end_time:
                
                self.Actions.pop(i)
        
        self.Actions = sorted(self.Actions, key = lambda act: act[0])
        
    def update_products_position(self):
        # 更新产品的位置
        for s in self.parser.state:
            
            if 'product_at' in s:
                
                product = s[1]
                
                if product in self.products:
                    
                    position = int(s[2][4:])
                    
                    self.products[product].position = position
               
    def update_pole_and_product(self, action, status):
        '''
            这个函数根据每个action 对 Product 和 Pole 进行相应的更新
            参数:
            action: 执行的动作
            status: at start | at end
        '''
        pole = action.parameters[0]
        product = action.parameters[-1]
        # 如果动作是启动天车start-moving, 就把pole 的stopping 属性置为False 
        if 'start-moving' in action.name and status == 'at start':
            self.Line.Poles.dict[pole].stopping = False
        
        if product in self.products:
           
            if 'hangoff' in action.name and status == 'at start':
                state = list(self.parser.state)
                self.Line.Poles.dict[pole].stopping = True
                state.remove(('pole_start_moving', pole))
                
                state.append(('pole_stop_moving',pole))
                
                self.parser.state = tuple(state)
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
                
                state = list(self.parser.state)
                if ('pole_start_moving', pole) in state:
                    self.Line.Poles.dict[pole].stopping = True
                    state.remove(('pole_start_moving', pole))
                    state.append(('pole_stop_moving',pole))
                    self.parser.state = tuple(state)

                
                self.products[product].mid = True
                self.products[product].pole = pole
                
                self.Line.Poles.dict[pole].mid = True
                self.Line.Poles.dict[pole].product = product

            elif 'hangup' in action.name and status == 'at end':
                position = self.products[product].position
                # if position in self.lock_stocking_slot and self.lock_stocking_slot[position]:
                #     self.lock_stocking_slot[position] = False
                self.products[product].mid = False
                self.Line.Poles.dict[pole].up_down = 3
                
                self.Line.Poles.dict[pole].mid = False
            
            elif 'stop-moving' in action.name and status == 'at end':

                self.Line.Poles.dict[pole].stopping = True   
            
            if 'hangoff-pole-exchanging' in action.name and status == 'at end':
                gear = action.parameters[1]
                self.Line.Gears.dict[gear].product = product
         
           
            elif ' move-gear-equip' in action.name and status == 'at end':
                gear = action.parameters[0]
                
                self.products[product].pole = None
                self.products[product].select = False

            elif 'hangup-pole-exchanging' in action.name and status == 'at end':
                gear = action.parameters[1]
                self.Line.Gears.dict[gear].product = None

            
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
    def execute(self, plan2out, out2plan):
        # self.Line.Products.add_product(self.parser, 1, 'craft211', db)

        start = 0
        self.error_init()
        while True:
            
            # if self.time - start >= 0 and start < 3000:
            #     self.Line.Products.add_product(self.parser, 1, 3, 1)
            #     start += 400
            
            self.add_product()
            self.accept_output_data(out2plan)
            if self.time - self.out_time <= 10:
                goal = self.gen_goal() 
                if goal:
                    utils.state2pddl(self.parser, goal, _config.other_config['new_problem_path'])
                    subprocess.run(f'D:/cygwin64/bin/python2.7  {_config.other_config["planning_path"]} she {_config.domain_config["domain_path"]} {_config.other_config["new_problem_path"]} --no-iterated  --time 5 > console_output.txt', shell=True)
                    actions_name = utils.parser_sas(goal)   
                    
                    stop_time = self.parser_stop_time(actions_name) 
                    min_end_time = self.parser_min_time(actions_name, stop_time)
                    
                    actions_name = self.fliter_actions(actions_name, min_end_time, stop_time)

                    actions_name = self.change_move_time(actions_name, stop_time, min_end_time)
                    actions_name = self.update_products(actions_name, min_end_time)
                else:
                    min_end_time = 1    
                    actions_name = []
                    stop_time = []
                
                self.update_state(actions_name, min_end_time, stop_time, plan2out)                            
                
                self.update_products_position()
            
                self.del_end_products()

                self.Line.Poles.update_pole_position(self.parser.state)
                self.Line.Gears.update_gear_position(self.parser.state)
                
                self.time += min_end_time
                # if not self.products: 
                #     return

# plan = Planning(_config)
# plan.execute(1,1)
# finally:
#     subprocess.run(f'rm *.pddl output output.sas plan.validation *sas_plan ', shell=True)
#     plan.output.close()
