
import sys
import os
sys.path.append("..")
import ipdb
from datainit import domain
from datainit import problem
from datainit import line
from datainit import PDDL
from datainit import database
from datainit import plcApi as PLC
import _config
domain.gen_domain(_config)                                  # 生成domain  文件
problem.gen_problem(_config)                                # 生成problem 文件
domain_path  = _config.domain_config['domain_path']         # 从config中读取domain_path
problem_path = _config.problem_config['problem_path']       # 从config中读取problem_path
Parser  = PDDL.init_parser(domain_path, problem_path)       # 初始化Parser
Line = line.Line(_config)                                   # 根据config 初始化生产线
db = database.Database(**_config.db_config)                 # 创建数据库连接