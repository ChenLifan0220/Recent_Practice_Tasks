import abc


class Transactions(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_positions(self, positions_df):
        pass

    @abc.abstractmethod
    def get_transactions(self, positions_df, ref_date_str):
        pass