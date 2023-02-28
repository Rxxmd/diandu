from collections import defaultdict
import os
import clr

# 定位DLL的位置
cur_path  = os.path.abspath(__file__)

root_path = cur_path[:cur_path.find('Electroplating') + len('Electroplating')]

dll_path = os.path.join(root_path, 'HIT', 'datainit', 'OmronPlcEthernet.dll')


# 导入Plc Dll 库
clr.FindAssembly(dll_path)
dll = clr.AddReference(dll_path)
from OmronPlcEthernet import *

RISE_CODE        = 0x1000
DOWN_CODE        = 0x3000
BELOW_MOVE_CODE  = 0x0000
TOP_MOVE_CODE    = 0x2000
WAIT_MIN_CODE    = 0x4800
WAIT_SEC_CODE    = 0x4000
BASIN_OPEN_CODE  = 0x6001
BASIN_CLOSE_CODE = 0x6002
EXSIGNAL_CODE    = 0xB000
FINAL_CODE       = 0xF000

HOIST_AUTO_ADDR   = 95936
HOIST_POS_ADDR    = 95976
INIT_WRITE_ADDR   = 13800
HOIST_COMD_ADDR   = 15400
TANK_SELECT_ADDR  = 95536
HOIST_UD_ADDR     = 95896

MAX_TANK  = 20
MAX_WORD  = 2
MAX_HOIST = 30

_PLC = PLC("192.168.1.2", 9600, 0, 2, 0, 0, 1, 0) # 创建Plc对象
        
'''
    Write API
'''

# def record_time(func): 
#     '''
#         记录物品的浸泡时间
#     '''
#     def wrapper(*args, **kwargs):
#         func(*args, **kwargs)
#         pole_num = args[0]
#         if not record[pole_num] and func.__name__ == 'rise':
#             return 
#         elif func.__name__ == 'down':
#             record[pole_num].append(time.time())
#         elif func.__name__ == 'rise':
#             record[pole_num][-1] = time.time() - record[pole_num][-1] - 10
#         return 
#     return wrapper

def check(func):
    '''
        每次往 plc 写入数据之前都要进行check, 读取 HOIST_COMD_ADDR + pole_num 的地址是否为1
    '''
    def wrapper(*args, **kwargs):
        
        if kwargs and not kwargs['wait']:     # 如果传入的参数不需要 wait 那么就直接执行func
            return func(*args, **kwargs)   

        pole_num = args[0]
        
        while True:                                 
            
            data = _PLC.Read(HOIST_COMD_ADDR + pole_num, 1, 0)  # data[1] 表示读取到的数据的个数，data[0] 是读取的数据
            if data[1] != 0 and (data[0][0] == 1 or data[0][0] == 3):        # 如果读到的data[0][0] 为1 表示前面的动作已经执行完成， 可以写入新的指令
                break

        return func(*args, **kwargs)
    
    return wrapper

@check
def __write(pole_num, data, wait = True):
    '''
        往内存写入数据
        参数：
            pole_num: 天车的编号
            data: 要写入的数据
    '''
    address = INIT_WRITE_ADDR + 50 * pole_num

    _PLC.Write(address, data)

    _PLC.Write(HOIST_COMD_ADDR + pole_num, [2])

def below_move(pole_num, slot_num, wait = False):
    '''
        下限移动
        参数：
            pole_num: 天车的编号
            slot_num: 目标槽位
            wait: 默认为False, 是否需要等待 15400 + pole_num 的地址送 1。
                    只有启动移动的时候才需要wait = True
    '''
    ### 判断是否在下限
    
    slot_num = BELOW_MOVE_CODE + int(str(slot_num), 16)
    __write(pole_num, [slot_num], wait=wait)
    # while True:
    #     data = get_hoist_up_down([pole_num])
    #     if data[pole_num] == 1:
    #         __write(pole_num, [slot_num], wait=wait)
    #         return

def top_move(pole_num, slot_num, wait = False):
    '''
        上限移动
        参数：
            pole_num: 天车的编号
            slot_num: 目标槽位
            wait: 默认为False, 是否需要等待 15400 + pole_num 的地址送一。
                    只有启动移动的时候才需要wait = True
    '''
    ### 判断天车是否在上限
    data = get_hoist_up_down([pole_num])
    
    slot_num = TOP_MOVE_CODE + int(str(slot_num), 16)
    __write(pole_num, [slot_num], wait=wait)
    # while True:
    #     data = get_hoist_up_down([pole_num])
    #     if data[pole_num] == 3:
    #         __write(pole_num, [slot_num], wait=wait)
    #     return 

def rise(pole_num, N, M):

    '''
        天车上升
        参数：
            pole_num : 天车的编号
            N : 需要上升的次数， 1 表示一次
            M : 0 单飞巴， 1双升降第一支飞巴, 2双升降第二支飞巴 , 3双升降飞巴
    '''

    N = int(f'{N - 1}00', 16)
    data = RISE_CODE + N + M
    __write(pole_num, [data])
    # 判断天车是否在下限
    # while True:
    #     up_down = get_hoist_up_down([pole_num])
    #     import ipdb
    #     ipdb.set_trace()
    #     if up_down[pole_num] == 1:
    #         __write(pole_num, [data])
    #         return

def down(pole_num, N, M):
    '''
        天车下降
        参数：
            pole_num : 天车的编号
            N : 需要下降的次数， 1 表示一次
            M : 0 单飞巴， 1双升降第一支飞巴, 2双升降第二支飞巴 , 3双升降飞巴
    '''
    N = int(f'{N - 1}00', 16)
    data = DOWN_CODE + N  + M
    __write(pole_num, [data])
    # 判断天车是否在上限
    # while True:
    #     up_down = get_hoist_up_down([pole_num])
    #     if up_down[pole_num] == 3:
    #         __write(pole_num, [data])
    #         return

