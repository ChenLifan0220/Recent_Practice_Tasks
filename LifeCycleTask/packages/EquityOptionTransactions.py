import services.LifeCycleTask.packages.TransactionHelper as transaction_helper
from services.LifeCycleTask.packages.Transactions import Transactions
import pandas as pd
from messer import DataCube
import logging


class EquityOptionTransactions(Transactions):
    def __init__(self, dc: DataCube):
        self._dc = dc
        self._logger = logging.getLogger(__name__)

    def get_positions(self, positions_df: pd.DataFrame):
        positions_df = positions_df[positions_df['_type'].isin(
            ['EquityOptionPosition'])]
        return positions_df

    def get_transactions(self, positions_df: pd.DataFrame, ref_date_str: str):
        positions_df.ExpiryDateTime = pd.to_datetime(
            positions_df.ExpiryDateTime, errors='coerce')
        expiry_positions_df = positions_df[positions_df.RefDate >=
                                           positions_df.ExpiryDateTime]
        expiry_positions_df['TransactionType'] = 'EquityOptionExpiryTransaction'

        transactions = []
        positions = expiry_positions_df.to_dict('records')
        for pos in positions:
            transaction = transaction_helper.generate_transaction(
                pos, ref_date_str)

            price_underlying = pos.get('PriceUnderlying')
            if not price_underlying:
                self._logger.error('Underlying price not found for equity option {}. Skip the expiry'.format(
                    transaction['Security']))
                continue

            transaction['PriceUnderlying'] = price_underlying['Value']
            transaction['Strike'] = pos['Strike']
            transaction['PutCallFlag'] = pos['PutCallFlag']
            transaction['SettlementType'] = pos['SettlementType']
            transaction['Multiplier'] = pos['Multiplier']
            transaction['Underlying'] = pos['Underlying']
            transactions.append(transaction)

        return transactions