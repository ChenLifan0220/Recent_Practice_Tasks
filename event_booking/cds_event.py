from messer import DataCube
import events_booking_utils


class CDSEventsManager(object):
    def __init__(self, dc: DataCube, logger):
        self._dc = dc
        self._logger = logger

    def get_coupon_schedules(self, security):
        coupon_schedule_manager = events_booking_utils.CouponScheduleManager(
            self._dc, self._logger)
        return coupon_schedule_manager.calculate_coupon_dates(security)

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
                        'EventType': 'CDSCouponPayment',
                        'CouponRate': coupon_rate,
                        'Status': 1,
                        'Description': '[CouponPayment CDS] Rate - {} Coupon date {}'.format(coupon_rate,
                                                                                             events_booking_utils.get_date_display_fmt(
                                                                                                 cpd)),
                        'Username': 'System'
                    }
                    coupon_events.append(event_cpn)
                self._logger.info(
                    '{} coupon events returned'.format(len(coupon_events)))

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
                    'EventType': 'CDSMaturity',
                    'Status': 1,
                    'Description': '[Maturity CDS] Maturity date {}'.format(
                        events_booking_utils.get_date_display_fmt(maturity_date)),
                    'Username': 'System'
                }
                self._logger.info('Maturity event returned')
                maturity_events.append(event_maturity)
        else:
            self._logger.warning(
                'The security {} does not have a maturity date'.format(new_security['Key']))
        return maturity_events