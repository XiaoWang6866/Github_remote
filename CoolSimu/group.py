import numpy as np
import device

class chiller_group(object):
    def __init__(self,load,evap_flow,cond_flow,coefs,S_value,numbers,thresholds):
        self.load=load # nominal cooling load (kW) of each type of chillers
        self.evap_flow = evap_flow  # nominal evaporator water flow rate (L/s) of each type of chillers
        self.cond_flow = cond_flow  # nominal condensor water flow rate (L/s) of each type of chillers
        self.coefs = coefs # plr-dcop polynomial coefs of each type of chillers
        self.S_value=S_value # S values for flow resistance
        self.numbers=numbers # numbers of each type of chillers
        self.thresholds=thresholds # if the chiller is duplex, define the switching treshold of working conditions

        # creating chillers
        self.chiller = []
        cnt=0
        for i in range(len(self.numbers)):
            for j in range(self.numbers[i]):
                self.chiller.append(device.chiller(self.load[i],self.evap_flow[i],self.cond_flow[i],self.S_value[i], self.coefs[i], thresholds=self.thresholds[i]))
                cnt+=1
        self.chiller_tol=cnt

    def combined_S(self):
        S_value = 0
        for i in range(self.chiller_tol):
            if self.chiller[i].on:
                S_value += 1 / self.chiller[i].S_cond ** 0.5
        S_value = 1 / S_value ** 2
        return S_value

    def cooling_load_dist(self,tol_cooling_load):
        effective_flow=[]
        for i in range(self.chiller_tol):
            if self.chiller[i].on:
                effective_flow.append(self.chiller[i].evap_flow_standard)
            else:
                effective_flow.append(0)
        effective_flow=np.array(effective_flow)
        effective_load=effective_flow/np.sum(effective_flow)*tol_cooling_load
        return effective_load

    def condensing_water_dist(self,tol_flow):
        effective_flow=[]
        for i in range(self.chiller_tol):
            if self.chiller[i].on:
                effective_flow.append(self.chiller[i].cond_flow_standard)
            else:
                effective_flow.append(0)
        effective_flow=np.array(effective_flow)
        effective_flow=effective_flow/np.sum(effective_flow)*tol_flow
        return effective_flow

    def run(self,tol_cooling_load,tol_flow_rate,t_chiller_in):
        dist_load=self.cooling_load_dist(tol_cooling_load)
        dist_flow=self.condensing_water_dist(tol_flow_rate)
        t_chiller_out=[]
        ele_ciller=[]
        for i in range(self.chiller_tol):
            tout,ele=self.chiller[i].chiller_run(t_chiller_in,dist_load[i],dist_flow[i])
            t_chiller_out.append(tout)
            ele_ciller.append(ele)
        t_chiller_out=np.sum(np.array(t_chiller_out)*dist_flow)/tol_flow_rate
        return t_chiller_out,ele_ciller

class pump_group(object):
    def __init__(self,flow_standard,QH_coefs,QP_coefs,S_value, numbers):
        self.flow_standard=flow_standard
        self.QH_coefs =QH_coefs
        self.QP_coefs =QP_coefs
        self.S_value=S_value
        self.numbers=numbers

        # creating pumps
        self.pump = []
        cnt=0
        for i in range(len(self.numbers)):
            for j in range(self.numbers[i]):
                self.pump.append(device.pump(self.flow_standard[i],self.QH_coefs[i],self.QP_coefs[i] ,self.S_value[i]))
                cnt+=1
        self.pump_tol=cnt

    def combined_S(self):
        S_value = 0
        for i in range(self.pump_tol):
            if self.pump[i].on:
                S_value += 1 / self.pump[i].S_vlv ** 0.5
        S_value = 1 / S_value ** 2
        return S_value

    def pump_S(self):
        S_values=[]
        for i in range(self.pump_tol):
            if self.pump[i].on:
                S_values.append(self.pump[i].S_vlv)
            else:
                S_values.append(0)
        return np.array(S_values)

    def cal_pump_t_rise(self,ele_arr,eta_arr,flow_arr):
        t_rise=[]
        for i in range(ele_arr):
            mech_p=self.pump[i].cal_mech_power(ele_arr[i])
            t_rise.append(mech_p*(1-eta_arr[i]) / flow_arr[i] / 4.18 * 3.6)
        return t_rise

    def run(self,s_curve):
        flow = []
        header = []
        ele_pump = []
        etas = []
        for i in range(self.pump_tol):
            Q,H,E,I=self.pump[i].pump_run(s_curve[i])
            flow.append(Q)
            header.append(H)
            ele_pump.append(E)
            etas.append(I)
        return flow,header,ele_pump,etas

class tower_group(object):
    def __init__(self,airflow_range,power_max,S_value,numbers):
        self.airflow_range=airflow_range
        self.power_max =power_max
        self.S_value=S_value
        self.numbers=numbers

        # creating towers
        self.tower = []
        cnt=0
        for i in range(len(self.numbers)):
            for j in range(self.numbers[i]):
                self.tower.append(device.tower(self.airflow_range[i],self.power_max[i],self.S_value[i]))
                cnt+=1
        self.tower_tol=cnt

    def combined_S(self):
        S_value = 0
        for i in range(self.tower_tol):
            if self.tower[i].on:
                S_value += 1 / self.tower[i].S_vlv ** 0.5
        S_value = 1 / S_value ** 2
        return S_value
    def water_dist(self,tol_flow):
        effective_flow=[]
        for i in range(self.tower_tol):
            if self.tower[i].on:
                effective_flow.append(1)
            else:
                effective_flow.append(0)
        effective_flow=np.array(effective_flow)
        effective_flow=effective_flow/np.sum(effective_flow)*tol_flow
        return effective_flow

    def run(self,t_tower_in,t_wb,flow):
        dist_flow=self.water_dist(flow)
        t_tower_out = []
        ele_tower = []
        for i in range(self.tower_tol):
            tout,ele=self.tower[i].tower_run(t_tower_in,t_wb,dist_flow[i])
            t_tower_out.append(tout)
            ele_tower.append(ele)
        t_tower_out=np.sum(np.array(t_tower_out)*dist_flow)/flow
        return t_tower_out,ele_tower

class pipe_group(object):
    def __init__(self,S_value,h_value):
        self.S_value=S_value # pipe resistance
        self.h_value=h_value # header drop irrelevant to flow rate
        self.pipe=device.pipe(self.S_value,self.h_value) # creating pipes

    def combined_S(self,S_arr):
        S_value=0
        for i in range(len(S_arr)):
            S_value+=1/S_arr[i]**0.5
        S_value=1/S_value**2
        return S_value

    def loop_S_curve(self,S_arr):
        S_curve=self.pipe.cal_S_curve()
        for i in range(len(S_arr)):
            S_curve[2]+=S_arr[i]
        return S_curve
