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
import time
from datainit import plcApi
from plan import Planning
import _config
from output import *
# import subprocess
# def is_all_hoist_below(data):
#     if all([v == 1 for v in data.values()]):
#         return True
    
#     res = [k for k, v in data.items() if v != 1]
#     print(f'天车 {res} 没有在下限')
#     return False

# def before_start(hoists, tanks):
    
#     while True: # 检查天车是否自动 和 天车都在下限
#         up_down_hoists = PLC.get_hoist_up_down(hoists)
#         if PLC.get_hoist_auto(hoists) and is_all_hoist_below(up_down_hoists):
#             break    
#         time.sleep(1)
#     hoists_position = PLC.get_hoist_position(hoists)
#     tank_status = PLC.get_tank_status(tanks)

#     return hoists_position, tank_status
# before_start([],[])

# try:
#     plan = Planning(_config)
#     plan.execute()

# finally:
#     subprocess.run(f'rm *.pddl output output.sas plan.validation *sas_plan* ', shell=True)
    
def output(queue):
    out = Output()
    out.excute(queue)

def planing(queue):
    plan = Planning(_config)
    plan.execute(queue)


from multiprocessing import Process, Queue
if __name__ == '__main__': 
    queue = Queue()
    
    p1 = Process(target = planing, args=(queue, ))
    p2 = Output(queue)

    p1.start()
    p2.start()
    # plan = Planning(_config)
    # plan.execute()
# plcApi.below_move(1, 2)
# plcApi.rise(1, 1, 0)
# plcApi.rise(2, 1, 0)
# plcApi.top_move(1, 3, wait= True)
