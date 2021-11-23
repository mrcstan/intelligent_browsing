import pandas as pd
from os.path import isfile

pd.set_option('display.max_columns', None, 'expand_frame_repr', False)

class Rating:
    def __init__(self, json_data, topK=5):
        '''
        :param json_data:
            assume json_data format is in the following form
            json_data[url][query][method][rank] = relevance
        :param topK:
             topK ranks to be used for calculating avg precision
        '''
        self.json_data = json_data
        self.df = self.json2data_frame(json_data)
        self.group_avg_precisions = []
        self.mean_avg_precisions = []
        self.topK = topK

    def json2data_frame(self, json_data):
        data_list = []
        for (website, query_method_rank_relevance) in json_data.items():
            for (query, method_rank_relevance) in query_method_rank_relevance.items():
                for (method, rank_relevance) in method_rank_relevance.items():
                    for (rank, relevance) in rank_relevance.items():
                        data_list.append([website, query, method, rank, relevance])
        return pd.DataFrame(data_list, columns=['Website', 'Query', 'Method', 'Rank', 'Relevance'])

    def write_data_frame_to_file(self, file_path, df, replace=True):
        if replace or not isfile(file_path):
            df.to_csv(file_path, header=True, index=False)
        else:  # else it exists so append without writing the header
            df.to_csv(file_path, mode='a', header=False, index=False)

    def write_ratings_to_file(self, file_path):
        self.write_data_frame_to_file(file_path, self.df)

    def write_avg_precisions_to_file(self, file_path):
        self.write_data_frame_to_file(file_path, self.group_avg_precisions)

    def write_mean_avg_precisions_to_file(self, file_path):
        # Write mean avg precisions of each method to file
        self.write_data_frame_to_file(file_path, self.mean_avg_precisions)

    def sort_data_frame(self):
        self.df.sort_values(by=['Website', 'Query', 'Method', 'Rank'], inplace=True)

    def calculate_avg_precision(self, df_rank_relevance):
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
            if row['Rank'] >= self.topK:
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
        self.group_avg_precisions = self.df.groupby(['Website', 'Query', 'Method']).apply(self.calculate_avg_precision).reset_index()
        self.group_avg_precisions.reset_index(inplace=True, drop=True)
        self.group_avg_precisions.rename(columns={0:'Avg-Precision'}, inplace=True)
        return self.group_avg_precisions

    def calculate_mean_avg_precisions(self):
        self.calculate_avg_precision_each_group()
        self.mean_avg_precisions = self.group_avg_precisions.groupby('Method')['Avg-Precision'].mean().reset_index()
        self.mean_avg_precisions.rename(columns={'Avg-Precision':'Mean-Avg-Precision'}, inplace=True)
        return self.mean_avg_precisions


# if __name__ == "__main__":
#     user_ratings = {'https://www.channelnewsasia.com/singapore/singapore-mature-pme-unemployed-job-search-wsg-2293696': {'find job': {3: True, 1: False, 0: True}},
#                     'https://www.channelnewsasia.com/singapore/singapore-mature-pme-unemployed-job-search': {'find job2': {1: False, 6: True, 3: True}}}
#
#     relevances = pd.DataFrame({'Rank': [0, 1, 2, 3, 4], 'Relevance':[True, False, True, False, True]})
#     rating = Rating(user_ratings)
#     print(rating.df)
#     print(rating.calculate_avg_precision(relevances))
#     #rating.sort_data_frame()
#     rating.print_data_frame()
#     rating.calculate_mean_AP()
#     print(rating.group_avg_precisions)
#     print('MAP: ', rating.mean_avg_precision)