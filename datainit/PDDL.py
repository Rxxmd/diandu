from ipaddress import ip_address
import ipdb
import re
import itertools
from collections import defaultdict
import sys
from interval import Interval

class Action:

    # -----------------------------------------------
    # Initialize
    # -----------------------------------------------

    def __init__(self, name, parameters, positive_preconditions, negative_preconditions,numeric_preconditions,
                 add_effects, del_effects, numeric_effects, duration,extensions=None):
        def frozenset_of_tuples(data):
            return frozenset([tuple(t) for t in data])

        # print(positive_preconditions)
        self.name = name
        self.parameters = parameters
        self.positive_preconditions = frozenset_of_tuples(
            positive_preconditions)
        self.negative_preconditions = frozenset_of_tuples(
            negative_preconditions)
        self.numeric_preconditions = numeric_preconditions
        
        self.add_effects = frozenset_of_tuples(add_effects)
        self.del_effects = frozenset_of_tuples(del_effects)
        self.numeric_effects = numeric_effects
        self.duration = duration

    # def __init__(self, name, parameters, positive_preconditions, negative_preconditions,
    #              add_effects, del_effects, extensions=None):
    #     def frozenset_of_tuples(data):
    #         return frozenset([tuple(t) for t in data])
    #     self.name = name
    #     self.parameters = parameters
    #     self.positive_preconditions = frozenset_of_tuples(
    #         positive_preconditions)
    #     self.negative_preconditions = frozenset_of_tuples(
    #         negative_preconditions)
    #     self.add_effects = frozenset_of_tuples(add_effects)
    #     self.del_effects = frozenset_of_tuples(del_effects)

    # -----------------------------------------------
    # to String
    # -----------------------------------------------

    def __str__(self):
        return 'action: ' + self.name + \
            '\n  parameters: ' + str(self.parameters) + \
            '\n  positive_preconditions: ' + str([list(i) for i in self.positive_preconditions]) + \
            '\n  negative_preconditions: ' + str([list(i) for i in self.negative_preconditions]) + \
            '\n  add_effects: ' + str([list(i) for i in self.add_effects]) + \
            '\n  del_effects: ' + str([list(i)
                                       for i in self.del_effects]) + '\n'

    # -----------------------------------------------
    # Equality
    # -----------------------------------------------

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    # -----------------------------------------------
    # Groundify
    # -----------------------------------------------

    def groundify(self, objects, types):
        if not self.parameters:
            yield self
            return
        type_map = []
        variables = []
        for var, type in self.parameters:
            type_stack = [type]
            items = []
            while type_stack:
                t = type_stack.pop()
                if t in objects:
                    items += objects[t]
                elif t in types:
                    type_stack += types[t]
                else:
                    raise Exception('Unrecognized type ' + t)
            type_map.append(items)
            variables.append(var)
        
        for assignment in itertools.product(*type_map):
            record= True
            if 'move' in self.name.lower():
                # print(self.name)
                for a in range(2,len(assignment)):
                    if abs(int(assignment[a].replace('slot','') ) - int(assignment[a-1].replace('slot','') )) != 1:
                        record = False
                        break
            if record == True:
                positive_preconditions = self.replace(
                    self.positive_preconditions, variables, assignment)
                negative_preconditions = self.replace(
                    self.negative_preconditions, variables, assignment)
                add_effects = self.replace(self.add_effects, variables, assignment)
                del_effects = self.replace(self.del_effects, variables, assignment)
                numeric_precondition = []
                for pre in self.numeric_preconditions:
                    replace_sen = []
                    for sen in pre:
                        if '?' in ''.join(x for x in sen):
                            replace_sen.append(self.replace([sen], variables, assignment)[0])
                        else:
                            replace_sen.append(sen)
                    numeric_precondition.append(replace_sen)
                
                numeric_effects = []
                for pre in self.numeric_effects:
                    replace_sen = []
                    for sen in pre:
                        if '?' in ''.join(x for x in sen):
                            replace_sen.append(self.replace([sen], variables, assignment)[0])
                        else:
                            replace_sen.append(sen)
                    numeric_effects.append(replace_sen)

                duration = []
                for pre in self.duration:
                    replace_sen = []
                    for sen in pre:
                        if '?' in ''.join(x for x in sen) and '?duration' not in ''.join(x for x in sen):
                            replace_sen.append(self.replace([sen], variables, assignment)[0])
                        else:
                            replace_sen.append(sen)
                    duration.append(replace_sen)
                yield Action(self.name, assignment, positive_preconditions,
                            negative_preconditions, numeric_precondition,add_effects, del_effects,numeric_effects,duration)
                
   
    # def get_numeric(self, state):

    # -----------------------------------------------
    # Replace
    # -----------------------------------------------

    def replace(self, group, variables, assignment):
        g = []
        
        for pred in group:
            pred = list(pred)
            iv = 0
            for v in variables:
                while v in pred:
                    pred[pred.index(v)] = assignment[iv]
                iv += 1
            g.append(pred)
        return g

    def to_string(self):
        def combine(s, objs):
            return s + " " + " ".join(objs)
        string_dict = {}
        string_dict['fullname'] = combine(self.name, self.parameters)
        string_dict['preconditions'] = [
            combine(i[0], list(i[1:])) for i in self.positive_preconditions]
        string_dict['preconditions'] += [
            combine(i[0], list(i[1:])) for i in self.negative_preconditions]
        string_dict['add_effects'] = [
            combine(i[0], list(i[1:])) for i in self.add_effects]
        string_dict['del_effects'] = [
            combine(i[0], list(i[1:])) for i in self.del_effects]
        return string_dict
    
    def to_relaxed(self):
        action = self
        action.negative_preconditions = []
        action.del_effects = []
        return action

