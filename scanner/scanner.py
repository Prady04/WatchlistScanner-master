import datetime
import os
import time

import pandas as pd

from chart import Chart
from downloader import get_historical_price
import tabulate


class Scanner(object):
    def __init__(self, watchlist_file=None):
        self.__ignore_list = []
        if watchlist_file is None:
            self.__watchlist = []
        else:
            self.load_watchlist(watchlist_file)
        self.patlist = []


    def load_watchlist(self, watchlist_file):
        """Read all scrips from watchlist file"""
        with open(watchlist_file, 'r') as f:
            watchlist = f.readlines()
            #watchlist = watchlist[:4]
        self.__watchlist = [w.replace('\n', '') for w in watchlist]
        print('Loaded {} symbols from watchlist.'.format(len(self.__watchlist)))

    @staticmethod
    def _create_chart(scrip):
        """Convert historical price info for scrip into chart & bar objects"""
        data = get_historical_price(scrip)
        if data.empty:
            return None
        else:           
            loaded = False
            if os.path.exists('tmp/{}.pickle'.format(scrip)):
                ctime = os.path.getctime('tmp/{}.pickle'.format(scrip))
                if datetime.datetime.strptime(time.ctime(ctime), "%a %b %d %H:%M:%S %Y").date() < datetime.datetime.today().date():
                    os.remove('tmp/{}.pickle'.format(scrip))
                else:
                    data = pd.read_pickle('tmp/{}.pickle'.format(scrip))
                    loaded = True
            if not loaded:
                data = get_historical_price(scrip)
                if data is None:
                    print('Unable to fetch data')
                    return None
                else:
                    pd.to_pickle(data, 'tmp/{}.pickle'.format(scrip))
            return Chart(data)

    def _collate(self, str):
        self.patlist.append("\n"+str)
        print(str)

    def __check_active_pattern(self, chart, n=5):
        """Check if any known candlestick patterns are formed in the last *n* days"""
        for i, bar in enumerate(reversed(chart.bars[-n:])):
            if bar.pattern != []:
                [self._collate('{:10} => t-{:1} ; pattern = {}'.format(
                    chart.name, i, pattern)) for pattern in bar.pattern
                    if pattern not in self.__ignore_list]
       
    def tabulate(self):
            
        data = self.patlist
        # Splitting each string into columns based on the '=>' delimiter
        rows = []
        for item in data:
        # Removing "; pattern =" from each item
            clean_item = item.replace('pattern =', '')
            # Splitting each string into columns based on the '=>' delimiter
            cols = clean_item.split(' => ')
            # Splitting each column based on ';' delimiter if it exists
            split_cols = [col.split(';') for col in cols]
            # Flattening the split columns into a single list
            flattened_cols = [item.strip() for sublist in split_cols for item in sublist]
            rows.append(flattened_cols)
        # Creating the table header
        header = ['Name', 'Index', 'Pattern']
        
        # Creating the table using tabulate
        table = tabulate.tabulate(rows, headers=header, tablefmt='grid')
        # Returning the table as a string
        print(table)
    def scan_watchlist(self):
        """Run pattern recognition on all scrips in watchlist"""
        for scrip in self.__watchlist:
            chart = Scanner._create_chart(scrip)
            if chart is not None:
                self.__check_active_pattern(chart)
        self.tabulate()
    @property
    def ignore_list(self):
        return self.__ignore_list

    @ignore_list.setter
    def ignore_list(self, ignore_patterns):
        self.__ignore_list = ignore_patterns
