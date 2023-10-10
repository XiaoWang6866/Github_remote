from tools import Model
import pandas
import re
from multiprocessing import cpu_count

config=pandas.read_csv('config.csv')
method=config['algorithm'][0]
train_days=re.sub(r'\D', '',str(config['histsize'][0]))
update_days=re.sub(r'\D', '',str(config['predwindow'][0]))
n_per_day=re.sub(r'\D', '',str(config['resolution'][0]))
renew_way=re.sub(r'[^a-zA-Z]', '',config['renew'][0]).lower()
error=config['error'][0]
outform=re.sub(r'[^a-zA-Z]', '',config['outform'][0]).lower()
parallel=re.sub(r'[^-\d.]', '',str(config['parallel'][0]))
func=re.sub(r'[^a-zA-Z]', '',config['func'][0]).lower()
CaseModel = Model()
CaseModel.load_from_file("input-t.csv","input-p.csv",func)
metric = CaseModel.eval_get_result(to_file='output', error=error, outform=outform,parallel=min(cpu_count(), int(parallel)))
print('100 % completed')
if metric:
    print(error+'=',metric)