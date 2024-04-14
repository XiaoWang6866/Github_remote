from system import system

on_state={'chillers':[0,1,0,0,0,1,0,0,0,0],
          'pumps':[0,1,0,0,0,1,0,0,0,0,1,0],
          'towers':[0,1,0,0,0,1,0,0,0,0,1,0,0,0,1,0]}
freq={'pumps':[50,45,50,50,50,50,50,50,50,50,50,50],
      'towers':[50,40,50,50,50,50,50,50,50,50,50,50,50,50,50,50]}

load=[7042,2641,2462]
e_flow=[239.23,83.73,83.89]
c_flow=[396.14,140.71,139]
coef_chiller1=[[+ 6.939E-02,+ 1.969E+00,- 2.343E+00],
               [+ 1.155E-01,+ 9.164E-01,- 3.948E-01]]
coef_chiller2=[[+ 1.311E-01,+ 7.971E-01,- 3.311E-01]]
coef_chiller3=[[- 4.753E-02,+ 1.725E+00,- 9.436E-01]]
coef=[coef_chiller1,coef_chiller2,coef_chiller3]
S_value=[2.680E-06,2.062E-05,2.117E-05]
N=[6,3,1]
tr=[[0.5],[],[]]
chiller_paras={'load':load,'evap_flow':e_flow,'cond_flow':c_flow,'coefs':coef,'S_value':S_value,'numbers':N,'thresholds':tr}

flow=[1446,530]
Hcoef=[[+ 4.504E+01,+ 2.482E-03,- 6.203E-06],
       [+ 4.386E+01,- 5.086E-03,- 2.653E-05]]
Pcoef=[[+ 1.296E+02,+ 1.939E-02,+ 2.783E-05,- 1.378E-08],
       [+ 4.370E+01,+ 5.835E-02,- 4.744E-06,- 3.163E-08]]
S_value=[1.16E-05,6.53e-5]#todo3.34782E-06,2.49199E-05
N=[7,5]
pump_paras={'flow':flow,'QH_coefs':Hcoef,'QP_coefs':Pcoef,'S_value':S_value,'numbers':N}

air_flow_range=[[25537,47100]]
power_max=[37.049]
S_value=[1.92e-4]#2.83447E-05]#todo
N=[16]
tower_paras={'airflow_range':air_flow_range,'power_max':power_max,'S_value':S_value,'numbers':N}

S=7.40485575e-08#pipe
h=5#tower
pipe_paras={'S_value':S,'h_value':h}

cooling_water_system=system(chiller_paras,pump_paras,tower_paras,pipe_paras)

load=7256
t_wb=23

elecs=cooling_water_system.run(load,t_wb,on_state,freq)

print('chiller:',elecs[0])
print('pump:',elecs[1])
print('tower:',elecs[2])
