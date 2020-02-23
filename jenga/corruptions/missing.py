import numpy as np
import pandas as pd

class MissingValuesHighEntropy:

    def __init__(self, 
                    fraction, 
                    model, 
                    categorical_columns, 
                    numerical_columns,
                    categorical_value_to_put_in='NULL',
                    numerical_value_to_put_in=0):
        self.fraction = fraction
        self.model = model
        self.categorical_value_to_put_in = categorical_value_to_put_in
        self.numerical_value_to_put_in = numerical_value_to_put_in
        self.categorical_columns = categorical_columns
        self.numerical_columns = numerical_columns

    def __call__(self, clean_df):
        # we operate on a copy of the data
        df = clean_df.copy(deep=True)

        probas = self.model.predict_proba(df)
        # for samples with the smallest maximum probability 
        # the model is most uncertain
        cutoff = int(len(df) * (1-self.fraction))
        least_confident = probas.max(axis=1).argsort()[-cutoff:]
        for c in self.categorical_columns:
            if pd.api.types.is_categorical(df[c]):
                df[c].cat.add_categories([self.categorical_value_to_put_in], inplace=True)
        df.loc[df.index[least_confident], self.categorical_columns] = self.categorical_value_to_put_in
        df.loc[df.index[least_confident], self.numerical_columns] = self.numerical_value_to_put_in

        return df

class MissingValuesLowEntropy:

    def __init__(self, 
                    fraction, 
                    model, 
                    categorical_columns, 
                    numerical_columns,
                    categorical_value_to_put_in='',
                    numerical_value_to_put_in=0):
        self.fraction = fraction
        self.model = model
        self.categorical_value_to_put_in = categorical_value_to_put_in
        self.numerical_value_to_put_in = numerical_value_to_put_in
        self.categorical_columns = categorical_columns
        self.numerical_columns = numerical_columns

    def __call__(self, clean_df):
        # we operate on a copy of the data
        df = clean_df.copy(deep=True)

        probas = self.model.predict_proba(df)
        # for samples with the smallest maximum probability 
        # the model is most uncertain
        cutoff = int(len(df) * (1-self.fraction))
        most_confident = probas.max(axis=1).argsort()[:cutoff]
        for c in self.categorical_columns:
            if pd.api.types.is_categorical(df[c]):
                df[c].cat.add_categories([self.categorical_value_to_put_in], inplace=True)
            df.loc[df.index[most_confident], c] = self.categorical_value_to_put_in
        for c in self.numerical_columns:
            df.loc[df.index[most_confident], c] = self.numerical_value_to_put_in

        return df

class MissingValues:

    def __init__(self, fraction, column, na_value, missingness='MCAR'):
        self.column = column
        self.fraction = fraction
        self.na_value = na_value
        self.missingness = missingness

    def __call__(self, data):
        corrupted_data = data.copy(deep=True)
        if self.missingness == 'MCAR':
            idx = np.random.rand(len(data)) > self.fraction
            if pd.api.types.is_categorical(corrupted_data[self.column]):
                corrupted_data[self.column].cat.add_categories([self.na_value], inplace=True)
            corrupted_data.loc[idx, [self.column]] = self.na_value
        elif self.missingness == 'MAR':
            depends_on_col = np.random.choice(list(set(data.columns) - set([self.column])))
            # pick a random percentile of values in other column
            n_values_to_discard = int(len(data) * min(self.fraction,1.0))
            perc_lower_start = np.random.randint(0, len(data)-n_values_to_discard)
            perc_idx = range(perc_lower_start, perc_lower_start + n_values_to_discard)
            missing_indices = corrupted_data[depends_on_col].sort_values().iloc[perc_idx].index
            if pd.api.types.is_categorical(corrupted_data[self.column]):
                corrupted_data[self.column].cat.add_categories([self.na_value], inplace=True)
            corrupted_data.loc[missing_indices, [self.column]] = self.na_value
        elif self.missingness == 'MNAR':
            # pick a random percentile of values in this column
            n_values_to_discard = int(len(data) * min(self.fraction,1.0))
            perc_lower_start = np.random.randint(0, len(data)-n_values_to_discard)
            perc_idx = range(perc_lower_start, perc_lower_start + n_values_to_discard)
            missing_indices = corrupted_data[self.column].sort_values().iloc[perc_idx].index
            if pd.api.types.is_categorical(corrupted_data[self.column]):
                corrupted_data[self.column].cat.add_categories([self.na_value], inplace=True)
            corrupted_data.loc[missing_indices, [self.column]] = self.na_value
        else:
            print('missingness should be in MCAR, MAR or MNAR')
        return corrupted_data