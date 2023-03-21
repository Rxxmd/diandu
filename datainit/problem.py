import re
import argparse
import ipdb
import pandas as pd

def gen_problem(config):
    pb = dict(**config.problem_config, **config.slot_config, **config.pole_config, **config.gear_config)
    name = f'(problem {pb["name"]})'
    domain = f'(:domain {pb["domain"]})'
    objects = gen_objects(pb)
    init = gen_init(pb)
    goal = '(:goal (and ))'
    problem = f'(define {name} {domain} {objects} {init} {goal})'
    
    with open(pb['problem_path'], 'w') as f:
        print(problem, file=f)

def gen_objects(pb):
    s = '(:objects\n'
    for slot in pb["slots"]:
        s += f'slot{slot} '
    s += '- slot\n'

    for pole in pb["poles"]:
        s += f'pole{pole} '
    for gear in pb["gears"]:
        s += f'gear{gear} '
    s += '- pole\n'
    s += 'p100000 - product\n'
    s += ')'
    return s

def gen_init(pb):
    border = ''
    stocking = ''
    blanking = ''
    duration = ''
    region = gen_pole_region(pb)
    connection = gen_slot_connection(pb)

    for bs in pb["border_slot"]:
        border += f'(border_slot slot{bs})\n'
    
    for ss in pb["stocking_slot"]:
        stocking += f'(stocking_slot slot{ss})\n'

    for bs in pb["blanking_slot"]:
        blanking += f'(blanking_slot slot{bs})\n'

    duration += f'(= (pole_moving_duration_each_slot) {pb["pole_moving_duration"]})\n'
    duration += f'(= (pole_hangon_duration) {pb["pole_hangon_duration"]})\n'
    duration += f'(= (pole_hangoff_duration) {pb["pole_hangoff_duration"]})\n'
    duration += f'(= (pole_start_duration) {pb["pole_start_duration"]})\n'
    duration += f'(= (gear_moving_duration) {pb["gear_moving_duration"]})\n'
    
    init = f'(:init\n {border} {stocking} {blanking} {connection} {duration} {region} )'
    
    return init

def gen_slot_connection(pb):
    forward_connection = ''
    inverse_connection = ''
    for i, slot in enumerate(pb["slots"]):
        if pb["is_cycle"] and i == len(pb["slots"]) - 1:
            first = pb["slots"][0]
            forward_connection += f'(forward_slot_connection slot{slot} slot{first})\n'
            inverse_connection += f'(inverse_slot_connection slot{first} slot{slot})\n'
        elif i < len(pb["slots"]) - 1:
            next = pb["slots"][i + 1]
            forward_connection += f'(forward_slot_connection slot{slot} slot{next})\n'
            inverse_connection += f'(inverse_slot_connection slot{next} slot{slot})\n'
    return forward_connection + inverse_connection

def gen_pole_region(pb):
    region = ''
    available = ''
    empty = ''
    shp = ''
    stop = ''
    position = ''
    exchange = ''
    for pole, slot, rg in zip(pb["poles"], pb["pole_position"], pb["pole_region"]):
        available += f'(pole_available pole{pole})\n'
        empty += f'(pole_empty pole{pole})\n'
        stop += f'(pole_stop_moving pole{pole})\n'
       
        for pos in rg:
            region += f'(pole_region pole{pole} slot{pos})\n'
    
        position += f'(pole_position pole{pole} slot{slot})\n'
        shp += f'(slot_have_pole slot{slot})\n'
    
    for gear, slot, rg in zip(pb["gears"], pb["gears_position"], pb["gears_region"]):
        available += f'(pole_available gear{gear})\n'
        empty += f'(pole_empty gear{gear})\n'
        exchange += f'(exchanging_connection slot{rg[0]}  slot{rg[1]})\n'
        exchange += f'(exchanging_connection slot{rg[1]}  slot{rg[0]})\n'
        for pos in rg:
            region += f'(pole_region gear{gear} slot{pos})\n'
            exchange += f'(exchanging_slot slot{pos})\n'
    
        position += f'(pole_position gear{gear} slot{slot})\n'
        # shp += f'(slot_have_pole slot{slot})\n'

    return region + available + empty + shp + stop + position + exchange



