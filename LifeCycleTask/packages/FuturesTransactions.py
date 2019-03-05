import services.LifeCycleTask.packages.TransactionHelper as transaction_helper
from services.LifeCycleTask.packages.Transactions import Transactions
import pandas as pd
from messer import DataCube


class FuturesTransactions(Transactions):
    def __init__(self, dc: DataCube):
        self._dc = dc

    def get_positions(self, positions_df):
        positions_df = positions_df[positions_df['_type'].isin(
            ['FuturesPosition'])]
        return positions_df

    def get_transactions(self, positions_df, ref_date_str):
        positions_df.ExpiryDateTime = pd.to_datetime(
            positions_df.ExpiryDateTime, errors='coerce')
        expiry_positions_df = positions_df[positions_df.RefDate >=
                                           positions_df.ExpiryDateTime]
        expiry_positions_df['TransactionType'] = 'FuturesExpirationTransaction'

        transactions = []
        positions = expiry_positions_df.to_dict('records')
        for pos in positions:
            transaction = transaction_helper.generate_transaction(
                pos, ref_date_str)
            transaction['SettlementType'] = pos['SettlementType']
            transaction['Multiplier'] = pos['Multiplier']
            transaction['Underlying'] = pos['Underlying']
            transactions.append(transaction)

        return transactions