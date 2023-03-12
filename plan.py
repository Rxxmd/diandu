from collections import defaultdict, namedtuple
import portion as P
from datainit.global_var import Line, Parser, db, _config, PLC
import re
import copy
import subprocess
import ipdb
import utils
import time
from algorithm.predict import Predict

class Planning:
    def __init__(self, config):
        self.init_time = time.time()
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

        self.pole_min_end_times = {}   # 用来记录每个天车的下一次规划的时间点
        self.tank_ocupy_time = {}
        self.pole_move_time   = config.pole_config['pole_moving_duration']
        self.pole_stop_time   = config.pole_config['pole_stop_duration']
        self.pole_start_time  = config.pole_config['pole_start_duration']
        self.pole_load_time   = config.pole_config['pole_hangon_duration']
        self.pole_unload_time = config.pole_config['pole_hangoff_duration']
        self.gear_move_time   = config.gear_config['gear_moving_duration']
        self.collision_time = 5
        self.pole_interval = 4
        self.cut_pole = None
        self.init_pole_min_end_time()

        # self.output = open(_config.other_config['output_actions_path'], 'w')
    def init_pole_min_end_time(self):
        for pole in self.Line.Poles.dict:
            self.pole_min_end_times[pole] = float('inf')

    def add_product(self):
        # data = PLC.get_bar_position(self.Line.Slots.stocking)
        # if data and any(data.values()):
        #     positions = [k for k ,v in data.items() if v == 1]
        #     for pos in positions :
        #         if not self.lock_stocking_slot[pos]:
        #             print('添加物品成功')
        #             self.lock_stocking_slot[pos] = True
        #             self.Line.Products.add_product(self.parser, pos, 'craft211', db)
        for craft, products in self.Line.Products.dict.items():
            if not products:
                continue
            product = copy.deepcopy(products[0])
            product =  self.predict.pre_sort_product(product,self.time)
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

        for pole in poles:
            if pole.name in exe_poles:
                continue
            
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

         
            elif pole.select and not pole.product and not pole.mid:
                goal.append(f'(pole_have_things {pole.name} {pole.select})')

            elif not pole.select and not pole.product and pole.stopping and not pole.mid:
                
                product = self.select_product(pole)

                if product:
                    
                    goal.append(f'(pole_have_things {pole.name} {product})')
        state = tuple(state)
        
        self.parser.state = state
        return goal
   
    def gen_goal(self):

        gear_goal = self.gen_gear_goal()
        pole_goal = self.gen_pole_goal()
        goal = gear_goal + pole_goal
        return goal

    def record_ocupy_tank_time(self, tank, start_time):
        self.tank_ocupy_time[tank] = P.closed(start_time, start_time + self.pole_load_time)

    def is_collision(self, tank, start_time):
        # pole_interval = -(-self.pole_interval // 2)
        pole_interval = self.pole_interval
        tanks = list(range(tank - pole_interval, tank + pole_interval + 1))
        if set(tanks) & self.tank_ocupy_time.keys():
            for tank in set(tanks) & self.tank_ocupy_time.keys():
                if P.closed(start_time, start_time + self.pole_load_time) & self.tank_ocupy_time[tank]:
                    return True
        return False
        
    def select_product(self, pole):
        min_t = float('inf')
        gproduct = None
        gtank = None
        # 确定pole的下一个物品
        # 预估pole下一次取物品的时间， 记录到pole_min_end_Time
        
        for k ,v in self.products.items():
            # upper是预排序好的完成时间
            try:
                hoist = v.hoist_table[v.stage + 1][1]
            except:
                hoist = v.hoist_table[v.stage][1]
            if hoist == pole.name:
                
                upper = v.tank_table[v.stage][0].upper
                move_time = abs(pole.position - v.position) + self.pole_start_time + self.pole_stop_time
                if pole.position == v.position:
                    move_time = 0
                #          已经反应的时间                         反应时间的下界
                if self.time - v.process_start_time >= v.processes[v.stage].lower_bound - move_time:
                    v.available = True
                if upper - self.time <= move_time and v.available and v.position == v.next_slot:
                # if v.hoist_table[v.stage + 1] and  v.hoist_table[v.stage + 1][0].lower <= self.time and v.position == v.next_slot and v.available:
                    # print(self.time - v.hoist_table[v.stage][0].lower)
                    # if self.time - v.hoist_table[v.stage][0].lower > 10:
                    #     ipdb.set_trace()
                    
                    tank = v.tank_table[v.stage][1]
                    hoist = v.hoist_table[v.stage + 1][1]
                    end_move_time = self.time + move_time + self.pole_load_time + self.pole_start_time + self.pole_stop_time + abs(tank - v.position)

                    cols1 = self.is_collision(v.position,self.time + move_time)
                    cols2 = self.is_collision(tank, end_move_time)
                    
                    if cols1 or cols2:
                        return None
                   
                    if hoist == pole.name and tank in self.Line.Slots.empty:
                        tl = upper
                        if min_t > tl:
                            gproduct = v
                            min_t = tl
                            gtank = tank
                
                else:
                    
                    if upper < min_t and v.position == v.next_slot:
                        min_t = upper
                        self.pole_min_end_times[pole.name] = upper - self.time - move_time
                        
        if gproduct:
            self.record_ocupy_tank_time(v.position, self.time + move_time)
            self.record_ocupy_tank_time(gtank, end_move_time - self.pole_unload_time)
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
    def add_action(self, actions_name, min_end_time, plan2out):
        template_actions = self.parser.actions
        poles = self.Line.Poles.dict
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
                        
                        # plan2out.put({'action': (self.time + time, act, duration), 'poles': poles})
                        break
    
    def update_state(self, actions_name, min_end_time, stop_time, plan2out):
        
        self.add_action(actions_name, min_end_time, plan2out)
        
        for time, act, status in sorted(self.Actions, key = lambda action: action[0]):
                if time <= self.time + min_end_time:
                    # print(f'{time} {act.name} {act.parameters}')
               
                    self.parser.state = utils.apply(act, status, self.parser.state)
                    
                    if 'hangoff' in act.name or 'hangup' in act.name or 'move-gear-equip' in act.name or 'start-moving' in act.name:
                            
                        self.update_pole_and_product(act, status)

                    if 'move-pole' in act.name:

                        pole = act.parameters[0]

                        if pole in stop_time and status == 'at start' and self.time + stop_time[pole][0] == time:
                            
                            self.Line.Poles.dict[pole].stop_time = self.time + stop_time[pole][1]

                        elif self.Line.Poles.dict[pole].stop_time == time:
                            
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
                if position in self.lock_stocking_slot and self.lock_stocking_slot[position]:
                    self.lock_stocking_slot[position] = False
                self.products[product].mid = False
                self.Line.Poles.dict[pole].up_down = 3
                
                self.Line.Poles.dict[pole].mid = False
            
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
    def execute(self, plan2out, out2plan):

        # self.Line.Products.add_product(self.parser, 1, 'craft211', db)
        # self.Line.Products.add_product(self.parser, 1, 'craft211', db)
        # self.Line.Products.add_product(self.parser, 1, 'craft211', db)
        # self.Line.Products.add_product(self.parser, 1, 'craft211', db)
        # self.Line.Products.add_product(self.parser, 1, 'craft211', db)
        # self.Line.Products.add_product(self.parser, 1, 'craft211', db)
        count = 0
        start = time.time()
        while True:
            if (time.time() - start) % 200 >= count:
                self.Line.Products.add_product(self.parser, 1, 'craft211', db)
                count += 1

            self.add_product()
            self.predict.products = self.products
       
            goal = self.gen_goal() 
            
            if goal:
                utils.state2pddl(self.parser, goal, _config.other_config['new_problem_path'])
                subprocess.run(f'D:/cygwin64/bin/python2.7  {_config.other_config["planning_path"]} she {_config.domain_config["domain_path"]} {_config.other_config["new_problem_path"]} --no-iterated  --time 5 > console_output.txt', shell=True)
            actions_name = utils.parser_sas(goal)   
            
            stop_time = self.parser_stop_time(actions_name) 
            min_end_time = self.parser_min_time(actions_name, stop_time)
            
            actions_name = self.fliter_actions(actions_name, min_end_time, stop_time)

            actions_name = self.change_move_time(actions_name, stop_time, min_end_time)
            
            self.update_products(actions_name, min_end_time)
            # out_actions = self.sort_actions_name(actions_name)
            # ipdb.set_trace()
            # if out_actions:
            #     poles = self.Line.Poles.dict
            #     plan2out.put({'actions': sorted(out_actions), 'poles': poles})
            # utils.output(actions_name, self.Line.Poles.dict,  self.time, self.init_time, self.output)
            self.update_state(actions_name, min_end_time, stop_time, plan2out)                            
            
            self.update_products_position()

            self.del_end_products()

            self.Line.Poles.update_pole_position(self.parser.state)
            
            self.time += min_end_time

            # if not self.products: 
            #     return

plan = Planning(_config)
plan.execute(1,1)
# finally:
#     subprocess.run(f'rm *.pddl output output.sas plan.validation *sas_plan ', shell=True)
#     plan.output.close()
