from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field
class Product:
    def __init__(self, name, craft_name, processes, position):
        self.name = name
        self.craft = craft_name
        self.position = position
        self.next_slot = position
        self.stage = 0
        self.available = True
        self.processes = processes
        self.process_start_time = 0
        self.pole = None
        self.mid = False
    
    def __repr__(self):
        return str(self.__dict__)


class Products:
    def __init__(self) -> None:
        self.craft = {}
        self.dict = defaultdict(list)
        self.names = []

    def add_product(self, parser, position, table_name, db_con):
        craft = Craft(table_name, db_con)

        if craft.name not in self.craft:
            self.craft[craft.name] = craft.process
        # product name
        for i in range(1000):
            if f'p{i}' not in self.names:
                name = f'p{i}'
                self.names.append(name)
                state = list(parser.state)
                state.append(('product_at', name, f'slot{position}'))
                parser.state = tuple(state)
                
                parser.objects['product'].append(name)
                # create product
                product = Product(name, craft.name, craft.process, position)
                self.dict[craft.name].append(product)
                break
    
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
    up_num: int = 0
    down_num: int = 0


class Craft: 
    '''
        这个类用来从数据库中读取工艺
    '''
    def __init__(self, table_name, db_con):
        self.name = table_name
        data = db_con.read_table(table_name)
        self.process = self.parse_process(data)

    def parse_process(self, df):
        LB = []
        UB = []
        processes = OrderedDict()
        
        for stage, group in df.groupby("Stage"):
            tanks = group["Tank"].tolist()
            lower_bound = group["LB"].iloc[0]
            upper_bound = group["UB"].iloc[0]
            wait = 0
            drip = 0
            up_num = 0
            down_num = 0
            process = Process(lower_bound, upper_bound, tanks, wait, drip, up_num, down_num)
            processes[stage] = process
        return processes

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
                position = int(s[2][4:])
                self.dict[pole].position = position
    
    def __repr__(self):
        return str(self.__dict__)


class Gear:
    def __init__(self, name, position, region) -> None:
        self.name = name,
        self.product = None
        self.position = position,
        self.region = region,
        self.begin = region[0]
        self.end = region[1]

    def __repr__(self):
        return str(self.__dict__)


class Gears:
    def __init__(self, config):
        self.dict = {}
    
    def parse_gears(self, config):
        gears = config['gears']
        gears_region = config['gears_region']
        gears_position = config['gears_position'] 

        for name, positon, region in zip(gears, gears_position, gears_region):
            name = 'gear' + str(name)
            gear = Gear(name, positon, region)
            self.dict[name] = gear           

    def __repr__(self):
        return str(self.__dict__)


class Slots:
    def __init__(self, config):
        
        self.array = list(config['slots'])
        self.empty = list(config['empty_slot'])
        self.blanking = config['blanking_slot']
        self.stocking = config['stocking_slot']
        self.disable = config['disable_slot']

    ###### 真实生产线需要修改
    def set_blanking_slot_empty(self):
        for slot in self.blanking:
            if slot not in self.empty:
                self.empty.append(slot)   

    def corresponding_slot(self, pole):
        region = pole.interval
        if pole.position == region.lower_bound and region.lower_bound in self.gears_begin:
            return region.upper_bound
        elif pole.position == region.upper_bound and region.upper_bound in self.gears_begin:
            return region.lower_bound
        elif pole.position == region.lower_bound and region.lower_bound in self.gears_end:
            return region.upper_bound
        elif pole.position == region.upper_bound and region.upper_bound in self.gears_end:
            return region.lower_bound

    def __repr__(self):
        return str(self.__dict__)


class Line:
    def __init__(self, config):
        self.Products = Products()
        self.Poles = Poles(config.pole_config)
        self.Slots = Slots(config.slot_config)
        self.Gears = Gears(config.gear_config)

    def __repr__(self):
        return str(self.__dict__)








    