import numpy as np
import group

class system(object):
    def __init__(self,chiller_paras,pump_paras,tower_paras,pipe_paras):
        self.chillers=group.chiller_group(chiller_paras['load'],chiller_paras['evap_flow'],chiller_paras['cond_flow'],
                                          chiller_paras['coefs'],chiller_paras['S_value'],chiller_paras['numbers'],
                                          chiller_paras['thresholds'])
        self.pumps=group.pump_group(pump_paras['flow'],pump_paras['QH_coefs'],pump_paras['QP_coefs'],
                                    pump_paras['S_value'],pump_paras['numbers'])
        self.towers=group.tower_group(tower_paras['airflow_range'],tower_paras['power_max'],
                                      tower_paras['S_value'],tower_paras['numbers'])
        self.pipes=group.pipe_group(pipe_paras['S_value'],pipe_paras['h_value'])

    def change_state(self,on_state,frequency):
        chiller_state=on_state['chillers']
        pump_state=[on_state['pumps'],frequency['pumps']]
        tower_state=[on_state['towers'],frequency['towers']]
        for i in range(len(chiller_state)):
            self.chillers.chiller[i].on=chiller_state[i]
        for i in range(len(pump_state[0])):
            self.pumps.pump[i].on=pump_state[0][i]
            self.pumps.pump[i].frequency=pump_state[1][i]
        for i in range(len(tower_state[0])):
            self.towers.tower[i].on=tower_state[0][i]
            self.towers.tower[i].frequency=tower_state[1][i]
        return

    def cal_pipe_t_rise(self,ele,flow,header,eta,chiller_s,pump_s,tower_s):
        # t_rise: pump, chiller to tower, tower to pump
        heats=np.zeros(3)
        half_pipe_S=self.pipes.S_value/2
        for i in range(self.pumps.pump_tol):
            if self.pumps.pump[i].on:
                heat=ele[i]*eta[i]*(header[i]-self.pipes.h_value)/header[i]
                S_seq=np.array([pump_s[i],chiller_s+half_pipe_S,tower_s+half_pipe_S])
                dist_heat = S_seq / np.sum(S_seq) * heat
                heats+=dist_heat
        t_rise=heats/ np.sum(flow) / 4.18 * 3.6
        return t_rise
    def water_system_run(self):
        chiller_S_cmb=self.chillers.combined_S()
        pump_S=self.pumps.pump_S()
        tower_S_cmb=self.towers.combined_S()
        S_curve=[]
        for i in range(self.pumps.pump_tol):
            S_curve.append(self.pipes.loop_S_curve([chiller_S_cmb,tower_S_cmb,pump_S[i]]))
        results=np.array(self.pumps.run(S_curve))
        t_rise_pipe=self.cal_pipe_t_rise(results[2],results[0],results[1],results[3],chiller_S_cmb,pump_S,tower_S_cmb)
        return results,t_rise_pipe

    def run(self,load,t_wb,on_state,frequency):
        ele_chiller,ele_pump,ele_tower=None,None,None
        self.change_state(on_state,frequency)
        water_system_re,t_rise_pipe=self.water_system_run()
        flow=water_system_re[0]
        tol_flow=np.sum(flow)
        ele_pump=water_system_re[2]

        dt = 0.01
        t_tower_out_0=t_wb
        t_tower_out=t_tower_out_0+2*dt
        while abs(t_tower_out-t_tower_out_0)>dt:
            t_tower_out_0=t_tower_out
            t_pump_in=t_tower_out_0+t_rise_pipe[2]
            t_pump_out=t_pump_in+t_rise_pipe[0]
            t_chiller_out,ele_chiller=self.chillers.run(load,tol_flow,t_pump_out) # t_pump_out is t_chiller_in
            t_tower_in=t_chiller_out+t_rise_pipe[1]
            t_tower_out, ele_tower=self.towers.run(t_tower_in,t_wb,tol_flow)
        return ele_chiller,ele_pump,ele_tower
