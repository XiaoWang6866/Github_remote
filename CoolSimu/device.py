import numpy as np

class chiller(object):
    def __init__(self,cooling_load_standard,evap_flow_standard,cond_flow_standard,S_cond,coefs,thresholds=[],te=6,dt=1):
        self.te=te #evap temp
        self.dt=dt #heat transfer delta_t at condensor between refrigant and water
        self.cooling_load_standard=cooling_load_standard #nominal cooling load
        self.evap_flow_standard = evap_flow_standard  # nominal evaporator water flow rate
        self.cond_flow_standard = cond_flow_standard  # nominal condensor water flow rate
        self.thresholds=thresholds # 1-D array
        self.coefs=np.array(coefs) # 2-D array
        self.squares=np.array(range(0,len(self.coefs[0])))
        self.S_cond=S_cond # condensor S value for flow resistance
        self.on=False

    def cal_COP(self,cooling_load, tcout):
        if self.on==False:
            cooling_load=0
        plr = cooling_load / self.cooling_load_standard

        i=0
        while i<len(self.thresholds) and plr>self.thresholds[i]:
            i+=1

        dcop=np.sum(self.coefs[i]*plr**self.squares)
        dcop = max(dcop, 0.01)
        icop = (self.te + 273.15) / (tcout + self.dt - self.te)
        COP = icop * dcop
        COP = max(COP, 0.01)
        return COP

    def cal_ele(self,cooling_load,cop):
        if self.on==False:
            cooling_load=0
        return cooling_load/cop

    def chiller_run(self,t_condensor_in,cooling_load,water_flow):
        if self.on==False:
            return t_condensor_in,0
        dt=0.01
        t_condensor_out_0=t_condensor_in
        t_condensor_out = t_condensor_in + 2*dt
        elec=0
        while abs(t_condensor_out-t_condensor_out_0)>dt:
            t_condensor_out_0=t_condensor_out
            cop=self.cal_COP(cooling_load,t_condensor_out_0)
            elec=self.cal_ele(cooling_load,cop)
            t_rise=(cooling_load+elec)/(water_flow*4.18/3.6)
            t_condensor_out=t_condensor_in+t_rise
        return t_condensor_out,elec

class pump(object):
    def __init__(self,flow_standard,QH_coefs,QP_coefs,S_vlv,freq_standard=50,eta_e=0.976424306):
        self.flow_standard=flow_standard # standard flow
        self.freq_standard=freq_standard # standard frequncy
        self.eta_e=eta_e # electrical efficiency
        self.QH_coefs=np.array(QH_coefs)
        self.QP_coefs=np.array(QP_coefs)# note that the coefs are flow rate to electrical power, instead of mechanical power
        self.QH_squares=np.array(range(0,len(self.QH_coefs)))
        self.QP_squares=np.array(range(0,len(self.QP_coefs)))
        self.S_vlv=S_vlv # valve S value for flow resistance
        self.on=False
        self.frequency=self.freq_standard

    def switch_freq(self,coefs):
        ratio=self.frequency/self.freq_standard
        squares=np.arange(len(coefs)-1, -1, -1)
        new_coefs=coefs*ratio**np.flip(squares)
        return new_coefs

    def cal_flow(self,s_curve):#s_curve:s[0]+s[1]*G+s[2]*G^2,s[1]=0
        if self.on==False:
            return 0,False
        # cal Q from H
        Hcoefs=self.switch_freq(self.QH_coefs)
        tbd = False
        polys=Hcoefs-s_curve
        a,b,c=polys[2],polys[1],polys[0]
        discriminant = b**2-4*a*c
        if discriminant<0:
            print('no solution')
            Q=[0.1]
            return Q,tbd
        x=np.zeros(2)
        x[0]= (-b + discriminant**0.5) / (2 * a)
        x[1]= (-b - discriminant**0.5) / (2 * a)
        Q=[]
        for i in range(len(x)):
            if x[i]>=0.1 and x[i]<=self.flow_standard:
                Q.append(x[i])
        if len(Q)==0:
            Q.append(self.flow_standard)
        elif len(Q)==2:
            tbd=True
        return Q,tbd

    def cal_ele_power(self,flow,tbd=False):
        if self.on==False:
            return 0,0
        Pcoefs=self.switch_freq(self.QP_coefs)
        if tbd:
            ele1=np.sum(Pcoefs*flow[0]**self.QP_squares)
            ele2=np.sum(Pcoefs*flow[1]**self.QP_squares)
            if ele1<ele2:
                Q=flow[0]
                ele=ele1
            else:
                Q=flow[1]
                ele=ele2
        else:
            Q=flow[0]
            ele = np.sum(Pcoefs * Q ** self.QP_squares)
        return ele,Q

    def cal_mech_power(self,ele):
        if self.on==False:
            return 0
        return ele*self.eta_e

    def cal_header(self,flow):
        if self.on==False:
            return 0
        Hcoefs=self.switch_freq(self.QH_coefs)
        header = np.sum(Hcoefs * flow ** self.QH_squares)
        return header

    def cal_eta(self,flow,header,ele):
        if self.on==False:
            return 0
        mech_p=self.cal_mech_power(ele)
        return flow * header / mech_p / 360

    def pump_run(self,s_curve):
        if self.on==False:
            return 0,0,0,0
        flow,tbd=self.cal_flow(s_curve)
        ele,flow=self.cal_ele_power(flow)
        header=self.cal_header(flow)
        eta=self.cal_eta(flow,header,ele)
        return flow,header,ele,eta

class tower(object):
    def __init__(self,airflow_range,power_max,S_vlv,freq_standard=50):
        self.airflow_range=airflow_range # air flow range (min,max)
        self.freq_standard=freq_standard # standard frequncy
        self.power_max=power_max # elec power at maximum air flow
        self.S_vlv=S_vlv # valve S value for flow resistance
        self.on=False
        self.frequency=self.freq_standard

    def switch_freq(self):
        ratio=self.frequency/self.freq_standard
        ratio=np.clip(ratio,self.airflow_range[0]/self.airflow_range[1],1)
        air_flow=self.airflow_range[1]*ratio
        power=self.power_max*ratio**3
        return air_flow,power

    def cal_epsilon(self,water_flow,air_flow):
        # this is a built-in function, user may fit customized epsilon-NTU equations in terms of specific cooling towers
        if self.on==False:
            return 0
        ratio=air_flow/water_flow
        NTU=0.03051722*ratio # NTU ~ air-water-ratio
        epsilon= NTU/(1+NTU)
        return epsilon

    def tower_run(self,t_tower_in,t_wb,water_flow):
        if self.on==False:
            return 0,0
        air_flow,power=self.switch_freq()
        epsilon=self.cal_epsilon(water_flow,air_flow)
        t_tower_out=t_tower_in-epsilon*(t_tower_in-t_wb)
        return t_tower_out,power

class pipe(object):
    def __init__(self,S_value,h_value):
        self.S_value=S_value # pipe resistance
        self.h_value=h_value # header drop irrelevant to flow rate

    def cal_S_curve(self):
        return np.array([self.h_value,0,self.S_value])
