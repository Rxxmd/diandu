from collections import defaultdict
from Interval import interval

class Prediction:
    def __init__(self, Line, config):
        
        self.tank_table      = defaultdict(dict)
        self.hoist_table     = defaultdict(dict)
        self.tank_map_table  = defaultdict(dict)
        self.hoist_map_table = defaultdict(dict)

        self.init_hoist_talbe(Line)
        self.init_tank_table(Line)

        self.pole_move_time   = config.pole_config['pole_moving_duration']
        self.pole_stop_time   = config.pole_config['pole_stop_duration']
        self.pole_start_time  = config.pole_config['pole_start_duration']
        self.pole_load_time   = config.pole_config['pole_hangon_duration']
        self.pole_unload_time = config.pole_config['pole_hangoff_duration']
        self.gear_move_time   = config.gear_config['gear_moving_duration']
    '''
        预判模块
    '''
    def init_tank_table(self, Line):
        for tank in Line.Slots.array:

            if tank not in self.tank_table:
            
                self.tank_table[tank] = {}
    
    def init_hoist_talbe(self, Line):
        for k, v in Line.Poles.dict.items():
            self.hoist_table[k] = {}

    def match_tank(self, tanks, time, temp_tt, sum_t,):

        for tank in tanks:
            for k, v in temp_tt[tank].items():
                upper = sum_t + time + self.pole_load_time + self.pole_unload_time 
                if Interval(sum_t, upper).overlaps(v):
                    return False
        return tank, time

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
    
    def constraint_table(self, product, Line):
        poles = copy.deepcopy(Line.Poles.dict)
        temp_tt = copy.deepcopy(self.tank_table)
        temp_pt = copy.deepcopy(self.hoist_table)
        temp_tt_map = copy.deepcopy(self.tank_map_table)
        temp_pt_map = copy.deepcopy(self.hoist_map_table)
        sum_t = self.time
        *process, _ = product.process
        for stage, tanks, time, _ in process:
            
            next_tank = product.process[stage + 1][1][-1]
            avai_poles = [v for k, v in poles.items() if tanks[0] in v.interval and next_tank in v.interval]
            
            res = self.match_tank(tanks, time, temp_tt, sum_t)
            if not res:
                return False
            
            slc_tank, res_t = res

            res = self.match_pole(avai_poles, slc_tank, next_tank, sum_t, res_t) 
            if not res:
                
                return False
            pole, ts, te = res

        
            if set(tanks).issubset(self.Line.Slots.stocking):    
                temp_pt[pole.name][(product.name, product.stage)] = Interval(ts, te)
                temp_pt_map[(product.name, product.stage)] = pole.name

                product.stage += 1
                sum_t += (te - ts) 
                
            elif not set(tanks).issubset(self.Line.Slots.blanking):  
                

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