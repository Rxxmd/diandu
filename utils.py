import re
import glob
import ipdb
from datainit import plcApi
import time
def replace_param(action, param_list):
    param_map = {}
    
    """
        参数映射
    """
    for pl, parameter in zip(param_list, action.parameters):
        param_map[parameter[0]] = pl

    
    def map_args(x):
        temp = []
        for pre in x:
            if pre in param_map.keys():
                temp.append(param_map[pre])
            else:
                temp.append(pre)
        return tuple(temp)
    """
        过滤at start, at end 命题
    """
         
    action.positive_preconditions = frozenset(map(map_args,  action.positive_preconditions))
    action.negative_preconditions = frozenset(map(map_args,  action.negative_preconditions))
    action.add_effects = frozenset(map(map_args,  action.add_effects))           
    action.del_effects = frozenset(map(map_args,  action.del_effects))           
    action.parameters = param_list
    return action

def apply(action, status, state):

    def filter_predicates(pro, status):

        return [p[1:] for p in pro if p[0] == status or p[0] == 'over all']

    pos_pres = filter_predicates(action.positive_preconditions, status)
    neg_pres = filter_predicates(action.negative_preconditions, status)
    add_effs = filter_predicates(action.add_effects, status)            
    del_effs = filter_predicates(action.del_effects, status)    
    
    assert check(state, pos_pres, neg_pres), '有命题不再state中'

    return tuple(tuple(set(state).difference(del_effs).union(add_effs)))

def check(state, pos_pres, neg_pres):
    return all(pre for pre in pos_pres if pre in state) and \
           all(pre for pre in neg_pres if pre in state)

def state2pddl(parser, goal, path):
    with open(path, 'w') as f:
        print('(define (problem electroplating)', file=f)
        print('\t(:domain Electroplating)', file=f)
        print('\t(:objects', file=f)

        for obj in parser.objects:
            for o in parser.objects[obj]:
                print('\t\t'+o+' - '+obj, file=f)

        print('\t\t)', file=f)
        print('\t(:init', file=f)

        for s in parser.state:
            s = str(s)
            s = s.replace("'", '')
            s = s.replace(",", '')
            print('\t\t'+s, file=f)
        print('\t)', file=f)
        print('\t(:goal', file=f)
        print('\t(and', file=f)

        for g in goal:
            print('\t\t'+str(g), file=f)
        print('\t)', file=f)
        print('\t)', file=f)
        # print('\t(:metric minimize (TOTAL-TIME))', file=f)
        print(')', file=f)

def is_invalid_action(start_poles, move_poles, actions_name):
    for sp in start_poles:
        if sp[1] not in move_poles or sp[0] > move_poles[sp[1]]:
            temp = [act for act in actions_name if sp[1].lower() in act[1] and 'start-moving-pole' in act[1] and float(act[0]) == sp[0]]
            for t in temp:
                actions_name.remove(t)

def parser_sas(goal):
    actions_name = []
    products = ''
    start_poles = []
    move_poles = {}

    if goal:
        # 规划出来的文件名字为 tmp_sas_plan  |  tmp_sas_plan.1
        for name in glob.glob('tmp_sas_plan*'):
            tmp_plan = name

        # 解析当前在subgoal的物品
        for sg in goal:
            products = products + ' ' + sg
        try:
            with open(tmp_plan) as sas_plan:
                
                for line in sas_plan:
                    if ';' not in line:
                        line = line.strip('\n')
                        regMatch = re.findall(
                            r'(\d+\.\d+): ([(].*[)]) [[](\d+)\.\d+[]]', line)

                        if 'START-MOVING-POLE' in line:
                            reg = re.findall(r'(\d+\.\d+).*(POLE\d+)', line)[0]
                            start_poles.append((float(reg[0]), reg[1]))
                        if 'MOVE-POLE' in line:
                            reg = re.findall(r'(\d+\.\d+).*(POLE\d+)', line)[0]
                            move_poles[reg[1]] = float(reg[0])
                        # 删除多余的hangup动作，如果物品不在subgoal里，不执行它的hanggup动作
                        if 'HANGUP'  in line:
                            reg = regMatch[0][1].split(' ')
                            reg = reg[-1].split(')')
                            product = reg[0]
                            product = product.lower()
                            if product not in products:
                                print('出现多余的hangup hangup 动作')
                                # ipdb.set_trace()
                                continue
                        # 解析出来的动作，添加到actions_name
                        if regMatch != []:
                            actions_name.append(
                                (float(format(float(regMatch[0][0]), '.1f')), regMatch[0][1].lower(), float(format(float(regMatch[0][2])))))
        except:
            # 如果没有解，就跳过，等到有些动作执行完成就不冲突了
            pass
    is_invalid_action(start_poles, move_poles, actions_name)
    return actions_name

def output(actions, poles,  alg_time, init_time, f):
    data = plcApi._PLC.Read(15401, len(poles), 0)
    actions = sorted(actions, key = lambda act: act[0])
    temp = {}
    for start, act, duration in actions:
        while time.time() < init_time + alg_time +  start:
            time.sleep(init_time + alg_time + start - time.time())
        if 'start-moving-pole' in act:
            _, name, pole, _ = re.split(' |\(|\)',act)
            
            temp[pole] = start + duration
        elif 'move' in act:
            _, name, pole, cur_slot, des_slot, *_ = re.split(' |\(|\)',act)
            if pole in temp:
                
                start -= temp[pole] 
                duration += temp[pole]
                temp.pop(pole)
            
            act = f'({name} {pole} {cur_slot} {des_slot})'
            des_slot = int(des_slot[4:])
            print(f'{alg_time + start:7} {act:50} {duration}', file = f)

            # if poles[pole].up_down == 1:
                
            #     plcApi.below_move(poles[pole].order_num, des_slot)
            
            # elif poles[pole].up_down == 3:
                
            #     plcApi.top_move(poles[pole].order_num, des_slot)
        else:
            
            print(f'{alg_time + start:7} {act:50} {duration}', file = f)
             
            # _, name, pole, slot, product, _ = re.split(' |\(|\)',act)
            # pole_num = int(poles[pole].order_num)

            # if 'hangup' in act and poles[pole].up_down == 1 :
            #     plcApi.rise(pole_num, 1, 0) 
            
            # elif 'huangoff' in act and poles[pole].up_down == 1:
            #     plcApi.down(pole_num, 1, 0) 

   
        














 
    