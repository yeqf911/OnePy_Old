import pandas as pd
import itertools
import copy
import Queue
from threading import Thread
import multiprocessing

from statistics import stats
from execution import SimulatedExecutionHandler
from event import events

import os,sys
import matplotlib.pyplot as plt
import matplotlib.style as style
import threading

class OnePiece():
    def __init__(self, data, strategy, portfolio):
        self.events = events
        self.Feed = data
        self.strategy = strategy
        self.portfolio = portfolio
        self.broker = SimulatedExecutionHandler(commission=None)

        self.cur_holdings = self.portfolio.current_holdings
        self.all_holdings = self.portfolio.all_holdings
        self.initial_capital = self.portfolio.initial_capital

        self._activate = {}
        self._activate['print_order'] = False
        self._activate['print_stats'] = False
        self._activate['full_stats'] = False

    def sunny(self):
        while True:
            try:
                event = self.events.get(False)
            except Queue.Empty:
                self.Feed.update_bars()
                self.portfolio._update_timeindex()
            else:
                if event is not None:
                    if event.type == 'Market':
                        self.strategy.luffy()
                        # print self.Feed.latest_bar_dict['000001'][-1]

                    if event.type == 'Signal':
                        self.portfolio.update_signal(event)
                        # print event.datetime

                    if event.type == 'Order':
                        if (self.cur_holdings['cash'] > event.quantity_l*event.price and
                            self.cur_holdings['cash'] > event.quantity_s*event.price):

                            self.broker.execute_order(event)

                            # print order
                            if self._activate['print_order']:
                                event.print_order()

                    if event.type == 'Fill':
                        self.portfolio.update_fill(event)

                        if self._activate['print_order']:
                            event.print_executed()
                    # if event.type == 'Fill':
                    #     def dd(self,event):
                    #         self.portfolio.update_fill(event)
                    #         if self._activate['print_order']:
                    #             event.print_executed()
                    #     a = threading.Thread(target=dd,args=(event))
                    #     t.setDaemon(True)
                    #     a.start

                if self.Feed.continue_backtest == False:
                    # a.join()
                    print 'Final Portfolio Value: '+ str(self.all_holdings[-1]['total'])

                    if self._activate['print_stats']:
                        self.portfolio.create_equity_curve_df()
                        print self.portfolio.output_summary_stats()

                    if self._activate['full_stats']:
                        self.get_analysis()
                    break

    def print_trade(self):
        self._activate['print_order'] = True

    def print_stats(self,full=False):
        self._activate['print_stats'] = True
        if full:
            self._activate['full_stats'] = True
    def get_log(self):
        log = pd.DataFrame(self.portfolio.trade_log)
        return log[['datetime','symbol','s_type','price','qty',
                    'cur_positions','cash','total','PnL']]

    def get_equity_curve(self):
        df = self.portfolio.create_equity_curve_df()
        df.index =pd.DatetimeIndex(df.index)
        return df

    def get_analysis(self):
        tlog = self.get_log()
        dbal = self.get_equity_curve()
        start = self.get_equity_curve().index[0]
        end = self.get_equity_curve().index[-1]
        capital = self.initial_capital
        return stats(tlog, dbal, start, end, capital)
####################### from portfolio ###############################

    def get_current_holdings(self):
        return pd.DataFrame(self.cur_holdings)

    def get_current_positions(self):
        return pd.DataFrame(self.portfolio.current_positions)

    def get_all_holdings(self):
        return pd.DataFrame(self.all_holdings)

    def get_all_positions(self):
        return pd.DataFrame(self.portfolio.all_positions)

    def get_symbol_list(self):
        return self.portfolio.symbol_list

    def get_initial_capital(self):
        return self.initial_capital


######################### For Optimize ###############################

def params_generator(*args):
    d = {}
    for i in range(len(args)):
        d[i] = args[i]

    if len(args) == 1:
        return itertools.product(d[0])
    if len(args) == 2:
        return itertools.product(d[0],d[1])
    if len(args) == 3:
        return itertools.product(d[0],d[1],d[2])
    if len(args) == 4:
        return itertools.product(d[0],d[1],d[2],d[3])
    if len(args) == 5:
        return itertools.product(d[0],d[1],d[2],d[3],d[4])
    if len(args) == 6:
        return itertools.product(d[0],d[1],d[2],d[3],d[4],d[5])
    if len(args) == 7:
        return itertools.product(d[0],d[1],d[2],d[3],d[4],d[5],d[6])
    if len(args) == 8:
        return itertools.product(d[0],d[1],d[2],d[3],d[4],d[5],d[6],d[7])
    if len(args) == 9:
        return itertools.product(d[0],d[1],d[2],d[3],d[4],d[5],d[6],d[7],d[8])
    if len(args) == 10:
        return itertools.product(d[0],d[1],d[2],d[3],d[4],d[5],d[6],d[7],d[8],d[9])

def optimizer(strategyclass,portfolioclass,feed,params_generator,pkl_name=None):
    log = {}
    if pkl_name is None:
        pkl_name = 'optimizer_log'

    pkl_path = os.path.join(sys.path[0],'%s.pkl' % pkl_name)
    pd.to_pickle(log, pkl_path)

    while True:
        try:
            p_list = params_generator.next()
        except:
            break
        else:
            backup = copy.deepcopy(feed)
            data = backup
            strategy = strategyclass(data,p_list)
            portfolio = portfolioclass(data)
            go = OnePiece(data, strategy, portfolio)

            def combine():
                go.sunny()
                print p_list
                log = pd.read_pickle(pkl_path)
                log[p_list] = go.get_all_holdings().iat[-1,-1]
                pd.to_pickle(log, pkl_path)
            p = multiprocessing.Process(target=combine)
            p.daemon=True
            p.start()
    p.join()

def opti_analysis(pkl_path):
    log = pd.read_pickle(pkl_path)
    log = dict((v,k) for k,v in log.iteritems())

    df = pd.DataFrame(log).T
    df.reset_index(inplace=True)
    df.rename(columns={'index':'Capital'},inplace=True)

    style.use('ggplot')
    df[['Capital']].plot(table=df)
    plt.show()





######################################################################
