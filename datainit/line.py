from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field
from datainit import database
class Product:
    def __init__(self, name, stage, craft_name, processes, position, process_start_time=0):
        self.name = name
        self.craft = craft_name
        self.position = position
        self.next_slot = position
        self.stage = stage
        self.available = True
        self.processes = processes
        self.process_start_time = process_start_time
        self.pole = None
        self.mid = False
    
    def __repr__(self):
        return str(self.__dict__)

class Products:
    def __init__(self, crafts):
        self.crafts = crafts.dict
        self.dict = defaultdict(list)
        self.name = 0

    def add_product(self, parser, position, ProcessNumber, stage = 1, process_start_time = 0, is_stocking = True):
        # product name
        name = f'p{self.name}'
        self.name += 1
        state = list(parser.state)
        state.append(('product_at', name, f'slot{position}'))
        if not is_stocking:
            state.append(('slot_not_available', f'slot{position}'))
        parser.state = tuple(state)
        parser.objects['product'].append(name)
       
        # create product
        product = Product(name, stage, ProcessNumber, self.crafts[ProcessNumber], position, process_start_time)
        self.dict[ProcessNumber].append(product)
    
    def __repr__(self):
        return str(self.__dict__)

@dataclass
class Process:
    ''' 这是一个简单的类， 保留每一道步序的序号， 反应时间区间， 可选槽位 '''
    lower_bound: int = -1
    upper_bound: int = -1
    tanks: list = field(default_factory = list)
    wait: int = 0
    drip: int = 0
    basin: bool = False
    up_num: int = 0
    down_num: int = 0

class Craft: 
    '''
        这个类用来从数据库中读取工艺
    '''
    def __init__(self, table_name, db_con):
        self.dict = {}
        data = db_con.read_table(table_name)
        self.process = self.parse_process(data)

    def parse_process(self, df):
        # 获取所有的流程号
        df['ProcessNumber'] = df['ProcessNumber'].astype(int)
        all_process_numbers = set(df['ProcessNumber'])
        for process_number in all_process_numbers:
            # 过滤出某个工艺的所有流程信息
            processes = df[df.ProcessNumber == process_number]
            # 转换数据类型
     
            processes['StepNumber'] = processes['StepNumber'].astype(int)
            processes['TankNumber'] = processes['TankNumber'].astype(int)
            processes['DipTime'] = processes['DipTime'].astype(int)
            processes['UpCount'] = processes['UpCount'].astype(int)
            processes['DripTray'] = processes['DripTray'].astype(int)
            processes['WaitTime'] = processes['WaitTime'].astype(int)
            processes['DipTimeUpLimit'] = processes['DipTimeUpLimit'].astype(int)
            processes['PushWaterCount'] = processes['PushWaterCount'].astype(int)
            processes['DripWaterTime']  = processes['DripWaterTime'].astype(int)


            # 按照步序把流程分组
            craft = OrderedDict()
            for step, group in processes.groupby('StepNumber'):
                tanks       = group['TankNumber'].tolist()
                wait        = group['WaitTime'].iloc[0]
                up_num      = group['UpCount'].iloc[0]
                drip        = group['DripWaterTime'].iloc[0]
                down_num    = group['PushWaterCount'].iloc[0]
                lower_bound = group["DipTime"].iloc[0]
                upper_bound = group['DipTimeUpLimit'].iloc[0]
                basin = group['DripTray'].iloc[0]

                process = Process(lower_bound, upper_bound, tanks, wait, drip, basin, up_num, down_num)
                craft[step] = process
            # 把流程保存在Craft类中的dict            
            self.dict[process_number] = craft

    def __repr__(self):
        return str(self.__dict__)

class Pole:
    def __init__(self, name, position, interval, order_num):
        self.name = name
        self.order_num = order_num
        self.position = position
        self.interval = interval
        self.mid = False
        self.product = None
        self.select = False
        self.stopping = True
        self.stop_time = -1
        self.up_down = 1

    def __repr__(self):
        return str(self.__dict__)

class Poles:
    def __init__(self, config):
        self.dict = {}

        self.parse_poles(config)
    
    def parse_poles(self, config):
        poles = config['poles']
        pole_region = config['pole_region']
        pole_position = config['pole_position']
        pole_order_num = config['pole_order_num']

        for name, region, position, order_num in zip(poles, pole_region, pole_position, pole_order_num):
            name = 'pole' + str(name)
            pole = Pole(name, position, region, order_num)
            self.dict[name] = pole
    
    def update_pole_position(self, state):
        for s in state:
            if 'pole_position' in s:
                pole = s[1]
                if pole in self.dict:
                    position = int(s[2][4:])
                    self.dict[pole].position = position
    
    def __repr__(self):
        return str(self.__dict__)


@dataclass
class Gear:
    name: str
    product: str
    position: int
    region: tuple
    begin: int
    end: int

class Gears:
    def __init__(self, config):
        self.dict = {}
        self.parse_gears(config)
    
    def parse_gears(self, config):
        gears = config['gears']
        gears_region = config['gears_region']
        gears_position = config['gears_position'] 

        for name, positon, region in zip(gears, gears_position, gears_region):
            name = 'gear' + str(name)
            begin = region[0]
            end = region[1]
            product = None
            gear = Gear(name, product, positon, region, begin, end)
            
            self.dict[name] = gear           
   
    def update_gear_position(self, state):  
        for s in state:
            if 'pole_position' in s:
                gear = s[1]
                if gear in self.dict:
                    position = int(s[2][4:])
                    self.dict[gear].position = position
   
    def __repr__(self):
        return str(self.__dict__)

class Slots:
    def __init__(self, config):
        self.array = list(config['slots'])
        self.empty = list(config['empty_slot'])
        self.blanking = config['blanking_slot']
        self.stocking = config['stocking_slot']
        self.disable = config['disable_slot']
        self.gear_slot = config['gears_begin_slot'] + config['gears_end_slot']

    #### 真实生产线需要修改
    def set_blanking_slot_empty(self):
        for slot in self.blanking:
            if slot not in self.empty:
                self.empty.append(slot)   

    # def corresponding_slot(self, pole):
        # region = pole.interval
        # if pole.position == region.lower_bound and region.lower_bound in self.gears_begin:
        #     return region.upper_bound
        # elif pole.position == region.upper_bound and region.upper_bound in self.gears_begin:
        #     return region.lower_bound
        # elif pole.position == region.lower_bound and region.lower_bound in self.gears_end:
        #     return region.upper_bound
        # elif pole.position == region.upper_bound and region.upper_bound in self.gears_end:
        #     return region.lower_bound

    def __repr__(self):
        return str(self.__dict__)

class Line:
    def __init__(self, config):
        db = database.Database(**config.db_config)           # 创建数据库连接
        self.Craft = Craft(config.TABLE_NAME, db)            # 读取数据库中的工艺流程
        self.Products = Products(self.Craft)                           # 用来保存在生产线中的物品， 但是还没纳入规划过程的物品
        self.Poles = Poles(config.pole_config)               # 初始化生产线中的天车
        self.Slots = Slots(config.slot_config)               # 初始化生产线中的槽位
        self.Gears = Gears(config.gear_config)               # 初始化生产线中的交换车

    def __repr__(self):
        return str(self.__dict__)







    