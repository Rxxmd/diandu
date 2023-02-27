from collections import defaultdict
from datainit import plcApi
import time
import re
import ipdb

class Output:
    def __init__(self):
        self.actions = []
        self.poles = {}
        self.time = 0
        self.get_next = True    # 只有get next 为 True 的时候才可以从队列中获取数据

    def __get_data_from_queue__(self, queue):
        '''
            从队列中获取数据 actions time poles
            一次取一组
        '''
        if not queue.empty():
            
            data = queue.get()
            if data['actions'] == []:
                return None
            self.actions = data['actions']
            self.time = data['time']
            self.poles = data['poles']
            
            self.get_next = False
        return True 

    def __output_actions_to_plc__(self):
        '''
            对处理过的动作， 按照时间先后发送给plc 执行
        '''

        filter_actions = self.__handle_actions__()
        
        
        def _handle_below_move(action):
            name, pole_num, slot_num, wait = action
            if wait:
                if start > self.time:
                    plcApi.below_move(pole_num, slot_num, wait)
            else:
                    plcApi.below_move(pole_num, slot_num, wait)
        
        def _handle_top_move(action):
            name, pole_num, slot_num, wait = action
            if wait:
                if start > self.time:
                    plcApi.top_move(pole_num, slot_num, wait)
            else:
                plcApi.top_move(pole_num, slot_num, wait)

        def _handle_rise(action):
            pole_num = action[1]
            plcApi.rise(pole_num, 1, 0)
        
        def _handle_down(action):
            pole_num = action[1]
            plcApi.down(pole_num, 1, 0)
        
        for start in sorted(filter_actions):     # sort
            actions = filter_actions[start]      # 时间一样的动作同时执行
        
            for action in actions: 
                print(self.time, action) 
                act = action[0]
                if 'below-move' == act:
                    _handle_below_move(action)
                elif 'top-move' == act:
                    _handle_top_move(action)
                elif 'rise' == act:
                    _handle_rise(action)
                elif 'down' == act:
                    _handle_down(action)
        self.get_next = True

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
        temp_actions = defaultdict(list)      # 存放清洗后的数据
        
        def _filter_move_action(act,):
            flag = False
            
            _, name, pole, cur_slot, des_slot, *_  = re.split(' |\(|\)',act)
            
            if pole in start_move_actions:
                flag = True
            
            slot_num = des_slot[4:]
            pole_num = self.poles[pole].order_num
            
            
            if self.poles[pole].up_down == 1:
                if flag:
                    return (f'below-move-start', pole_num, slot_num, True)
                else:
                    return (f'below-move-start', pole_num, slot_num, False)
            elif self.poles[pole].up_down == 3:
                if flag:
                    return (f'top-move-start', pole_num, slot_num, True)
                else:
                    return (f'top-move-start', pole_num, slot_num, False)
            
        def _filter_hang_action(act):
            _, name, pole, slot, product, _ = re.split(' |\(|\)',act)
            pole_num = int(self.poles[pole].order_num)
            if 'hangup' in name:
                return ('rise', pole_num)
            elif 'hangoff' in name:
                return ('down', pole_num)
       
        def _handle_start_action(start, act, duration):
            _, _, pole, _ = re.split(' |\(|\)',act)
            start_move_actions[pole] = start + duration

        for start, act, duration in sorted(self.actions, key=lambda a: a[0]):
            if 'start-moving-pole' in act:
                new_act = _handle_start_action(start, act, duration)
            elif 'move' in act:
                _, name, pole, cur_slot, des_slot, *_  = re.split(' |\(|\)',act)
                new_act = _filter_move_action(act)
                
                if pole in start_move_actions:
                    start -= start_move_actions[pole] 
                    start_move_actions.pop(pole)
            elif 'hang' in act:
                new_act = _filter_hang_action(act)
            if new_act is not None:
                temp_actions[self.time + start].append(new_act)
    
        return temp_actions
    
    def excute(self, queue):
        while True:
            if not queue.empty():
                data = self.__get_data_from_queue__(queue)
                if data is not None:
                    self.__output_actions_to_plc__()
                    # print(self.actions, self.time, self.poles)




