from messer import DataCube
import events_booking_utils


class BondEventsManager(object):
    def __init__(self, dc: DataCube, logger):
        self._dc = dc
        self._logger = logger

    def get_coupon_schedules(self, security):
        coupon_schedule_manager = events_booking_utils.CouponScheduleManager(
            self._dc, self._logger)
        return coupon_schedule_manager.calculate_coupon_dates(security)

    def get_events_callable_puttable(self, new_security, old_security, put_call):
        events = []
        schedule_property = put_call + 'Schedule'
        event_type = put_call + 'Date'
        schedule_dates_ls = new_security.get(schedule_property)

        if schedule_dates_ls:
            if events_booking_utils.is_new_event(new_security, old_security, [schedule_property]):
                for schedule_date in schedule_dates_ls:
                    event_date = {
                        'Date': schedule_date['Date'],
                        'Security': new_security['Key'],
                        'EventType': event_type,
                        'Status': 'Active',
                        'PutCallPrice': schedule_date['Price'],
                        'Description': '[{}] {} @ {}'.format(event_type, new_security['Name'], schedule_date['Price']),
                        'Username': 'System'
                    }
                    events.append(event_date)
                self._logger.info(
                    '{} {} date events returned'.format(len(events), put_call))

        return events

    def get_events_coupon(self, new_security, old_security):
        coupon_events = []

        coupon_dates_ls = new_security.get('CouponDateList')
        coupon_rate = new_security.get('Coupon', 0)

        if coupon_dates_ls:
            if events_booking_utils.is_new_event(new_security, old_security, ['CouponDateList', 'Coupon']):
                for cpd in coupon_dates_ls:
                    event_cpn = {
                        'Date': cpd,
                        'Security': new_security['Key'],
                        'EventType': 'BondCouponPayment',
                        'CouponRate': coupon_rate,
                        'Status': 1,
                        'Description': '[CouponPayment Bond] Rate - {} Coupon date {}'.format(coupon_rate,
                                                                                              events_booking_utils.get_date_display_fmt(
                                                                                                  cpd)),
                        'Username': 'System'
                    }
                    coupon_events.append(event_cpn)
                self._logger.info(
                    '{} bond coupon events returned'.format(len(coupon_events)))

        return coupon_events

    def get_events_maturity(self, new_security, old_security):
        maturity_events = []

        maturity_date = new_security.get('MaturityDate')

        if maturity_date:
            if events_booking_utils.is_new_event(new_security, old_security, ['MaturityDate']):
                # This is to handle if the date is saved as '0001-01-01T00:00:00Z'
                if not events_booking_utils.is_valid_datetime_fields(maturity_date):
                    return []
                event_maturity = {
                    'Date': maturity_date,
                    'Security': new_security['Key'],
                    'EventType': 'BondMaturity',
                    'Status': 1,
                    'Description': '[Maturity Bond] Maturity date {}'.format(events_booking_utils.get_date_display_fmt(maturity_date)),
                    'Username': 'System'
                }
                self._logger.info('Bond maturity event returned')
                maturity_events.append(event_maturity)
        else:
            self._logger.warning(
                'Bond security {} does not have a maturity date'.format(new_security['Key']))
        return maturity_events

    def get_events_conversion(self, new_security, old_security):
        convertible_events = []

        convertible_date = new_security.get('LastConvertibleDate')
        underlying = new_security.get('Underlying')
        conversion_ratio = int(new_security.get('ConversionRatio'))

        if convertible_date and underlying and conversion_ratio:
            if events_booking_utils.is_new_event(new_security, old_security, ['LastConvertibleDate', 'Underlying', 'ConversionRatio']):
                # This is to handle if the date is saved as '0001-01-01T00:00:00Z'
                if not events_booking_utils.is_valid_datetime_fields(convertible_date):
                    return []
                event_conversion = {
                    'Date': convertible_date,
                    'Security': new_security['Key'],
                    'EventType': 'BondConversion',
                    'Status': 1,
                    'Description': '[Conversion Bond] Convertible date {}'.format(
                        events_booking_utils.get_date_display_fmt(convertible_date)),
                    'Underlying': new_security['Underlying'],
                    'ConversionRatio': new_security['ConversionRatio'],
                    'ConversionPrice': new_security['ConversionPrice'],
                    'Username': 'System'
                }
                self._logger.info('Bond convertible event returned')
                convertible_events.append(event_conversion)
        else:
            self._logger.warning(
                'Convertible bond security {} does not have convertible date, underlying or conversion ratio'.format(new_security['Key']))
        return convertible_events