def wait(pole_num, time):
    '''
        需要写一个定时任务
        等待/滴水
        pole_num : 天车的编号
        time : 需要等待的时间， 单位 秒
    '''
    minute = time // 60
    second = time % 60

    minute = int(f'{minute}', 16)
    second = int(f'{second}', 16)

    data = [WAIT_SEC_CODE + second]

    __write(pole_num, data)

def wait_external_signal(pole_num, slot_num):
    '''
        等待外部信号， 等待slot_num 的实际处理时间 >= 设定的时间
        参数:
            pole_num: 天车的编号
            slot_num: 目标槽位
    '''
    first_num = slot_num % 16
    second_num = slot_num // 16

    second_num = int(f'{second_num}0', 16)
    data = EXSIGNAL_CODE + second_num + first_num
    __write(pole_num, [data])

def basin_operation(pole_num, *, operation):
    '''
        operation = 1 : open basin
        operation = 2 : close basin
    '''
    if operation == 'open':
        data = [BASIN_OPEN_CODE]
    elif operation == 'close':
        data = [BASIN_CLOSE_CODE]
    
    __write(pole_num, data)

def final_step(pole_num):
    '''
        传递结束信号， 暂时不会用到
    '''
    data = [FINAL_CODE]
    __write(pole_num, data)

'''
    READ API
'''

def get_tank_status(tanks):
    '''
        查看可以使用的槽位 1 表示可用， 0 表示不可用（封槽）
        参数:
            tanks: list 需要查询的槽位
    '''
    return __read(tanks, TANK_SELECT_ADDR, MAX_TANK, True)
    
def get_hoist_up_down(hoists):
    '''
        查看天车的升降位置， 1下限/2中间/3上限
        参数：
            hoist: 需要查询的天车的数据
        返回：
            1 下限， 2 中间， 3 上限
            返回一个hoists为key的dict
    '''
    return __read(hoists, HOIST_UD_ADDR, MAX_HOIST, False)

def get_hoist_auto(hoists):
    '''
        查询天车是否为自动模式 1自动/0手动
        参数：
            hoist: 需要查询的天车的数据
        返回：
            返回一个hoists为key的dict
    '''
    data = __read(hoists, HOIST_AUTO_ADDR, MAX_WORD, True)
    if all(data.values()):
        return True
    else:
        no_auto_hoists = [k for k, v in data.items() if v == 0]
        print(f'天车 {no_auto_hoists} 没有设置为自动模式')
        return False  

def get_hoist_position(hoists):
    '''
        查询天车当前的位置
        参数：
            hoist: 需要查询的天车的数据
        返回：
            返回一个hoists为key的dict
        
    '''
    return __read(hoists, HOIST_POS_ADDR, MAX_HOIST, False)

def __read(input, address, maxnum, is_bit):
    '''
        读_PLC数据,调用Plc.Read接口
        返回一个一input为key的dict
    '''
    data = _PLC.Read(address, maxnum, 0)
    return convert_data(data, input, is_bit)

def convert_data(data, input, is_bit):
    '''
        参数:
            data: 读取到的数据
            input: 需要查询的数据
            is_bit: 表示读取的数据是否以16个一组存在一个word里
        返回一个一input为key的dict
    '''
    res = {}
    if is_bit:
        for it in input:
            index = it // 16
            offset = it % 16
            status = (data[0][index] >> offset) & 1
            res[it] = status
    else:
        for it in input:
            res[it] = data[0][it]
    return res


# for i in range(1, 4):
#     position = hoist_position([i])
#     position = position[i]
#     below_move(i, position + 1, wait=True)
#     for j in range(2, 4):
#         below_move(i, position + j)
#     rise(i, 1, 0)

#     position = hoist_position([i])
#     position = position[i]
#     top_move(i, position - 1, wait=True)
    
#     top_move(i, position - 2)
#     down(i, 1, 0)




# init = time.time()

# up_down = {'pole1': 1, 'pole2': 1, 'pole3': 1}
# def do_hang(line):
#     start, name, pole, *_ = line.split()
#     start = float(start)
#     while time.time() - init < start and ('start' in name or 'hang' in name):
#         pass

#     pole_num = int("".join(re.findall(r"\d+", pole)))

#     if 'hangoff' in line:
#         up_down[pole] = 1
#         down(pole_num, 0, 0)
#     elif 'hangup' in line:
#         up_down[pole] = 2
#         rise(pole_num, 0, 0)

# def do_move(line):
#     start, name, pole, _, des_slot, *_ = line.split()
#     pole_num = int("".join(re.findall(r"\d+", pole)))
#     slot_num = int("".join(re.findall(r"\d+", des_slot)))

#     start = float(start)
#     while time.time() - init < start and ('start' in name or 'hang' in name):
#         pass

#     if up_down[pole] == 1:
#         if 'start' in name:
#             below_move(pole_num, slot_num, wait=True)
#         else:   
#             below_move(pole_num, slot_num)
#     else:
#         if 'start' in name:
#             top_move(pole_num, slot_num, wait=True)
#         else:
#             top_move(pole_num, slot_num)

# with open('../data/211/211.txt', 'r') as f:
#     for index, line in enumerate(f):
    
#         line = line.replace('(', '').replace(')', '')
#         print(line)
#         if 'hang' in line:
#             do_hang(line)
#         elif 'move' in line:
#             do_move(line)





# df = pd.DataFrame(record)
# print(df)
# df.to_excel(sheet_name='../data/211/record.xls')

