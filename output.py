from collections import defaultdict
import multiprocessing
from queue import Queue
from datainit import plcApi
from threading import Thread
import time
import re
from watchpoints import watch
import ipdb
output_data = {}
class Output(multiprocessing.Process):
    def __init__(self, from_plan_queue, to_plan_queue, Line, config):
        super().__init__()
        self.error_time =  0                            ## 设置算法初始运行时间，用来辅助判断动作的执行时间
        self.init_time = time.time()                    ## 记录现在的时间点， 用来辅助判断动作的执行时间
        self.plan_time = 0
        self.actions = []                               ## 接收从算法传过来的动作序列 
        self.poles = {}                                 ## 接受从算法传过来的天车的对象，用来判断天车的上限移动和下限移动
        self.actions_queue = defaultdict(Queue)         ## 用来存放每个天车的动作序列， 一个天车一个队列，是对self.actions 清洗过后的数据
        self.ready_execute_actions = {}                 ## 用来存放待执行的第一个动作
        self.from_plan_queue = from_plan_queue          ## 和算法通信的队列
        self.to_plan_queue = to_plan_queue
        self.craft = Line.Craft.dict
        self.Line = Line
        self.stocking_bars = []
        self.pole_move_time   = config.pole_config['pole_moving_duration']
        self.pole_stop_time   = config.pole_config['pole_stop_duration']
        self.pole_start_time  = config.pole_config['pole_start_duration']
        self.pole_load_time   = config.pole_config['pole_hangon_duration']
        self.pole_unload_time = config.pole_config['pole_hangoff_duration']
        self.gear_move_time   = config.gear_config['gear_moving_duration']
        self.basin_close_time = config.pole_config['basin_close_time']
        self.basin_open_time =  config.pole_config['basin_open_time']
    
    def __init_ready_execute_actions__(self):           ## 初始化self.ready_execute_actions
        for pole in self.poles:                         ##            
            self.ready_execute_actions[pole] = False       ##
                                                        ##
    
    # def __get_data_from_queue__(self):                  ##
    #     '''                                             ##
    #         从队列中获取数据 actions time poles         ##
    #         一次取一组                                  ##
    #     '''                                             ##
    #     if not self.from_plan_queue.empty():            ## 如果队列不为空就获取数据，一定要加这个判断，
    #         data = self.from_plan_queue.get()           ## 否则程序会在这里阻塞，对空队列进行get会阻塞
    #         self.actions = data['action']              ##
    #         # self.time = data['time']                    ##
    #         self.poles = data['poles']                  ##
    #     return True                                     ##

    def _handle_below_move(self, start, action):
        '''
            执行下限移动的函数,如果是有wait=True表示需要等待 1,
            并且满足时间要求才可以执行，否则就不需要等待直接写入数据
        '''
        _, pole_num, slot_num, wait = action
        if wait:
            plcApi.below_move(pole_num, slot_num, wait)
        else:
            plcApi.below_move(pole_num, slot_num, wait)
        return True
    
    def _handle_top_move(self, start, action):
        name, pole_num, slot_num, wait = action
        if wait:
            plcApi.top_move(pole_num, slot_num, wait)
        else:
            plcApi.top_move(pole_num, slot_num, wait)
        return True
    
    def _handle_rise(self, start, action):
        pole_num = action[1]
        plcApi.rise(pole_num, 1, 0)
        return True
    
    def _handle_wait(self, start, action):
        pole_num, wait_time = action[1], action[2]
        plcApi.wait(pole_num, wait_time)
        return True
    
    def _handle_down(self, start, action):
        pole_num, tank, stage = action[1], action[2], action[3]
        plcApi.down(pole_num, 1, 0)
        plcApi.write_products_stage(tank, stage)
        return True
    
    def _handle_action_queue(self, saction):
        start, action = saction
        
        
        act = action[0]
        res = False
        if 'below-move' in act:
            res = self._handle_below_move(start, action)
        elif 'top-move' in  act:
            res = self._handle_top_move(start, action)
        elif 'rise' == act:
            res = self._handle_rise(start, action)
        elif 'down' == act:
            res = self._handle_down(start, action)
        elif 'wait' == act:
            res = self._handle_wait(start, action)
        # if res:
        #     print(f'{time.time() - self.init_time:5.2f}', saction)
        return res
    
    def check_all_poles_signal(self, poles):
        return plcApi.check_all_poles_signal(poles)
   
    def __output_actions_to_plc__(self):
        
        '''
            每个天车的动作都必须严格按照规划的时间执行，如果
            是相同时间执行的动作，那么一定要在同一秒执行，如
            果某一个动作延迟了， 那么所有的动作都需要延迟，下
            面我们把所有天车的第一个动作都放到ready_execute_actions
            这个队列里面。
            if 是移动动作并且不需要等待信号的，直接执行
            else 取所有动作序列里动作时间最小的一批动作，
                检查所有的天车的 signal 都为1， 一起执行。
                如果天车的signal 有一个不为1，那么就等待
                知道所有的天车的 signal都为0.
        '''
        if time.time() - self.init_time - self.error_time > self.plan_time:
            self.plan_time = time.time() - self.init_time - self.error_time
            self.to_plan_queue.put({'out_time':time.time() - self.init_time - self.error_time})
        for pole, al in self.ready_execute_actions.items():
            pole_queue = self.actions_queue[pole]
            # 如果是不需要等待的直接执行
            while not al and not pole_queue.empty():
                action = self.actions_queue[pole].get()
                # 如果是move 且不需要等待那么就直接执行
                # 否则加入reap队列
                start, act = action
                if 'move' in act[0]:
                    wait = act[-1]
                    if not wait:
                        self._handle_action_queue(action)
                    else:
                        self.ready_execute_actions[pole] = action
                        break
                else:
                    self.ready_execute_actions[pole] = action
                    break
        # 需要等待的全部加入self.ready_execute_actions
        # 找出self.ready_execute_actions的最小时间， 最小时间的一起执行
        if any(self.ready_execute_actions.values()):
            min_times = [act[0] for pole, act in self.ready_execute_actions.items() if act]
            min_times = sorted(min_times)
            min_time = min_times[0]
            
            
            
            # 找出同一时间执行的所有poles
            poles = [k for k, v in self.ready_execute_actions.items() if v and v[0] == min_time]
            pole_nums = [int(pole[4:]) for pole in poles]
            if self.check_all_poles_signal(pole_nums) and min_time + self.error_time <= time.time() - self.init_time:
                for pole in poles:
                    action = self.ready_execute_actions[pole]
                    self.ready_execute_actions[pole] = False
                    self._handle_action_queue(action)
                    self.error_time = (time.time() - self.init_time - min_time)
            # if al is None and not pole_queue.empty():
            #     action = self.actions_queue[pole].get()
            #     res = self._handle_action_queue(action)
            #     if not res:
            #         self.ready_execute_actions[pole] = action
            # elif al is not None:
            #     action = al
            #     res = self._handle_action_queue(action)
            #     if res:
            #         self.ready_execute_actions[pole] = None

    def __handle_actions__(self):
        '''
            处理动作， 把动作变成如下形式
            (start, below_move, pole_num, des_slot_num)
            (start, top_move, pole_num, des_slot_num)
            (start, below_move_start, pole_num, des_slot_num)
            (start, top_move_start, pole_num, des_slot_num)
            (start, rise, pole_num)
            (start, down, pole_num)
            
            把start move 和第一个动作组合move_start
        ''' 

        start_move_actions = {}  # 用来存放start move的字典
        
        def _filter_move_action(act, start, start_move_actions):
            flag = False
            
            _, name, pole, cur_slot, des_slot, *_  = re.split(' |\(|\)',act)
            
            if pole in start_move_actions:
                flag = True
            
            slot_num = des_slot[4:]
            pole_num = self.poles[pole].order_num
            
            if pole in start_move_actions:
                start -= 2 
                start_move_actions.pop(pole)
            
            if self.poles[pole].up_down == 1:
                if flag:
                    temp =  (f'below-move', pole_num, slot_num, True)
                else:
                    temp =  (f'below-move', pole_num, slot_num, False)
           
            elif self.poles[pole].up_down == 3:
                if flag:
                    temp = (f'top-move', pole_num, slot_num, True)
                else:
                    temp =  (f'top-move', pole_num, slot_num, False)
            self.actions_queue[pole].put((start, temp)) 
        
        def _filter_hang_action(act, start, craft, stage):
            _, name, pole, slot, product, _ = re.split(' |\(|\)',act)
            pole_num = int(self.poles[pole].order_num)
            process = self.craft[craft][stage]
            if 'hangup' in name:
                # 如果是hangup，根据craft 和 stage 替换成上升，滴水，合水盆
                # 上升
                self.poles[pole].up_down = 3
                temp = ('rise', pole_num)
                self.actions_queue[pole].put((start, temp))
                # 滴水
                drip = process.drip
                if drip > 0:
                    temp = ('wait', pole_num, drip)
                    self.actions_queue[pole].put((start + self.pole_load_time, temp))

            elif 'hangoff' in name:
                # 如果是hangoff，根据craft 和 stage 替换成下降，等待，开水盆
                # 等待
                wait = process.wait
                if wait < 0:
                    assert '等待时间小于0'
                if wait > 0:
                    temp = ('wait', pole_num, wait)
                    self.actions_queue[pole].put((start, temp))
                # 写入步序
                tank = self.poles[pole].position
                # temp = ('write_stage', tank, stage + 1)
                # 下降
                self.poles[pole].up_down = 1
                temp = ('down', pole_num, tank, stage + 1)
                self.actions_queue[pole].put((start + wait, temp))
       
        def _handle_start_action(start, act, duration):
            _, _, pole, _ = re.split(' |\(|\)',act)
            start_move_actions[pole] = start + duration

        while True:                               
            data = self.from_plan_queue.get()
            action = data['action']
            start, act, duration = action
            self.poles = data['poles']
            if 'start-moving-pole' in act:
                _handle_start_action(start, act, duration)
            elif 'move' in act:
                _filter_move_action(act, start, start_move_actions)
            elif 'hang' in act:
                craft = data['craft']
                stage = data['stage']
                _filter_hang_action(act, start, craft, stage)
            if len(self.ready_execute_actions) == 0 and len(self.poles) > 0:
                self.__init_ready_execute_actions__()
    
    def get_output_form_algorithm(self):
        '''
            这个线程用来获取算法输出的数据
        '''
        while True:
            if not self.from_plan_queue.empty():
                # self.__get_data_from_queue__()
                self.__handle_actions__()
    
    def send_output_to_plc(self):
        '''
            这个线程用来把结果输出到plc
        '''
        while True:
            self.__output_actions_to_plc__()
    
    def check_product(self):
        while True:
            # 查看上下料槽位是否有飞巴
            bar_positions = plcApi.get_bar_position(self.Line.Slots.stocking)
            # 如果有飞巴， 记录到self.stocking_bar
            if bar_positions:
                if any(bar_positions.values()):
                    for pos in bar_positions:
                        if pos not in self.stocking_bars:
                            self.stocking_bars.append(pos)
                    # 已经被取走物品的槽位， 发送给算法
                    empty_slot = list(set(self.stocking_bars) - set(bar_positions))
                    if empty_slot:
                        self.stocking_bars = list(set(self.stocking_bars) - set(empty_slot))
                        print(empty_slot, '的物品被取走了')
                        self.to_plan_queue.put({'empty_slot': empty_slot})
                else:
                    empty_slot = self.stocking_bars
                    if empty_slot:
                        self.to_plan_queue.put({'empty_slot': empty_slot})
                        self.stocking_bars = []
            time.sleep(3)
            

    def run(self):
        t1 = Thread(target=Output.get_output_form_algorithm, args = (self, ))
        t2 = Thread(target=Output.send_output_to_plc, args = (self, ))
        t3 = Thread(target=Output.check_product, args=(self, ))
        t1.start()
        t2.start()
        t3.start()
        




