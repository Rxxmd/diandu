from interval import Interval
from datainit.global_var import Line, Parser, db, _config, PLC
import re
import copy
import subprocess
import ipdb
import utils
import time
class Planning:
    def __init__(self, config):
        self.init_time = time.time()
        self.time = 0    
        self.Actions = []   # 保存当前正在执行的动作
        self.products = {}  # 保存当前加入规划的物品
        self.parser = Parser
        self.Plc = PLC
        self.Line = Line

        self.parser.state_to_tuple()

        self.pole_move_time   = config.pole_config['pole_moving_duration']
        self.pole_stop_time   = config.pole_config['pole_stop_duration']
        self.pole_start_time  = config.pole_config['pole_start_duration']
        self.pole_load_time   = config.pole_config['pole_hangon_duration']
        self.pole_unload_time = config.pole_config['pole_hangoff_duration']
        self.gear_move_time   = config.gear_config['gear_moving_duration']
        
        self.tank_table      = {}
        self.hoist_table     = {}
        self.tank_map_table  = {}
        self.hoist_map_table = {}

        self.init_tank_table()
        self.init_hoist_table()

        self.output = open(_config.other_config['output_actions_path'], 'w')
    '''
        预判模块
    '''
    def init_tank_table(self):
        for tank in self.Line.Slots.array:

            if tank not in self.tank_table:
            
                self.tank_table[tank] = {}
    
    def init_hoist_table(self):
        for k, v in self.Line.Poles.dict.items():
            self.hoist_table[k] = {}

    def match_tank(self, tanks, lower_bound, temp_tt, sum_t,):

        for tank in tanks:
            for k, v in temp_tt[tank].items():
                upper = sum_t + lower_bound + self.pole_load_time + self.pole_unload_time 
                if Interval(sum_t, upper).overlaps(v):
                    return False
        return tank, lower_bound

    def match_pole(self, poles, tank, ntank, sum_t, time): 
        for pole in poles:
            # if pole.is_gear:
            #     ts = sum_t
            #     te = sum_t + time + 20
            # else:
            if tank == pole.position:
                move_time = 0
            else:
                move_time = abs(pole.position - tank) * self.pole_move_time - self.pole_stop_time - self.pole_start_time
            ts = sum_t + time - move_time
            
            te = sum_t + time + self.pole_unload_time + self.pole_load_time + abs(tank - ntank) + self.pole_stop_time + self.pole_start_time 
            
            if ts < 0:
                ts = 0
            for k, v in self.hoist_table[pole.name].items():
                if Interval(ts, te).overlaps(v) and Interval(ts, te) != v:
                    try:
                        intersection = Interval(ts, te) & v
                    except Exception as e:
                        print(e)
                        ipdb.set_trace()
                    if intersection.upper_bound - intersection.lower_bound:
                        pole.position = ntank
                        return pole, ts, te
                    
                    return False
            pole.position = ntank

            return pole, ts, te
    
    def constraint_table(self, product):
        poles = copy.deepcopy(self.Line.Poles.dict)
        temp_tt = copy.deepcopy(self.tank_table)
        temp_pt = copy.deepcopy(self.hoist_table)
        temp_tt_map = copy.deepcopy(self.tank_map_table)
        temp_pt_map = copy.deepcopy(self.hoist_map_table)
        sum_t = self.time
        for stage in range(product.stage, max(product.processes) + 1):
            process = product.processes[stage]
            lower_bound, upper_bound, tanks = process.lower_bound, process.upper_bound, process.tanks
            if (stage + 1) in product.processes: 
                next_tank = product.processes[stage + 1].tanks[-1]    # 获取下一个槽位
            else:
                next_tank = self.Line.Slots.blanking[-1]
            avai_poles = [v for k, v in poles.items() if tanks[0] in v.interval and next_tank in v.interval]  # 选出物品在当前槽位到目标槽位可用的天车
            
            res = self.match_tank(tanks, lower_bound, temp_tt, sum_t)  
            if not res:
                return False
            
            slc_tank, res_t = res

            res = self.match_pole(avai_poles, slc_tank, next_tank, sum_t, res_t) 
            if not res:
                return False

            pole, ts, te = res

        
            if set(tanks).issubset(self.Line.Slots.stocking) and product.stage == 0:    
                temp_pt[pole.name][(product.name, product.stage)] = Interval(ts, te)
                temp_pt_map[(product.name, product.stage)] = pole.name

                product.stage += 1
                sum_t += (te - ts) 
                
            else:  
                
                temp_tt[slc_tank][(product.name, product.stage)] = Interval(sum_t, sum_t + res_t)
                temp_tt_map[(product.name, product.stage)] = slc_tank
            
                temp_pt[pole.name][(product.name, product.stage)] = Interval(ts, te)
                temp_pt_map[(product.name, product.stage)] = pole.name
                
                product.stage += 1
                sum_t += (te - ts + res_t)
                   
        self.tank_table = temp_tt
        self.hoist_table = temp_pt
        self.tank_map_table = temp_tt_map
        self.hoist_map_table = temp_pt_map

        return True
    
    def add_product(self):
        for craft, products in self.Line.Products.dict.items():
            
            if not products:
                
                continue
            
            product = copy.deepcopy(products[0])
            if self.constraint_table(product):
                name = self.Line.Products.dict[craft][0].name
                
                self.products[name] = self.Line.Products.dict[craft][0]

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
            if pole in exe_poles:
                
                continue
            
            if pole.select and pole.product and pole.up_down != 2 and pole.product in self.products: 
                
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

            elif not pole.select and not pole.product and pole.stopping:
                
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

    def select_product(self, pole):
       
        min_t = 1000000000
        gproduct = None
        gtank = None
  
        for k ,v in self.products.items():
    
            lower_bound = v.processes[v.stage].lower_bound
            
            move_time = abs(pole.position - v.position) * self.pole_move_time
            
            if pole.position != v.position:
                move_time += self.pole_start_time + self.pole_stop_time
            
            if move_time >= lower_bound and v.position == v.next_slot:
                if (k, v.stage + 1) in self.tank_map_table:
                    tank = self.tank_map_table[(k, v.stage + 1)]
                else:
                    tank = v.processes[v.stage].tanks[-1]
                if (k, v.stage) not in self.hoist_map_table:
                    continue
                try:
                    hoist = self.hoist_map_table[(k, v.stage)]
                except:
                    ipdb.set_trace()
                if hoist == pole.name and tank in self.Line.Slots.empty:
                    tl = self.hoist_table[pole.name][(k, v.stage)].lower_bound
                    if min_t > tl:
                        gproduct = v
                        min_t = tl
                        gtank = tank
        
        
        
        if gproduct:
            # if abs(min_t - self.time) > self.pole_load_time + self.pole_unload_time :
            #     self.update_constraint_table(gproduct.name, gproduct.stage, min_t)
            if (gproduct.name,gproduct.stage) in self.tank_table[gtank]:
                self.tank_table[gtank].pop((gproduct.name,gproduct.stage))
                self.tank_map_table.pop((gproduct.name,gproduct.stage))
            if (gproduct.name,gproduct.stage - 1) in self.hoist_table:
                self.hoisttable[pole.name].pop((gproduct.name,gproduct.stage - 1))
            if (gproduct.name,gproduct.stage - 1) in self.hoist_map_table:
                self.hoist_map_table.pop((gproduct.name,gproduct.stage - 1))
            self.products[gproduct.name].stage += 1
            self.products[gproduct.name].next_slot = gtank

            self.Line.Slots.empty.remove(gtank)
            
        
            self.Line.Poles.dict[pole.name].select = gproduct.name
            
            return gproduct.name
            
        return None

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
                self.products[product].processes.pop(cur_stage - 1)
                
                self.products[product].available = True 

            if time <= min_end_time and ('hangoff' in act_name or 'move-gear-equip' in act_name):

                assert self.products[product].available, '产品没置为available'
                self.products[product].available = False
                self.products[product].processes[cur_stage].lower_bound += (time + duration)
                self.products[product].processes[cur_stage].upper_bound += (time + duration)
                    
        actions_name.extend(replace)

        output_actions.extend(replace)
        
        actions_name = list(set(actions_name) - set(delete))

        output_actions = list(set(output_actions) - set(delete))
        
        for k, v in self.products.items():
            
            if not v.available:
                self.products[k].processes[v.stage].lower_bound  -= min_end_time
                self.products[k].processes[v.stage].upper_bound -= min_end_time

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
            if len(v.processes) == 1 and  v.position in self.Line.Slots.blanking:
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
                    # print(time + self.time, act.name, act.parameters)
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
           
    '''
        总的plan
    '''
    def execute(self, queue):
        
        self.Line.Products.add_product(self.parser, 1, 'craft211', db)
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
            
            actions_name = self.update_products(actions_name, min_end_time)
            poles = self.Line.Poles.dict
            queue.put({'actions': actions_name, 'poles': poles, 'time': self.time})
            # utils.output(actions_name, self.Line.Poles.dict,  self.time, self.init_time, self.output)
            self.update_state(actions_name, min_end_time, stop_time)                            
            
            self.update_products_position()

            self.del_end_products()

            self.Line.Poles.update_pole_position(self.parser.state)
            
            self.time += min_end_time

            if not self.products: 
                return


# finally:
#     subprocess.run(f'rm *.pddl output output.sas plan.validation *sas_plan ', shell=True)
#     plan.output.close()
