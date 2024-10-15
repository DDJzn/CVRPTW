# 2024.09.09
# model V1


from gurobipy import Model, GRB, GurobiError, quicksum, tupledict, LinExpr
import json


"""parmater and set input"""
class get_static_parameter():
    def __init__(self, path) -> None:
        """
        get static parameter from .json (info about vehicle and deadhead)

        Args:
            path (str): static parameters [.json]
        """
        self.path = path
        # self.read()

    
    def read(self):
        with open(self.path) as f:
            self.settings = json.load(f)
        
        self.get_paras()
        self.get_sets()


    def get_paras(self):
        """
        generate global variable
        """
        global Q_r_v, Q_f_v, dh, M, tc
        # dh is travel time between real-world sation, d_i_j in the model generated in order CLASS
        # tc is travel time per min, pi_v_i_j in the model generated in order CLASS

        Q_r_v = self.settings['capacity_passengers']
        Q_f_v = self.settings['capacity_packages']
        dh = self.settings['travel_time']
        M = self.settings['M']
        tc = self.settings['travel_cost']

        Q_r_v = {int(k): v for k, v in Q_r_v.items()}
        Q_f_v = {int(k): v for k, v in Q_f_v.items()}


    def get_sets(self):
        """
        generate global set
        """
        global V

        V = [int(i) for i in Q_r_v.keys()]


