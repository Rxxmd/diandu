'''
    运行流程：
        1.开始前
            a.检查天车自动 
            b.判断天车都在下限
            c.读取天车的位置
            d.检查所有的可用槽位
        2.预判
        3.规划
        4.输出一系列动作
        5.检查流水线的状态和当前pdll状态是否一致
            a. 若不一致 --> 2
            b. 一致 --> 3
        6.若遇到各种需要从新计算的情况，保存预判的顺序，从新计算
'''
from multiprocessing import Process, Queue
import subprocess
import time
from datainit import plcApi
from datainit.global_var import _config, Line
from plan import Planning
from output import *
TANKS = _config.slot_config['slots']
HOIST = _config.pole_config['poles']
# import subprocess
def is_all_hoist_below(hoists):
    data = plcApi.get_hoist_up_down(hoists)
    if all([v == 1 for v in data.values()]):
        return True
    
    res = [k for k, v in data.items() if v != 1]
    print(f'天车 {res} 没有在下限')
    return False

def is_all_hoist_auto(hoists):
    if not plcApi.get_hoist_auto(hoists):
        print(f'天车不是自动状态')
    else:
        return True

def check_hoist_status(hoists):
    
    while True: # 检查天车是否自动 和 天车都在下限
        
        if is_all_hoist_auto(hoists) and is_all_hoist_below(hoists):
            return    
        time.sleep(1)
    


# try:
#     plan = Planning(_config)
#     plan.execute()

# finally:
#     subprocess.run(f'rm *.pddl output output.sas plan.validation *sas_plan* ', shell=True)
    


def planing(plan2out, out2plan):
    plan = Planning(_config)
    plan.execute(plan2out, out2plan)


from multiprocessing import Process, Queue
if __name__ == '__main__': 
    try:
        check_hoist_status(HOIST)             # 检查天车在下限而且是自动状态才能开始规划
        plan2out = Queue()              
        out2plan = Queue()
        p1 = Process(target = planing, args=(plan2out, out2plan ))
        p2 = Output(plan2out, out2plan, Line, _config)

        p1.start()
        p2.start()
    finally:
        subprocess.run(f'rm *.pddl output output.sas plan.validation *sas_plan planSchedule console_output.txt compileSHE.exe.* ', shell=True)



        
    # plan = Planning(_config)
    # plan.execute()
# plcApi.below_move(1, 2)
# plcApi.rise(1, 1, 0)
# plcApi.rise(2, 1, 0)
# plcApi.top_move(1, 3, wait= True)
