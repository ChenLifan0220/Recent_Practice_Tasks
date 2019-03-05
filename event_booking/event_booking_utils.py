from datetime import datetime
import logging
import os

import QuantLib as ql

from messer import DataCube

FORMAT = '%(asctime)s %(levelname)s %(name)s - %(message)s'

logging.basicConfig(format=FORMAT)
logging.getLogger().setLevel(os.getenv('LOG_LEVEL', 'INFO'))

logger = logging.getLogger(__name__)
is_secure = os.getenv('SECURE', 'True') in ['True', '1', 'Yes', 'Y']
server = os.getenv('SERVER', DataCube.LOCAL_SERVER)
dc = DataCube(server, port=os.getenv('PORT'), secure=is_secure,
              api_key=os.getenv('APIKEY'))

COUPON_FREQENCY_MAPPING = {
    'Annual': 1,
    'SemiAnnual': 2,
    'TriAnnual': 3,
    'Quarterly': 4,
    'Monthly': 12,
    'BiWeekly': 26,
    'Weekly': 52
}


def is_new_event(new_sec, old_sec, fields):
    return not old_sec or any([new_sec.get(f) != old_sec.get(f) for f in fields])


def get_date_display_fmt(dt_json_fmt):
    return dt_json_fmt[:10] if dt_json_fmt else None


def is_valid_datetime_fields(dt_json_fmt):
    dt_datetime_fmt = datetime.strptime(dt_json_fmt, dc.DATE_JSON_FORMAT)
    if dt_datetime_fmt == datetime.min:
        logger.error('{} is invalid, please check.'.format(dt_json_fmt))
        return False
    else:
        return True


class CouponScheduleManager(object):
    def __init__(self, dc: DataCube, logger):
        self._dc = dc
        self._logger = logger

    # Need to revisit
    # QuantLib module calculates coupon dates backward from the maturity date. We set the maturity to 99 years after the first coupon date.
    def _get_perpetual_maturity_date(self, first_coupon_date):
        maturity_date = datetime(
            first_coupon_date.year + 99, first_coupon_date.month, first_coupon_date.day)
        return maturity_date

    def _get_ql_calendar_type(self, country=None):
        if country == 'HK':
            return ql.HongKong()
        elif country == 'CN':
            return ql.China()
        elif country == 'GB':
            return ql.UnitedKingdom()
        elif country == 'SG':
            return ql.Singapore()
        elif country == 'US':
            return ql.UnitedStates()
        elif country == 'General':
            return ql.WeekendsOnly()
        else:
            return ql.NullCalendar()

    def _get_first_coupon_date(self, security):
        first_coupon_date = security.get('FirstCouponDate')
        if not first_coupon_date:
            self._logger.error(
                'First coupon date does not exist in {}.'.format(security['Key']))
            return None
        first_coupon_date = datetime.strptime(
            first_coupon_date, self._dc.DATE_JSON_FORMAT)
        return first_coupon_date

    def _get_maturity_date(self, security, first_coupon_date):
        maturity_date = security.get('MaturityDate')
        if maturity_date:
            maturity_date = datetime.strptime(
                maturity_date, self._dc.DATE_JSON_FORMAT)
        elif security.get('IsPerpetual') is True:
            maturity_date = self._get_perpetual_maturity_date(
                first_coupon_date)
        else:
            self._logger.error(
                'Maturity date does not exist in {}'.format(security['Key']))
            return None
        return maturity_date

    def _get_coupon_frequency_num(self, security):
        coupon_frequency = security.get('Frequency')
        if not coupon_frequency:
            self._logger.error('Coupon frequency is {} in the security {}'.format(
                coupon_frequency, security['Key']))
            return None
        coupon_freq_num = COUPON_FREQENCY_MAPPING.get(coupon_frequency)
        return coupon_freq_num

    def calculate_coupon_dates(self, security):
        coupon_dates = []

        first_coupon_date = self._get_first_coupon_date(security)
        if not first_coupon_date:
            return []

        maturity_date = self._get_maturity_date(security, first_coupon_date)
        if not maturity_date:
            return []

        coupon_freq_num = self._get_coupon_frequency_num(security)
        if not coupon_freq_num:
            return []

        try:
            start_date = ql.Date(first_coupon_date.day,
                                 first_coupon_date.month, first_coupon_date.year)
        except:
            self._logger.error('Cannot get day/month/year of first coupon date {} for security {}'.format(
                first_coupon_date, security['Key']))
            return []

        try:
            end_date = ql.Date(maturity_date.day,
                               maturity_date.month, maturity_date.year)
        except:
            self._logger.error('Cannot get day/month/year of maturity date {} for security {}'.format(
                maturity_date, security['Key']))
            return []

        country = security.get('Countries').get('Domicile').get('ShortCode')
        quant_lib_calendar_type = self._get_ql_calendar_type(country)
        schedule_list = ql.Schedule(start_date, end_date, ql.Period(coupon_freq_num),
                                    quant_lib_calendar_type,
                                    ql.Unadjusted, ql.Unadjusted, ql.DateGeneration.Backward, False)

        for coupon_date in schedule_list:
            coupon_date = datetime(
                coupon_date.year(), coupon_date.month(), coupon_date.dayOfMonth())
            format_coupon_date = coupon_date.strftime(
                DataCube.DATE_JSON_FORMAT)
            coupon_dates.append(format_coupon_date)

        return coupon_dates