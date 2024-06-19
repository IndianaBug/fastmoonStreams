    
# binance

# 'BTCUSD@perpetual@binance': {'tta_long_ratio': 0.7377, 'tta_short_ratio': 0.2623, 'tta_ratio': 2.8124, 'gta_long_ratio': 0.7377, 'gta_short_ratio': 0.2623, 'gta_ratio': 2.8124, 'ttp_long_ratio': 0.5607, 'ttp_short_ratio': 0.4393, 'ttp_ratio': 1.2761},

# BECAUSE ITS FOR ALL


def build_option_dataframes(self, expiration_ranges, ppr):
        columns = self.oiflowOption_getcolumns(ppr)
        df_dic = {}
        for i, exp_range in enumerate(expiration_ranges):
            if i in [0, len(expiration_ranges)-1]:
                df_dic[f'{int(exp_range)}'] = pd.DataFrame(columns=columns, dtype="float64") #.set_index('timestamp')
                df_dic[f'{int(exp_range)}']['timestamp'] = pd.to_datetime([])
                df_dic[f'{int(exp_range)}'].set_index('timestamp', inplace=True)
            if i in [len(expiration_ranges)-1]:
                df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}'] = pd.DataFrame(columns=columns, dtype="float64") #.set_index('timestamp')
                df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}']['timestamp'] = pd.to_datetime([])
                df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}'].set_index('timestamp', inplace=True)
            else:
                df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}'] = pd.DataFrame(columns=columns, dtype="float64") #.set_index('timestamp')
                df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}']['timestamp'] = pd.to_datetime([])
                df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}'].set_index('timestamp', inplace=True)
        df_dic.pop(f"{int(np.max(expiration_ranges))}_{int(np.min(expiration_ranges))}")
        return df_dic
    
    @staticmethod
    def oiflowOption_getcolumns(price_percentage_ranges: np.array):
        price_percentage_ranges[price_percentage_ranges == -0] = 0
        fuckot[fuckot == fuckot[0]] = 0
        fuckot = np.unique(fuckot)
        columns = np.concatenate((np.array(['timestamp']), fuckot), axis=0)
        return columns
    
    @staticmethod
    def oiflowOption_getranges(fuckot: np.array):
        fuckot = np.unique(np.sort(np.concatenate((fuckot, -price_percentage_ranges)), axis=0))
        price_percentage_ranges[price_percentage_ranges == -0] = 0
        price_percentage_ranges[price_percentage_ranges == price_percentage_ranges[0]] = 0
        price_percentage_ranges = np.unique(price_percentage_ranges)
        return price_percentage_ranges

    @staticmethod
    def oiflowOption_dictionary_helper(dfs, countdowns):
        countdown_ranges = list(dfs.keys())
        countdowns = np.unique(countdowns)
        countdown_ranges_flt = sorted(list(set(([float(item) for sublist in [x.split('_') for x in countdown_ranges] for item in sublist]))))
        mx = max(countdown_ranges_flt)
        mn = min(countdown_ranges_flt)
        l = {key: [] for key in countdown_ranges}
        for index, cf in enumerate(countdown_ranges_flt):
            for v in countdowns.tolist():
                if cf == mn and v <= cf:
                    l[str(int(cf))].append(v)
                if cf != mn and v <= cf and v > countdown_ranges_flt[index-1]:
                    l[f"{str(int(countdown_ranges_flt[index-1]))}_{str(int(cf))}"].append(v)
                if cf == mx and v > cf:
                    l[str(int(cf))].append(v)
            return l
    
    @staticmethod
    def getpcd(center, value):
        if center == 0 and value > center:
            return float(100)
        if value == 0 and value < center:
            return float(9999999999)
        else:
            diff = value - center
            average = (center + value) / 2
            percentage_diff = (diff / average) * 100
            return percentage_diff
        
        
    @staticmethod
    def oiflowOption_choose_range(ppr, value):
        for index, r in enumerate(ppr):
            if index == 0 and value < r:
                return ppr[0]
            if index == len(ppr)-1 and value > r:
                return ppr[-1]
            if value < r and value >= ppr[index-1]:
                return r
            



    def generate_data_for_plot(self):
        """ generates data for plots of options at a random timestamp to verify any discrepancies, good for testing """

        id_ = self.stream_data.get('id_ws') if "id_ws" in self.stream_data else self.stream_data.get('id_api')

        try:
            for type_, dict_ in zip(["Puts", "Calls"], [self.dict_dfpp, self.dict_dfpc]):
                for expiration in dict_:
                    
                    df = dict_.get(expiration).transpose()
                    df = pd.Series(df.values.transpose()[0], index=df.index.values)

                    plot_data = {
                        'x': df.index,
                        'y': df.values,
                        'xlabel': 'Level',
                        'ylabel': 'Amount',
                        'legend': f'Options oi data over {self.option_process_interval}, {self.exchange}, {self.symbol}, {type_}, {expiration} '
                    }

                    file_path = f"{self.folderpath}\\sample_data\\dfpandas\\processed\\oioption_{str(expiration)}_{type_}_{id_}.json"

                    with open(file_path, 'w') as file:
                        json.dump(plot_data, file)
                    
        except Exception as e:
            print(e)












# class DaskClientSupport():
#     logger = logging.getLogger("Example")  # just a reference
#     def find_free_port(self, start=8787, end=8800):
#         for port in range(start, end):
#             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#                 try:
#                     s.bind(('', port))
#                     return port
#                 except OSError:
#                     self.logger.error("Dask error, free port: %s", OSError, exc_info=True)
#                     continue
#         raise RuntimeError(f"No free ports available in range {start}-{end}")

#     def start_dask_client(self):
#         for attempt in range(5):
#             try:
#                 # Check for an available port
#                 free_port = self.find_free_port()
#                 print(f"Using port: {free_port}")

#                 # Initialize the Dask Client with the available port
#                 client = Client(n_workers=1, threads_per_worker=1, port=free_port)
#                 return client
#             except RuntimeError as e:
#                 self.logger.error("Dask error, RuntimeError, reconnecting: %s", e, exc_info=True)
#                 print(f"Attempt {attempt + 1}: {str(e)}")
#             except Exception as e:
#                 self.logger.error("Dask error, Unexpected error: %s", e, exc_info=True)
#                 print(f"Attempt {attempt + 1}: Unexpected error: {str(e)}")
#         raise RuntimeError("Failed to start Dask Client after several attempts")