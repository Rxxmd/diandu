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
    def __init__(self, from_plan_queue, to_plan_queue):
        super().__init__()
        self.time = 0                                   ## 设置算法初始运行时间，用来辅助判断动作的执行时间
        self.init_time = time.time()                    ## 记录现在的时间点， 用来辅助判断动作的执行时间
        self.actions = []                               ## 接收从算法传过来的动作序列 
        self.poles = {}                                 ## 接受从算法传过来的天车的对象，用来判断天车的上限移动和下限移动
        self.actions_queue = defaultdict(Queue)         ## 用来存放每个天车的动作序列， 一个天车一个队列，是对self.actions 清洗过后的数据
        self.ready_execute_actions = defaultdict(list)  ## 用来存放待执行的第一个动作
        self.from_plan_queue = from_plan_queue          ## 和算法通信的队列
        
    
    def __init_ready_execute_actions__(self):           ## 初始化self.ready_execute_actions
        for pole in self.poles:                         ##            
            self.ready_execute_actions[pole] = []       ##
                                                        ##
    
    def __get_data_from_queue__(self):                  ##
        '''                                             ##
            从队列中获取数据 actions time poles         ##
            一次取一组                                  ##
        '''                                             ##
        if not self.from_plan_queue.empty():            ## 如果队列不为空就获取数据，一定要加这个判断，
            data = self.from_plan_queue.get()           ## 否则程序会在这里阻塞，对空队列进行get会阻塞
            if data['actions'] == []:                   ##
                return None                             ## 如果没有动作序列，那就不需要取数据
            self.actions = data['actions']              ##
            self.time = data['time']                    ##
            self.poles = data['poles']                  ##
        return True                                     ##

    def __output_actions_to_plc__(self):
        '''
            对处理过的动作， 按照时间先后发送给plc 执行
        '''


        '''
            只有此函数会用到下面这些函数， 所以写成内联函数
        '''
        def _handle_below_move(start, action):
            '''
                执行下限移动的函数,如果是有wait=True表示需要等待 1,
                并且满足时间要求才可以执行，否则就不需要等待直接写入数据
            '''
            _, pole_num, slot_num, wait = action
            if wait:
                if start <= time.time() - self.init_time:
                    plcApi.below_move(pole_num, slot_num, wait)
                    return True
            else:
                plcApi.below_move(pole_num, slot_num, wait)
                return True
            return False
        
        def _handle_top_move(start, action):
            name, pole_num, slot_num, wait = action
            if wait:
                if start <= time.time() - self.init_time:
                    plcApi.top_move(pole_num, slot_num, wait)
                    return True
            else:
                plcApi.top_move(pole_num, slot_num, wait)
                return True
            return False
        
        def _handle_rise(start, action):
            if start <= time.time() - self.init_time:
                pole_num = action[1]
                plcApi.rise(pole_num, 1, 0)
                return True
            return False
        
        def _handle_down(start, action):
            if start <= time.time() - self.init_time:
                pole_num = action[1]
                plcApi.down(pole_num, 1, 0)
                return True
            return False
        
        def _handle_action_queue(saction):
            start, action = saction
            act = action[0]
            res = False
            if 'below-move' in act:
                res = _handle_below_move(start, action)
            elif 'top-move' in  act:
                res = _handle_top_move(start, action)
            elif 'rise' == act:
                res = _handle_rise(start, action)
            elif 'down' == act:
                res = _handle_down(start, action)
            if res:
                print(f'{time.time() - self.init_time:5.2f}', saction)
            self.time = start
            return res
        
        def check_all_poles_signal(poles):
            return plcApi.check_all_poles_signal(poles)
        
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
        
        for pole, al in self.ready_execute_actions.items():
            pole_queue = self.actions_queue[pole]
        #     while not al and not pole_queue.empty():
        #         action = self.actions_queue[pole].get()
        #         # 如果是move 且不需要等待那么就直接执行
        #         # 否则加入reap队列
        #         start, act = action
        #         if 'move' in act[0]:
        #             wait = act[-1]
        #             if not wait:
        #                 _handle_action_queue(action)
        #         else:
        #             self.ready_execute_actions[pole].append(action)
        #             break
            
            if not al and not pole_queue.empty():
                action = self.actions_queue[pole].get()
                res = _handle_action_queue(action)
                if not res:
                    self.ready_execute_actions[pole].append(action)
            elif al:
                action = al[0]
                res = _handle_action_queue(action)
                if res:
                    self.ready_execute_actions[pole].pop(0)

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
        
        def _filter_hang_action(act, start):
            _, name, pole, slot, product, _ = re.split(' |\(|\)',act)
            pole_num = int(self.poles[pole].order_num)
            if 'hangup' in name:
                self.poles[pole].up_down = 3
                temp = ('rise', pole_num)
            elif 'hangoff' in name:
                self.poles[pole].up_down = 1
                temp = ('down', pole_num)
                
            self.actions_queue[pole].put((start, temp))
       
        def _handle_start_action(start, act, duration):
            _, _, pole, _ = re.split(' |\(|\)',act)
            start_move_actions[pole] = start + duration

        for start, act, duration in sorted(self.actions, key=lambda a: a[0]):
            start += self.time

            if 'start-moving-pole' in act:
                _handle_start_action(start, act, duration)
            elif 'move' in act:
                _filter_move_action(act, start, start_move_actions)
            elif 'hang' in act:
                _filter_hang_action(act, start)
        self.actions = []
        if len(self.ready_execute_actions) == 0 and len(self.poles) > 0:
            self.__init_ready_execute_actions__()
    
    def get_output_form_algorithm(self):
        '''
            这个线程用来获取算法输出的数据
        '''
        while True:
            if not self.from_plan_queue.empty():
                self.__get_data_from_queue__()
                self.__handle_actions__()
    
    def send_output_to_plc(self):
        '''
            这个线程用来把结果输出到plc
        '''
        while True:
            self.__output_actions_to_plc__()
    
    def run(self):
        t1 = Thread(target=Output.get_output_form_algorithm, args = (self, ))
        t2 = Thread(target=Output.send_output_to_plc, args = (self, ))
        t1.start()
        t2.start()
        




