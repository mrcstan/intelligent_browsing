import pandas as pd
from os.path import isfile
from typing import List, Dict

pd.set_option('display.max_columns', None, 'expand_frame_repr', False)

class Rating:
    def __init__(self, rating_json, topK: int=5):
        '''
        :param rating_json:
            see json2data_frame for the expected format
        :param topK:
             topK ranks to be used for calculating avg precision
        '''
        self._rating_df_ = self.json2data_frame(rating_json)
        self._group_avg_precisions_ = []
        self._mean_avg_precisions_ = []
        self._topK_ = topK

    @staticmethod
    def json2data_frame(json_data) -> pd.DataFrame:
        """
        :param json_data:
            json_data should have the following format
            json_data[url][query][method][rank] = relevance
        :return:
            a data frame with the columns corresponding to the keys and values of json_data
        """
        data_list = []
        for (website, query_method_rank_relevance) in json_data.items():
            for (query, method_rank_relevance) in query_method_rank_relevance.items():
                for (method, rank_relevance) in method_rank_relevance.items():
                    for (rank, relevance) in rank_relevance.items():
                        data_list.append([website, query, method, rank, relevance])
        return pd.DataFrame(data_list, columns=['Website', 'Query', 'Method', 'Rank', 'Relevance'])

    @staticmethod
    def write_data_frame_to_file(file_path: str, df: pd.DataFrame, replace: bool=True):
        """
        :param file_path:
        :param df:
        :param replace:
            replace existing file if true. Otherwise, append to existing file
        """
        if replace or not isfile(file_path):
            df.to_csv(file_path, header=True, index=False)
        else:  # else it exists so append without writing the header
            df.to_csv(file_path, mode='a', header=False, index=False)

    def write_print_data_frame(self):
        print(self._rating_df_)

    def write_ratings_to_file(self, file_path: str):
        self.write_data_frame_to_file(file_path, self._rating_df_)

    def write_avg_precisions_to_file(self, file_path: str):
        self.write_data_frame_to_file(file_path, self._group_avg_precisions_)

    def write_mean_avg_precisions_to_file(self, file_path: str):
        # Write mean avg precisions of each method to file
        self.write_data_frame_to_file(file_path, self._mean_avg_precisions_)

    def print_mean_avg_precision(self):
        print(self._mean_avg_precisions_)

    def sort_data_frame(self):
        self._rating_df_.sort_values(by=['Website', 'Query', 'Method', 'Rank'], inplace=True)

    def calculate_avg_precision(self, df_rank_relevance: pd.DataFrame) -> float:
        '''
        :param df_rank_relevance:
            data frame containing the ranking of the matches and the relevance of the ranking
            0 is assumed to have the highest rank
            data frame will be sorted in ascending order of the ranking before calculating the avg precision
            only the topK ranks will be used to calculate avg precision
        :return:
            avg_precision
        '''
        if len(df_rank_relevance) == 0:
            return 0

        precision = 0
        count_relevant = 0
        df_rank_relevance.sort_values(by=['Rank'], inplace=True)
        for ind, row in df_rank_relevance.iterrows():
            if row['Rank'] >= self._topK_:
                break
            if row['Relevance']:
                count_relevant += 1
                max_rank = row['Rank']+1
                precision += count_relevant/max_rank

        if count_relevant == 0:
            return 0
        else:
            return precision/count_relevant

    def calculate_avg_precision_each_group(self):
        self._group_avg_precisions_ = self._rating_df_.groupby(['Website', 'Query', 'Method']).apply(self.calculate_avg_precision).reset_index()
        self._group_avg_precisions_.reset_index(inplace=True, drop=True)
        self._group_avg_precisions_.rename(columns={0:'Avg-Precision'}, inplace=True)
        return self._group_avg_precisions_

    def calculate_mean_avg_precisions(self):
        self.calculate_avg_precision_each_group()
        self._mean_avg_precisions_ = self._group_avg_precisions_.groupby('Method')['Avg-Precision'].agg(['mean', 'std']).reset_index()
        self._mean_avg_precisions_.rename(columns={'mean': 'Mean-Avg-Precision', 'std': 'Std-Avg-Precision'}, inplace=True)
        return self._mean_avg_precisions_

    def set_topK(self, topK):
        self._topK_ = topK

    def get_topK(self):
        return self._topK_