class PDDL_Parser:

    SUPPORTED_REQUIREMENTS = [':strips', ':negative-preconditions', ':typing']

    # -----------------------------------------------
    # Tokens
    # -----------------------------------------------

    def scan_tokens(self, filename):
        with open(filename, 'r') as f:
            # Remove single line comments
            str = re.sub(r';.*$', '', f.read(), flags=re.MULTILINE).lower()
        # Tokenize
        stack = []
        _list = []
        for t in re.findall(r'[()]|[^\s()]+', str):
            if t == '(':
                stack.append(_list)
                _list = []
            elif t == ')':
                if stack:
                    tmp = _list
                    _list = stack.pop()
                    _list.append(tmp)
                else:
                    raise Exception('Missing open parentheses')
            else:
                _list.append(t)
        if stack:
            raise Exception('Missing close parentheses')
        if len(_list) != 1:
            raise Exception('Malformed expression')
        return _list[0]

    # -----------------------------------------------
    # Parse domain
    # -----------------------------------------------

    def parse_domain(self, domain_filename):
        tokens = self.scan_tokens(domain_filename)
        if type(tokens) is list and tokens.pop(0) == 'define':
            self.domain_name = 'unknown'
            self.requirements = []
            self.types = {}
            self.objects = {}
            self.actions = []
            self.discrete_actions = []
            self.durative_actions = []
            self.predicates = {}
            self.functions = {}
            while tokens:
                group = tokens.pop(0)
                t = group.pop(0)
                if t == 'domain':
                    self.domain_name = group[0]
                elif t == ':requirements':
                    # for req in group:
                    #     if req not in self.SUPPORTED_REQUIREMENTS:
                    #         raise Exception('Requirement ' +
                    #                         req + ' not supported')
                    self.requirements = group
                elif t == ':constants':
                    self.parse_objects(group, t)
                elif t == ':predicates':
                    self.parse_predicates(group)
                elif t == ':types':
                    self.parse_types(group)
                elif t == ':action':
                    self.parse_action(group)
                elif t==':durative-action':
                    self.parse_durative_action(group)
                elif t==':functions':
                    self.parse_functions(group)
                else:
                    self.parse_domain_extended(t, group)
        else:
            raise Exception('File ' + domain_filename +
                            ' does not match domain pattern')

    def parse_domain_extended(self, t, group):
        print(str(t) + ' is not recognized in domain')

    # -----------------------------------------------
    # Parse hierarchy
    # -----------------------------------------------

    def parse_hierarchy(self, group, structure, name, redefine):
        _list = []
        while group:
            if redefine and group[0] in structure:
                raise Exception('Redefined supertype of ' + group[0])
            elif group[0] == '-':
                if not _list:
                    raise Exception('Unexpected hyphen in ' + name)
                group.pop(0)
                _type = group.pop(0)
                if _type not in structure:
                    structure[_type] = []
                structure[_type] += _list
                _list = []
            else:
                _list.append(group.pop(0))
        if _list:
            if 'object' not in structure:
                structure['object'] = []
            structure['object'] += _list

    # -----------------------------------------------
    # Parse objects
    # -----------------------------------------------

    def parse_objects(self, group, name):
        self.parse_hierarchy(group, self.objects, name, False)

    # -----------------------------------------------
    # Parse types
    # -----------------------------------------------

    def parse_types(self, group):
        self.parse_hierarchy(group, self.types, 'types', True)

    # -----------------------------------------------
    # Parse predicates
    # -----------------------------------------------

    def parse_predicates(self, group):
        for pred in group:
            predicate_name = pred.pop(0)
            if predicate_name in self.predicates:
                raise Exception('Predicate ' + predicate_name + ' redefined')
            arguments = {}
            untyped_variables = []
            while pred:
                t = pred.pop(0)
                if t == '-':
                    if not untyped_variables:
                        raise Exception('Unexpected hyphen in predicates')
                    type = pred.pop(0)
                    while untyped_variables:
                        arguments[untyped_variables.pop(0)] = type
                else:
                    untyped_variables.append(t)
            while untyped_variables:
                arguments[untyped_variables.pop(0)] = 'object'
            self.predicates[predicate_name] = arguments
            
    def parse_functions(self, group):
        for func in group:
            predicate_name = func.pop(0)
            if predicate_name in self.predicates:
                raise Exception('Functions ' + predicate_name + ' redefined')
            arguments = {}
            untyped_variables = []
            while func:
                t = func.pop(0)
                if t == '-':
                    if not untyped_variables:
                        raise Exception('Unexpected hyphen in predicates')
                    type = func.pop(0)
                    while untyped_variables:
                        arguments[untyped_variables.pop(0)] = type
                else:
                    untyped_variables.append(t)
            while untyped_variables:
                arguments[untyped_variables.pop(0)] = 'object'
            self.functions[predicate_name] = arguments

    # -----------------------------------------------
    # Parse action
    # -----------------------------------------------

    def parse_action(self, group):
        name = group.pop(0)
        if not type(name) is str:
            raise Exception('Action without name definition')
        for act in self.actions:
            if act.name == name:
                raise Exception('Action ' + name + ' redefined')
        parameters = []
        positive_preconditions = []
        negative_preconditions = []
        numeric_preconditions = []
        add_effects = []
        del_effects = []
        numeric_effects = []
        extensions = None
        while group:
            t = group.pop(0)
            if t == ':parameters':
                if not type(group) is list:
                    raise Exception('Error with ' + name + ' parameters')
                parameters = []
                untyped_parameters = []
                p = group.pop(0)
                while p:
                    t = p.pop(0)
                    if t == '-':
                        if not untyped_parameters:
                            raise Exception(
                                'Unexpected hyphen in ' + name + ' parameters')
                        ptype = p.pop(0)
                        while untyped_parameters:
                            parameters.append(
                                [untyped_parameters.pop(0), ptype])
                    else:
                        untyped_parameters.append(t)
                while untyped_parameters:
                    parameters.append([untyped_parameters.pop(0), 'object'])
            elif t == ':precondition':
                self.split_predicates(group.pop(
                    0), positive_preconditions, negative_preconditions,numeric_preconditions, name, ' preconditions')
            elif t == ':effect':
                self.split_predicates(
                    group.pop(0), add_effects, del_effects,numeric_effects,name, ' effects')
            else:
                extensions = self.parse_action_extended(t, group)
        self.actions.append(Action(name, parameters, positive_preconditions,
                                   negative_preconditions,numeric_preconditions, add_effects, del_effects, numeric_effects  ,[],extensions))
        self.discrete_actions.append(Action(name, parameters, positive_preconditions,
                                   negative_preconditions,numeric_preconditions, add_effects, del_effects, numeric_effects  ,[],extensions))
    # -----------------------------------------------
    # Parse durative action
    # -----------------------------------------------

    def parse_durative_action(self, group):
        name = group.pop(0)
        if not type(name) is str:
            raise Exception('Action without name definition')
        for act in self.actions:
            if act.name == name:
                raise Exception('Action ' + name + ' redefined')
        parameters = []
        positive_preconditions = []
        negative_preconditions = []
        numeric_preconditions = []
        add_effects = []
        del_effects = []
        numeric_effects = []
        duration = []
        extensions = None
        while group:
            t = group.pop(0)
            if t == ':parameters':
                if not type(group) is list:
                    raise Exception('Error with ' + name + ' parameters')
                parameters = []
                untyped_parameters = []
                p = group.pop(0)
                while p:
                    t = p.pop(0)
                    if t == '-':
                        if not untyped_parameters:
                            raise Exception(
                                'Unexpected hyphen in ' + name + ' parameters')
                        ptype = p.pop(0)
                        while untyped_parameters:
                            parameters.append(
                                [untyped_parameters.pop(0), ptype])
                    else:
                        untyped_parameters.append(t)
                while untyped_parameters:
                    parameters.append([untyped_parameters.pop(0), 'object'])
            elif t == ':condition':
                self.split_durative_predicates(group.pop(
                    0), positive_preconditions, negative_preconditions,numeric_preconditions, name, ' preconditions')
            elif t == ':effect':
                self.split_durative_predicates(
                    group.pop(0), add_effects, del_effects,numeric_effects,name, ' effects')
            elif t ==':duration':
                self.split_duration(group.pop(0), duration,name)
            else:
                extensions = self.parse_action_extended(t, group)
        self.actions.append(Action(name, parameters, positive_preconditions,
                                   negative_preconditions,numeric_preconditions, add_effects, del_effects, numeric_effects  ,duration,extensions))
        self.durative_actions.append(Action(name, parameters, positive_preconditions,
                                   negative_preconditions,numeric_preconditions, add_effects, del_effects, numeric_effects  ,duration,extensions))

    def parse_action_extended(self, t, group):
        print(str(t) + ' is not recognized in action')

    # -----------------------------------------------
    # Parse problem
    # -----------------------------------------------

    def split_proposition_variables(self,group):
        initial_propositions = []
        initial_variables = []

        for g in group:
            if '=' not in g[0]:
                initial_propositions.append(g)
            else:
                initial_variables.append(g)
            
        self.initial_propositions = initial_propositions
        self.initial_variables = initial_variables

    def parse_problem(self, problem_filename):
        def frozenset_of_tuples(data):
            return frozenset([tuple(t) for t in data])
        tokens = self.scan_tokens(problem_filename)
        if type(tokens) is list and tokens.pop(0) == 'define':
            self.problem_name = 'unknown'
            self.state = frozenset()
            self.positive_goals = frozenset()
            self.negative_goals = frozenset()
            while tokens:
                group = tokens.pop(0)
                t = group.pop(0)
                if t == 'problem':
                    self.problem_name = group[0]
                elif t == ':domain':
                    if self.domain_name != group[0]:
                        raise Exception(
                            'Different domain specified in problem file')
                elif t == ':requirements':
                    pass  # Ignore requirements in problem, parse them in the domain
                elif t == ':objects':
                    self.parse_objects(group, t)
                elif t == ':init':
                    self.split_proposition_variables(group)
                    self.state = group
                    self.initial_state = group
                elif t == ':goal':
                    positive_goals = []
                    negative_goals = []
                    numeric_goals = []
                    self.split_predicates(
                        group[0], positive_goals, negative_goals,numeric_goals, '', 'goals')
                    self.positive_goals = frozenset_of_tuples(positive_goals)
                    self.negative_goals = frozenset_of_tuples(negative_goals)
                    self.numeric_goals = numeric_goals
                    self.goal_group = group[0]
                else:
                    self.parse_problem_extended(t, group)
        else:
            raise Exception('File ' + problem_filename +
                            ' does not match problem pattern')
        self.parse_stasis()

    def parse_problem_extended(self, t, group):
        print(str(t) + ' is not recognized in problem')

    # -----------------------------------------------
    # Split predicates
    # -----------------------------------------------

    def split_predicates(self, group, positive, negative,numeric, name, part):
        if not type(group) is list:
            raise Exception('Error with ' + name + part)
        if group[0] == 'and':
            group.pop(0)
        else:
            group = [group]
        for predicate in group:
            if '>' in predicate[0] or '=' in predicate[0] or '<' in predicate[0] or 'increase' in predicate[0] or 'decrease' in predicate[0]:
                numeric.append(predicate)
            elif predicate[0] == 'not':
                if len(predicate) != 2:
                    raise Exception('Unexpected not in ' + name + part)
                negative.append(predicate[-1])
            else:
                positive.append(predicate)
    
    def split_duration(self, group, duration,name):
        if not type(group) is list:
            raise Exception('Error with ' + name)
        if group[0] == 'and':
            group.pop(0)
        else:
            group = [group]
        for g in group:
            duration.append(g)

    def flat(self,nums):
        res = []
        for i in nums:
            if isinstance(i, list):
                res.extend(self.flat(i))
            else:
                res.append(i)
        return res

    def split_durative_predicates(self, group, positive, negative,numeric, name, part):
        if not type(group) is list:
            raise Exception('Error with ' + name + part)
        if group[0] == 'and':
            group.pop(0)
        else:
            group = [group]
        for predicate in group:
            # print(predicate)
            # print([predicate[0] + ' '+predicate[1]] + self.flat(predicate[2]) )
            if '>' in predicate[2][0] or '=' in predicate[2][0] or '<' in predicate[2][0] or 'increase' in predicate[2][0] or 'decrease' in predicate[2][0]:
                numeric.append([predicate[0] + ' '+predicate[1]] + predicate[2])
            elif predicate[2][0] == 'not':
                # if len(predicate) != 2:
                #     raise Exception('Unexpected not in ' + name + part)
                negative.append([predicate[0] + ' '+predicate[1]] + predicate[2][1])
            else:
                positive.append([predicate[0] + ' '+predicate[1]] + predicate[2])

    def parse_stasis(self):
        candidates = set(self.predicates.keys())
        non_static_p = set()
        for act in self.actions:
            for eff in act.add_effects:
                non_static_p.add(eff[0])
            for eff in act.del_effects:
                non_static_p.add(eff[0])
        self.static_predicates = candidates - non_static_p
        # print(self.static_predicates)

    def groundify(self):
        def get_comb(res, cur, source, pos):
            if pos == len(source):
                res.append(cur)
                return res
            for i in source[pos]:
                if i in cur:
                    continue
                get_comb(res, cur+[i], source, pos+1)
            return res

        self.g_predicates = []
        self.g_static_predicates = []
        for p in self.predicates:
            combs = [[p]]
            for _, obj in self.predicates[p].items():
                if obj in self.objects:
                    combs.append(self.objects[obj])
                else:
                    typestack = self.types[obj].copy()
                    cur = []
                    while len(typestack) > 0:
                        t = typestack.pop()
                        if t in self.objects:
                            cur += self.objects[t]
                        else:
                            typestack += self.types[t]
                    combs.append(cur.copy())
            # self.g_predicates += get_comb([], [], combs, 0)
            if p not in self.static_predicates:
                self.g_predicates += [" ".join(c)
                                      for c in get_comb([], [], combs, 0)]
            else:
                self.g_static_predicates += [" ".join(c)
                                             for c in get_comb([], [], combs, 0)]
        return self.g_predicates, self.g_static_predicates

        # def get_comb(res, cur, length, source):
        #     if len(cur) == length:
        #         res.append(cur)
        #         return res

        #     for i in source:
        #         res = get_comb(res, cur+[i], length, source)

        #     return res

        # def preprocess_comb(source, maxlen):
        #     combs = {}
        #     for i in range(maxlen):
        #         combs[i] = get_comb([], [], i, source)
        #     return combs

        # res = []
        # maxlen = 5
        # combs = preprocess_comb(objects['object'], maxlen)
        # for p in predicates:
        #     plen = len(predicates[p])
        #     if plen > maxlen:
        #         comb = get_comb([], [], plen, objects['object'])
        #     else:
        #         comb = combs[plen]
        #     res += [p+" "+" ".join(c) for c in comb]

        # return res
   
    def mutual_agg(self):
        mutual_predicates = defaultdict(list)
        # atom: at
        for t in self.objects["tile"]:
            for pre in self.g_predicates:
                if t in pre:
                    mutual_predicates[t].append(pre)
        # atom: blank
        for pre in self.g_predicates:
            if "blank" in pre:
                mutual_predicates["blank"].append(pre)

        self.mutual_predicates = dict(mutual_predicates)

    def enhance_pddl(self):
        pass
    
    # -----------------------------------------------
    # tuple(state)
    # -----------------------------------------------
    def state_to_tuple(self):
        state = self.state
        for i in range(len(state)):
            for j in range(len(state[i])):
                if(type(state[i][j]) == list):
                    state[i][j] = tuple(state[i][j])
            if type(state[i] is list):
                state[i] = tuple(state[i])
        self.state = state
    
    # -----------------------------------------------
    # init numeric to interval
    # -----------------------------------------------
    def numeric_to_interval(self):
        state = self.state
        self.interval = []
        for i in state:
            if i[0] == '=':
                self.interval.append({'key':i[1],'value':Interval(float(i[2]),float(i[2]))})