class get_order_parameter():
    def __init__(self, order_path) -> None:
        """
        get order from .json (info about passengers and packages) and convert it into parameters

        Args:
            order_path (str): order info [.json]
        """
        self.order_path = order_path
        # self.read()


    def read(self):
        with open(self.order_path) as f:
            self.order = json.load(f)
        
        self.get_sets()
        self.get_paras()


    def get_sets(self):
        global Cr, Cf, N, P, D, o, s
        Cr, Cf, N, P, D = [], [], [], [], []
        o, s = -1, 9999

        for id, info in self.order.items():
            if info['number_passengers'] != 0:
                Cr.append(int(id))
            if info['number_packages'] != 0:
                Cf.append(int(id))
            P.append(info['startstation'])
            D.append(info['endstation'])
        
        N = P + D + [o, s]


    def get_paras(self):
        global q_rp_i, q_fp_i, q_rm_i, q_fm_i, d_i_j, e_p_i, l_p_i, e_d_i, l_d_i, p_i, d_i, omega_i, pi_v_i_j
        q_rp_i, q_fp_i, q_rm_i, q_fm_i, d_i_j, e_p_i, l_p_i, e_d_i, l_d_i, p_i, d_i, omega_i, pi_v_i_j = {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}

        for i in N:
            q_rp_i[i], q_fp_i[i], q_rm_i[i], q_fm_i[i] = 0, 0, 0, 0
        
        for id, info in self.order.items():
            id = int(id)
            p, d = info['startstation'], info['endstation']
            p_i[id], d_i[id] = p, d
            if info['number_passengers'] != 0:
                q_rp_i[p] = info['number_passengers']
                q_rm_i[d] = info['number_passengers']
            if info['number_packages'] != 0:
                q_fp_i[p] = info['number_packages']
                q_fm_i[d] = info['number_packages']
            
            e_p_i[id], l_p_i[id] = info['starttime_earliest'], info['starttime_lastest']
            e_d_i[id], l_d_i[id] = info['endtime_earliest'], info['endtime_lastest']
            omega_i[id] = info['profit']

        for i in P+D:
            for j in P+D:
                if i != j:
                    d_i_j[(i, j)] = dh[str(i // 1000)][str(j // 1000)]

            d_i_j[(o, i)] = dh[str(o)][str(i // 1000)]
            d_i_j[(s, i)] = dh[str(s)][str(i // 1000)]
            d_i_j[(i, s)] = dh[str(s)][str(i // 1000)]

        for v in V:
            for i in P+D:
                for j in P+D:
                    if i != j:
                        pi_v_i_j[(v, i, j)] = tc[str(v)] * dh[str(i // 1000)][str(j // 1000)]

                pi_v_i_j[(v, o, i)] = tc[str(v)] * dh[str(o)][str(i // 1000)]
                pi_v_i_j[(v, s, i)] = tc[str(v)] * dh[str(s)][str(i // 1000)]
                pi_v_i_j[(v, i, s)] = tc[str(v)] * dh[str(s)][str(i // 1000)]
                pi_v_i_j[(v, i, o)] = tc[str(v)] * dh[str(o)][str(i // 1000)]
            
            pi_v_i_j[(v, s, o)] = tc[str(v)] * dh[str(o)][str(s)]
            pi_v_i_j[(v, o, s)] = tc[str(v)] * dh[str(s)][str(o)]


class getAllInput():
    def __init__(self, order_path, static_path) -> None:
        """
        get all input ready

        Args:
            order_path (str): OrderSettings.json
            static_path (str): StaticSettings.json
        """
        self.order_path = order_path
        self.static_path = static_path

        
        sta = get_static_parameter(self.static_path)
        sta.read()

        ord = get_order_parameter(self.order_path)
        ord.read()


"""establish model"""
class get_model_index():
    def __init__(self) -> None:
        """
        generate indexes in model
        """
        self.vij()
        self.vi()
        self.i()


    def vij(self):
        global VIJ
        VIJ = [(v, i, j) for v in V for i in N for j in N if i != j]


    def vi(self):
        global VI, VIf  # VI: I belong to N; VIf: I belong to C^f
        VI = [(v, i) for v in V for i in N]
        VIf = [(v, i) for v in V for i in Cf]

    
    def i(self):
        global I
        I = [i for i in P+D]


class model_formulation():
    def __init__(self) -> None:
        get_model_index()
        self.model()
    

    def model(self):
        """
        activate gurobi
        """
        try:
            self.m = Model(" ")  # establish model
            self.variables()
            self.constraints()
            self.read()
            self.optimization()
            self.printLog()

        except GurobiError as e:
            print('Error code' + str(e.errno) + ':' + str(e))
        except AttributeError as e:
            print('Encountered an attribute error:' + str(e))


    def variables(self):
        """
        generate variables
        """
        self.X = self.m.addVars(VIJ, lb=0, ub=1, vtype=GRB.BINARY, name='X')
        self.SP = self.m.addVars(VIf, lb=0, ub=1, vtype=GRB.BINARY, name='S+')
        self.SM = self.m.addVars(VIf, lb=0, ub=1, vtype=GRB.BINARY, name='S-')

        self.T = self.m.addVars(I, lb=0, ub=1440, vtype=GRB.CONTINUOUS, name='t')
        self.TP = self.m.addVars(VIf, lb=0, ub=1440, vtype=GRB.CONTINUOUS, name='t+')
        self.TM = self.m.addVars(VIf, lb=0, ub=1440, vtype=GRB.CONTINUOUS, name='t-')
        self.QR = self.m.addVars(VI, lb=0, ub=100, vtype=GRB.CONTINUOUS, name='qr')
        self.QF = self.m.addVars(VI, lb=0, ub=100, vtype=GRB.CONTINUOUS, name='qf')

        self.aui = 0  # auxiliary variables index (to handle quadratic function)
        self.aui_max = int(1e5)
        self.AU = self.m.addVars(self.aui_max, lb=-GRB.INFINITY, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name='AU')  # auxiliary variables (to handle quadratic function)

        self.m.update()
        
    
    def constraints(self):
        """
        generate constraints as well as auxiliary variables (to handle quadratic function)
        """
        # self.constr_test()
        self.constr_F()
        self.constr_H()
        self.constr_C()
        self.constr_TW()
        self.constr_T()
        self.constr_PD()
        self.constr_SS()


        self.m.update()
        print("auxiliary index:", self.aui)
        

    def read(self):
        """
        read model file
        """
        None


    def optimization(self):
        """
        generate objective and optimization parameters
        """
        self.profit_passenger = self.m.addVar(vtype=GRB.CONTINUOUS, name='p_passenger')  # profits generated from passengers
        self.profit_package = self.m.addVar(vtype=GRB.CONTINUOUS, name='p_package')  # profits generated from packages
        self.cost = self.m.addVar(vtype=GRB.CONTINUOUS, name='cost')  # cost of deadhead process

        expr1, expr2 = LinExpr(), LinExpr()
        for v in V:
            for j in P+D+[o,s]:
                for i in Cr:
                    if p_i[i] != j:
                        expr1 += omega_i[i] * self.X[(v, j, p_i[i])]
                for i in Cf:
                    if p_i[i] != j:
                        expr2 += omega_i[i] * self.X[(v, j, p_i[i])]
        
        self.m.addConstr(self.profit_passenger == expr1)
        self.m.addConstr(self.profit_package == expr2)

        expr3 = LinExpr()
        for v in V:
            for i in P+D+[o,s]:
                for j in P+D+[o,s]:
                    if i != j:
                        expr3 += pi_v_i_j[(v, i, j)] * self.X[(v, i, j)]
        
        self.m.addConstr(self.cost == expr3)

        self.obj = self.profit_package + self.profit_passenger - self.cost
        self.m.setObjective(self.obj, GRB.MAXIMIZE)
        # self.m.setParam('NonConvex', 2)
        # self.m.setParam('DualReductions', 0)
        # self.m.setParam('MIPGap', gap)
        # self.m.setParam('LogFile', log_path)
        self.m.optimize()

        if self.m.status == GRB.Status.INFEASIBLE:
            print('Optimization was stopped with status %d' % self.m.status)
            self.m.computeIIS()
            for c in self.m.getConstrs():
                if c.IISConstr:
                    print('%s' % c.constrName)
            self.m.write("infeasiable.ilp")


    def printLog(self):
        """
        print info and save file
        """
        self.m.write(result_path)


    def constr_test(self):
        print('---------------------')
        print('RUN TEST constriants')
        print('---------------------')

        # self.m.addConstr(self.X[1,-1,1001] == 1, name=f'Test{1}')
        # self.m.addConstr(self.X[1,1001,9999] == 1, name=f'Test{2}')
        # self.m.addConstr(self.X[1,9999,-1] == 1, name=f'Test{3}')
        # self.m.addConstr(self.X[2,-1,9999] == 1, name=f'Test{4}')
        # self.m.addConstr(self.X[2,9999,2001] == 1, name=f'Test{5}')
        # self.m.addConstr(self.X[2,2001,3001] == 1, name=f'Test{6}')
        # self.m.addConstr(self.X[2,3001,3002] == 1, name=f'Test{7}')
        # self.m.addConstr(self.X[2,3002,-1] == 1, name=f'Test{8}')
        

    def constr_F(self):
        """
        flow balance
        """
        for i in P+D:
            self.m.addConstr(quicksum(self.X.select('*', '*', i)) <= 1, name=f'F1_{i}')
            for v in V:
                self.m.addConstr(quicksum(self.X.select(v, '*', i)) == quicksum(self.X.select(v, i, '*')), name=f'F2_{i}_{v}')
        
        for i in [s]:
            for v in V:
                self.m.addConstr(quicksum(self.X.select(v, '*', i)) == quicksum(self.X.select(v, i, '*')), name=f'F2_{i}_{v}')


    def constr_H(self):
        """
        pick up and deliver by the same veh, transfer package
        """
        for i in Cr:
            for v in V:
                self.m.addConstr(quicksum(self.X.select(v, '*', p_i[i])) == quicksum(self.X.select(v, d_i[i], '*')), name=f'H1_{i}_{v}')

        for i in Cf:
            expr1, expr2 = LinExpr(), LinExpr()
            for v in V:
                self.m.addConstr((1 - quicksum(self.SM.select('*', i))) * quicksum(self.X.select(v, '*', p_i[i])) == (1 - quicksum(self.SP.select('*', i))) * quicksum(self.X.select(v, d_i[i], '*')), name=f'H2_{i}_{v}')
                
                expr1 += self.SM[(v, i)] * quicksum(self.X.select(v, '*', p_i[i]))
                expr2 += self.SP[(v, i)] * quicksum(self.X.select(v, d_i[i], '*'))
            self.m.addConstr(expr1 == expr2, name=f'H3_{i}')
                

    def constr_C(self):
        """
        capacity
        """
        tpC1, tpC2 = [], []  # tupledict of constraints C1 C2
        for i in P+D+[o]:
            for j in P+D:
                if i != j:
                    for v in V:
                        tpC1.append(((v, i, j), self.X[(v, i, j)] * (self.QR[(v, i)] + q_rp_i[j] - q_rm_i[j])))
                        tpC2.append(((v, i, j), self.X[(v, i, j)] * (self.QF[(v, i)] + q_fp_i[j] - q_fm_i[j])))
        
        i = s
        for j in P+D:
            if i != j:
                for v in V:
                    tpC2.append(((v, i, j), self.X[(v, i, j)] * (self.QF[(v, i)] + q_fp_i[j] - q_fm_i[j])))

        tpC1, tpC2 = tupledict(tpC1), tupledict(tpC2)

        for i in P+D:
            for v in V:
                self.m.addConstr(self.QR[(v, i)] == quicksum(tpC1.select(v, '*', i)), name=f'C1_{i}_{v}')
                self.m.addConstr(self.QF[(v, i)] == quicksum(tpC2.select(v, '*', i)), name=f'C2_{i}_{v}')
        
        for v in V:
            self.m.addConstr(self.QR[(v, o)] == 0, name=f'C3_{v}')
            self.m.addConstr(self.QF[(v, o)] == 0, name=f'C4_{v}')

        for i in P+D:
            for v in V:
                self.m.addConstr(self.QR[(v, i)] <= Q_r_v[v], name=f'C5_{i}_{v}')
                self.m.addConstr(self.QF[(v, i)] <= Q_f_v[v], name=f'C6_{i}_{v}')
        for i in [s]:
            for v in V:
                self.m.addConstr(self.QF[(v, i)] <= Q_f_v[v], name=f'C6_{i}_{v}')


    def constr_TW(self):
        """
        time window
        """
        for i in P+D:
            for j in P+D:
                if i != j:
                    for v in V:
                        self.m.addConstr(self.T[i] + d_i_j[(i, j)] <= self.T[j] + M * (1 - self.X[(v, i, j)]), name=f'TW1_{i}_{j}_{v}')
        
        for i in Cr+Cf:
            self.m.addConstr(e_p_i[i] <= self.T[p_i[i]], name=f'TW2_{i}')
            self.m.addConstr(self.T[p_i[i]] <= l_p_i[i], name=f'TW3_{i}')
            self.m.addConstr(e_d_i[i] <= self.T[d_i[i]], name=f'TW4_{i}')
            self.m.addConstr(self.T[d_i[i]] <= l_d_i[i], name=f'TW5_{i}')

    
    def constr_T(self):
        tpT2_1, tpT2_2 = [], []  # tupledict of constraints T2
        for i in Cf:
            for j in P+D+[o]:
                for v in V:
                    tpT2_1.append(((v, j, i), self.X[(v, j, s)] * (self.QF[(v, j)] + q_fp_i[p_i[i]])))
                    tpT2_2.append(((v, j, i), self.X[(v, j, s)] * (self.QF[(v, j)] - q_fp_i[p_i[i]])))
        tpT2_1, tpT2_2 = tupledict(tpT2_1), tupledict(tpT2_2)

        for i in Cf:
            self.m.addConstr(quicksum(self.SM.select('*', i)) == quicksum(self.SP.select('*', i)), name=f'T2_{i}')
            for v in V:
                self.m.addConstr(self.SP[(v, i)] + self.SM[(v, i)] <= 1, name=f'T1_{i}_{v}')
                self.m.addConstr(self.SM[(v, i)] <= quicksum(self.X.select(v, '*', p_i[i])), name=f'T3_{i}_{v}')
                self.m.addConstr(self.SP[(v, i)] <= quicksum(self.X.select(v, d_i[i], '*')), name=f'T4_{i}_{v}')
                self.aui += 1
                self.m.addConstr(self.AU[self.aui] == quicksum(tpT2_1.select(v, '*', i)))
                self.aui += 1
                self.m.addConstr(self.AU[self.aui] == quicksum(tpT2_2.select(v, '*', i)))
                self.m.addConstr((self.SP[(v, i)] + self.SM[(v, i)]) * self.QF[(v, s)] == self.SP[(v, i)] * self.AU[self.aui-1] + self.SM[(v, i)] * self.AU[self.aui], name=f'T7_{i}_{v}')
                self.m.addConstr(self.TM[(v, i)] >= self.TP[(v, i)], name=f'T10_{i}_{v}')
                self.m.addConstr(self.SM[(v, i)] <= quicksum(self.X.select(v, '*', s)), name=f'T5_{i}_{v}')
                self.m.addConstr(self.SP[(v, i)] <= quicksum(self.X.select(v, s, '*')), name=f'T6_{i}_{v}')
                self.m.addConstr(self.TM[(v, i)] <= M * self.SM[(v, i)], name=f'T11_{i}_{v}')
                self.m.addConstr((1 - self.SM[(v, i)]) * M + self.TP[(v, i)] >= self.T[p_i[i]], name=f'T12_{i}_{v}')


        for i in Cf:
            for j in P+D:
                for v in V:
                    self.m.addConstr(self.T[j] + d_i_j[(j, s)] <= self.TP[(v, i)] + M * (1 - self.SM[(v, i)] * self.X[(v, j, s)]), name=f'T8_{i}_{j}_{v}')
                    self.m.addConstr(self.TM[(v, i)] + d_i_j[(s, j)] <= self.T[j] + M * (1 - self.SP[(v, i)] * self.X[(v, s, j)]), name=f'T9_{i}_{j}_{v}')


    def constr_PD(self):
        """
        pick-up and drop off sequence
        """
        for i in Cf+Cr:
            self.m.addConstr(self.T[p_i[i]] + d_i_j[(p_i[i], d_i[i])] <= self.T[d_i[i]], name=f'PD1_{i}')
    

    def constr_SS(self):
        """
        out-depot
        """
        for v in V:
            self.m.addConstr(quicksum(self.X.select(v, o, '*')) == quicksum(self.X.select(v, '*', o)), name=f'SS1_{v}')
            self.m.addConstr(quicksum(self.X.select(v, o, '*')) <=1 , name=f'SS2_{v}')
            self.m.addConstr(quicksum(self.X.select(v, o, '*')) >= quicksum(self.X.select(v, '*', '*')) / M, name=f'SS3_{v}')





# static_path = 'input/StaticSettings.json'
static_path = 'test/network_data.json'
# order_path = 'input/OrderSettings.json'
order_path = 'test/order_data.json'
result_path = 'result_test.sol'
getAllInput(order_path, static_path)
model_formulation()


