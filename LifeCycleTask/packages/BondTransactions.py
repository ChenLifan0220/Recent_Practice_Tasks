import services.LifeCycleTask.packages.CouponHelper as coupon_helper
import services.LifeCycleTask.packages.TransactionHelper as transaction_helper
from services.LifeCycleTask.packages.Transactions import Transactions
import pandas as pd
from messer import DataCube


class BondTransactions(Transactions):
    def __init__(self, dc: DataCube):
        self._dc = dc

    def get_positions(self, positions_df):
        positions_df = positions_df[positions_df['_type'].isin(
            ['BondPosition', 'ConvertibleBondPosition'])]
        return positions_df

    def get_transactions(self, positions_df, ref_date_str):
        positions_df.MaturityDate = pd.to_datetime(
            positions_df.MaturityDate, errors='coerce')
        # Maturity
        maturity_positions_df = positions_df[positions_df.RefDate >=
                                             positions_df.MaturityDate]
        maturity_positions_df['TransactionType'] = 'MaturityTransaction'

        positions_df = positions_df[(
            positions_df['RefDate'] <= positions_df['MaturityDate'])]
        positions_df = coupon_helper.get_coupon_positions_df(positions_df)

        # Accrual
        # only accrual interest payment if a bond is non swap or if a swap bond is priced clean
        accrual_positions_df = positions_df[
            ((positions_df['SwapType'] == 'None') | (positions_df['BondPriceType'] == 'Clean')) &
            (positions_df.RefDate < positions_df.NextCouponDate)]
        accrual_positions_df['TransactionType'] = 'Accrual'

        # Coupon
        coupon_positions_df = positions_df[positions_df.RefDate ==
                                           positions_df.NextCouponDate]
        coupon_positions_df['TransactionType'] = 'BondCouponTransaction'

        transaction_positions_df = pd.concat(
            [maturity_positions_df, accrual_positions_df, coupon_positions_df], ignore_index=True)

        transactions = []
        positions = transaction_positions_df.to_dict('records')
        for pos in positions:
            transaction = transaction_helper.generate_transaction(
                pos, ref_date_str)
            transaction_type = transaction['_type']
            if transaction_type == 'MaturityTransaction':
                # use 100 as we assume that the price of bond is the percent of the face value
                transaction['Price'] = 100,
                transaction['CloseOnly'] = True,
                transaction['Description'] = '[Bond Maturity] {}, Notional {}'.format(
                    ref_date_str[0:10], pos['Quantity'])
                transactions.append(transaction)
            elif transaction_type == 'Accrual':
                transaction['Amount'] = {'_type': 'CurrencyValue', 'Ccy': pos.get('Ccy'),
                                         'Value': pos.get('DailyAccrual')}
                transaction['AccrualType'] = 'BondInterest'
                transaction['Coupon'] = pos['Coupon']
                transaction['Description'] = '[Bond Coupon Accrual], Notional {} @ Coupon {}'.format(pos['Quantity'],
                                                                                                     pos['Coupon'])
                transactions.append(transaction)
            elif transaction_type == 'BondCouponTransaction':
                transaction['Amount'] = {'_type': 'CurrencyValue', 'Ccy': pos.get('Ccy'),
                                         'Value': pos.get('PeriodCoupon')},
                transaction['BondPriceType'] = pos['BondPriceType']
                transaction['Coupon'] = pos['Coupon'],
                transaction['PreviousCouponDate'] = pos['PreviousCouponDateStr'],
                transaction['Notional'] = pos['Quantity'],
                transaction['Description'] = '[Bond Coupon Payment] {} - {} Notional {} @ Coupon {}'.format(
                    pos['PreviousCouponDateStr'][0:10],
                    ref_date_str[0:10], pos['Quantity'], pos['Coupon'])
                transactions.append(transaction)

                if transaction['SwapType'] == 'None' or transaction['BondPriceType'] == 'Clean':
                    reverse_accrual_tran = pos.copy()
                    reverse_accrual_tran['_type'] = 'Accrual'
                    transaction['AccrualType'] = 'BondInterest'
                    reverse_accrual_tran['Amount']['Value'] = transaction_helper.get_period_accrued_amount(transaction,
                                                                                                           self._dc) * (
                        -1)
                    reverse_accrual_tran['Description'] = '[Reverse Interest Accrual], {} - {} '.format(
                        pos['PreviousCouponDate'][0:10],
                        pos['TradeDate'][0:10])
                    transactions.append(reverse_accrual_tran)

        return transactions