# def filter_predicates(action, status, **args):
#     param_map = {}
#     """
#         参数映射
#     """
#     for arg, parameter in zip(args, action.parameters):
#         param_map[parameter[0]] = arg
    
#     def filter_status(x):
#         return x[0] == status or x[0] == 'over all'
    
#     def map_args(x):
#         temp = []
#         for pre in x:
#             if pre in param_map.keys():
#                 temp.append(param_map[pre])
#             else:
#                 temp.append(pre)
#         return temp[1:]
    
#     """
#         过滤at start, at end 命题
#     """
#     pos_pres = list(filter(filter_status, action.positive_preconditions))
#     neg_pres = list(filter(filter_status, action.negative_preconditions))
#     add_effs = list(filter(filter_status, action.add_effects))
#     del_effs = list(filter(filter_status, action.del_effects))

#     pos_pres = frozenset(map(map_args, pos_pres))
#     neg_pres = frozenset(map(map_args, neg_pres))
#     add_effs = frozenset(map(map_args, add_effs))
#     del_effs = frozenset(map(map_args, del_effs))

#     return pos_pres, neg_pres, add_effs, del_effs

# def check(state, pos_pres, neg_pres):
#     return all(pre for pre in pos_pres if pre in state) and \
#            all(pre for pre in neg_pres if pre in state)

