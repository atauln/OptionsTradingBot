from dataclasses import dataclass
from datetime import date, timedelta
from img2table.tables.objects.extraction import ExtractedTable
from math import floor
from wallstreet import Call, Put
from concurrent.futures import ThreadPoolExecutor

@dataclass
class Chart:
    name: str
    extracted_table: ExtractedTable

    def get_release_date(self):
        name_split=self.name.split('_')
        return date(int(name_split[2]), int(name_split[0]), int(name_split[1]))
    
    def get_expiration_date(self):
        name_split=self.name.split('_')
        release_date = self.get_release_date()
        return release_date + timedelta(days=int(name_split[-1].strip("DTE")))
    
    def get_total_cost(self, amount_per_contract: int):
        total_cost = 0
        for (i, col) in self.extracted_table.content.items():
            try:
                ticker = col[0].value.split("/")[0]
                if ticker == None:
                    continue
                bought_for_per_share = float(col[3 if self.name.split('_')[-2] == "CALL" else 2].value.strip('$'))
                total_cost += floor(amount_per_contract / (bought_for_per_share * 100)) * bought_for_per_share * 100
            except:
                continue
        return total_cost

    def get_value_of_column(self, col, amount_per_contract: int, acceptable_loss: int = 0.3) -> tuple:
        '''
        The first element of the return value is the total value of the options.
        The second element of the return value is the total value of the options with a stop limit.
        '''
        total_value = 0
        total_value_with_stop_limit = 0
        exp_date = self.get_expiration_date()
        name_split=self.name.split('_')
        try:
            ticker = col[0].value.split("/")[0]
            if ticker == None:
                return (0, 0)
            bought_for_per_share = float(col[3 if name_split[-2] == "CALL" else 2].value.strip('$'))
            if name_split[-2] == "CALL":
                strike = col[0].value.split("/")[1]
                call = Call(ticker, m=exp_date.month, d=exp_date.day, y=exp_date.year, strike=float(strike))
                total_value += call.price * 100 * floor(amount_per_contract / (bought_for_per_share * 100))
                if call.price < bought_for_per_share * (1 - acceptable_loss):
                    total_value_with_stop_limit += (bought_for_per_share * (1 - acceptable_loss)) * 100 * floor(amount_per_contract / (bought_for_per_share * 100))
                else:
                    total_value_with_stop_limit += call.price * 100 * floor(amount_per_contract / (bought_for_per_share * 100))
            else:
                strike = col[0].value.split("/")[2]
                put = Put(ticker, m=exp_date.month, d=exp_date.day, y=exp_date.year, strike=float(strike))
                total_value += put.price * 100 * floor(amount_per_contract / (bought_for_per_share * 100))
                if put.price < bought_for_per_share * (1 - acceptable_loss):
                    total_value_with_stop_limit += (bought_for_per_share * (1 - acceptable_loss)) * 100 * floor(amount_per_contract / (bought_for_per_share * 100))
                else:
                    total_value_with_stop_limit += put.price * 100 * floor(amount_per_contract / (bought_for_per_share * 100))
        except:
            return (0, 0)
        return (total_value, total_value_with_stop_limit)
    
    def get_value(self, amount_per_contract: int, acceptable_loss: int = 0.3) -> tuple:
        '''
        The first element of the return value is the total value of the options.
        The second element of the return value is the total value of the options with a stop limit.
        '''
        total_value = 0
        total_value_with_stop_limit = 0
        for (i, col) in self.extracted_table.content.items():
            # use the get_value_of_column function
            result = self.get_value_of_column(col, amount_per_contract, acceptable_loss)
            if result != (0, 0):
                total_value += result[0]
                total_value_with_stop_limit += result[1]

        return (total_value, total_value_with_stop_limit)
    
    def get_value_with_threading(self, amount_per_contract: int, acceptable_loss: int = 0.3) -> tuple:
        #Create a thread for each column
        #Each thread will calculate the value of the options in the column

        total_value = 0
        total_value_with_stop_limit = 0

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for col in self.extracted_table.content.values():
                futures.append(executor.submit(self.get_value_of_column, col, amount_per_contract, acceptable_loss))
            for future in futures:
                if future.result() != (0, 0):
                    total_value += future.result()[0]
                    total_value_with_stop_limit += future.result()[1]
        return (total_value, total_value_with_stop_limit)

    
    def get_columns(self):
        result = {}
        for (i, col) in self.extracted_table.content.items():
            try:
                ticker = col[0].value
                if ticker == None:
                    continue
                result[i] = [ele.value for ele in col]
            except:
                continue