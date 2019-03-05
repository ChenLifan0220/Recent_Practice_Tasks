def generate_transaction(pos, ref_date_str):
    transaction = {
        '_type': pos['TransactionType'],
        'CounterpartyAccount': {'_type': 'CounterpartyAccount',
                                'Id': pos.get('CounterpartyAccount_Id'),
                                'ShortCode': pos.get('CounterpartyAccount_ShortCode')},
        'Strategy': {'_type': 'Strategy',
                     'Id': pos.get('Strategy_Id'),
                     'ShortCode': pos.get('Strategy_ShortCode')},
        'Fund': pos['Fund'],
        'TradeDate': ref_date_str,
        'SettlementDate': ref_date_str,
        'Security': pos['Security'],
        'TradeType': pos['TradeType'],
        'PositionType': pos['PositionType'],
        'Quantity': pos['Quantity'],
        'SwapType': pos['SwapType'],
        'SwapId': pos['SwapId']
    }

    return transaction


def get_period_accrued_amount(coupon_tran, dc):
    prev_coupon_date = coupon_tran['PreviousCouponDate']
    coupon_date = coupon_tran['TradeDate']
    accrual_filter = {'TradeDate>': prev_coupon_date,
                      'TradeDate<=': coupon_date,
                      'Status': 1,
                      'Fund._id': coupon_tran['Fund']['Id'],
                      'Strategy._id': coupon_tran['Strategy']['Id'],
                      'CounterpartyAccount._id': coupon_tran['CounterpartyAccount']['Id'],
                      'Security': coupon_tran['Security']}

    accrual_transactions = dc.transaction.accrual.get(accrual_filter)
    return sum([item['Amount']['Value'] for item in accrual_transactions])