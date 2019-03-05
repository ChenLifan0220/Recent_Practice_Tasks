from messer import DataCube
import events_booking_utils


class EquityOptionsEventsManager(object):
    def __init__(self, dc: DataCube, logger):
        self._dc = dc
        self._logger = logger

    def get_events_expiry(self, new_security, old_security):
        expiry_events = []

        expiry_date = new_security.get('ExpiryDateTime')
        put_call_flag = new_security.get('PutCallFlag')
        settlement_type = new_security.get('SettlementType')
        strike = new_security.get('Strike')
        underlying = new_security.get('Underlying')

        if not expiry_date:
            self._logger.warning(
                'Equity Option {} does not have a expiry date'.format(new_security['Key']))
        else:
            if events_booking_utils.is_new_event(new_security, old_security, ['ExpiryDateTime', 'PutCallFlag', 'SettlementType', 'Strike', 'Underlying']):
                # This is to handle if the date is saved as '0001-01-01T00:00:00Z'
                if not events_booking_utils.is_valid_datetime_fields(expiry_date):
                    return []
                if not put_call_flag:
                    self._logger.warning(
                        'The Equity Option {} has an invalid put/call flag {}. Please check'.format(new_security['Key'],
                                                                                                    put_call_flag))
                if not settlement_type:
                    self._logger.warning(
                        'The Equity Option {} has an invalid settlement type {}. Please check'.format(new_security['Key'],
                                                                                                      settlement_type))
                if not strike:
                    self._logger.warning(
                        'The Equity Option {} has an invalid strike {}. Please check'.format(new_security['Key'],
                                                                                             strike))
                if not underlying:
                    self._logger.warning(
                        'The Equity Option {} has an invalid underlying {}. Please check'.format(new_security['Key'],
                                                                                                 underlying))
                event_expiry = {
                    'Date': expiry_date,
                    'Security': new_security['Key'],
                    'EventType': 'OptionExpiry',
                    'Status': 1,
                    'Description': '[Expiry Equity Option] Expiry date: {}, [Name] Name: {}, [PutCallFlag] Put Call flag: {}, [SettlementTYpe] Settlement type: {}, [Strike] Strike: {}, [Underlying] Underlying: {}'.format(
                        events_booking_utils.get_date_display_fmt(expiry_date), new_security.get('Name'), put_call_flag, settlement_type, strike, underlying),
                    'AssetClass': new_security.get('AssetClass'),
                    'Name': new_security.get('Name'),
                    'PutCallFlag': put_call_flag,
                    'SettlementType': settlement_type,
                    'Strike': strike,
                    'Underlying': underlying,
                    'Username': 'System'
                }
                self._logger.info('Expiry event returned')
                expiry_events.append(event_expiry)
        return expiry_events