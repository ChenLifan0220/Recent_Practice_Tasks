from messer import DataCube
import events_booking_utils


class FuturesEventsManager(object):
    def __init__(self, dc: DataCube, logger):
        self._dc = dc
        self._logger = logger

    def get_events_expiry(self, new_security, old_security):
        expiry_events = []

        expiry_date = new_security.get('ExpiryDateTime')

        if expiry_date:
            if events_booking_utils.is_new_event(new_security, old_security, ['ExpiryDateTime']):
                # This is to handle if the date is saved as '0001-01-01T00:00:00Z'
                if not events_booking_utils.is_valid_datetime_fields(expiry_date):
                    return []
                event_expiry = {
                    'Date': expiry_date,
                    'Security': new_security['Key'],
                    'EventType': 'FutureExpiry',
                    'Status': 1,
                    'Description': '[Expiry Future] Expiry date: {}'.format(
                        events_booking_utils.get_date_display_fmt(expiry_date)),
                    'AssetClass': new_security['AssetClass'],
                    'Underlying': new_security['Underlying'],
                    'Name': new_security['Name'],
                    'Username': 'System'
                }
                self._logger.info('Expiry event returned')
                expiry_events.append(event_expiry)
        else:
            self._logger.warning(
                'The Futures {} does not have a expiry date'.format(new_security['Key']))
        return expiry_events