# def update_state(state, action, status, *args):
#     pos_pres, neg_pres, add_effs, del_effs = filter_predicates(action, status, *args)
#     assert not check, '有一些命题不在state中'
#     return tuple(tuple(set(state).difference(del_effs).union(add_effs)))

# def state2pddl(state, path):
#     pass







# -----------------------------------------------
# Main
# -----------------------------------------------
def init_parser(domain, instance=None):
    # initialize

    parser = PDDL_Parser()
    parser.parse_domain(domain)
    # for action in parser.actions:
    #     ipdb.set_trace()

    #     print(action.name)
    #     print(action.parameters)
    #     print(action.positive_preconditions)
    #     update_state(action, 'at start', 'p1')
    #     ipdb.set_trace()
    if instance:
        parser.parse_problem(instance)

    # preprocess
    # :predicates
    
    # parser.groundify()
    
    # parser.g_predicates = groundify(parser.predicates, parser.objects)
    # parser.predicates2idx = {i: idx for idx, i in enumerate(
    #     parser.g_predicates + parser.g_static_predicates)}

    # :actions
    # parser.g_actions = []
    # for act in parser.actions:
    #     parser.g_actions += [act.to_string()
    #                          for act in act.groundify(parser.objects, parser.types)]
    # parser.actions2idx = {i['fullname']: idx for idx,
    #                       i in enumerate(parser.g_actions)}

    # parser.g_actions = {}
    # for act in parser.actions:
    #     i = 0                                                                                        
    #     # print(act)
    #     for g_act in act.groundify(parser.objects, parser.types):
    #         act_dict = g_act.to_string()
    #         parser.g_actions[act_dict['fullname']] = act_dict
    #         i+=1
        # print(i)
        # sys.exit()

    return parser

