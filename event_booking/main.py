import json
import os

from datetime import datetime

import events_booking_utils
from bond_events import BondEventsManager
from cds_events import CDSEventsManager
from equity_options_events import EquityOptionsEventsManager
from events_booking_utils import logger
from futures_events import FuturesEventsManager
from fx_forward_events import FxForwardEventsManager
from messer import DataCube

FORMAT = '%(asctime)s %(levelname)s %(name)s - %(message)s'

is_secure = os.getenv('SECURE', 'True') in ['True', '1', 'Yes', 'Y']
server = os.getenv('SERVER', DataCube.LOCAL_SERVER)
dc = DataCube(server, port=os.getenv('PORT'), secure=is_secure,
              api_key=os.getenv('APIKEY'))


def get_sec_country(amend_security):
    sec_country = amend_security.get('Countries')
    if sec_country:
        sec_domicile = sec_country.get('Domicile')
        if sec_domicile:
            sec_shortcode = sec_domicile.get('ShortCode')
            return sec_shortcode


def update_bond_key(message_key, amend_security):
    sec_name = amend_security.get('Name')
    if amend_security.get('IsPerpetual'):
        sec_maturity = 'PERP'
    else:
        sec_maturity = amend_security.get('MaturityDate')
        if not events_booking_utils.is_valid_datetime_fields(sec_maturity):
            sec_maturity = None
        try:
            sec_maturity = datetime.strftime(datetime.strptime(
                sec_maturity, DataCube.DATE_JSON_FORMAT), '%Y%m%d')
        except:
            logger.error(
                'The security {} has an invalid maturity date {}. Please check'.format(amend_security['Key'],
                                                                                       sec_maturity))
    if amend_security.get('IsZeroCoupon'):
        sec_coupon = 0
    else:
        sec_coupon = amend_security.get('Coupon')

    if sec_name and sec_coupon and sec_maturity:
        amend_key = '{}_{}_{}'.format(
            sec_name, sec_coupon, sec_maturity)
        if message_key != amend_key:
            amend_security['Key'] = amend_key
            dc.sec_master.save_security(amend_security)
            return amend_key
        else:
            logger.info(
                'The key of security {} has already conformed to naming convention.'.format(amend_security['Key']))
    else:
        logger.error(
            'Security {} has no name/coupon/maturity date.'.format(amend_security['Key']))


def update_bond_orders_symbol(message_key, amend_key, amend_security):
    orders = dc.order.get({'OrderStatus': 'Open'})
    for order in orders:
        if order.get('Symbol') == message_key and order.get('Source') == 'DropCopy':
            order['Symbol'] = amend_key
            order['Action'] = 'Amend'

            ord_extended = order['Extended']
            sec_country = get_sec_country(amend_security)
            sec_name = amend_security.get('Name')
            sec_ccy = amend_security.get('Ccy')

            if not sec_country:
                logger.error(
                    'Security {} has no country.'.format(amend_key))
            else:
                if not ord_extended.get('SecCountry'):
                    ord_extended['SecCountry'] = sec_country

            if not sec_name:
                logger.error(
                    'Security {} has no name.'.format(amend_key))
            else:
                if not ord_extended.get('SecDescription'):
                    ord_extended['SecDescription'] = sec_name

            if not sec_ccy:
                logger.error(
                    'Security {} has no currency.'.format(amend_key))
            else:
                if not ord_extended.get('Currency'):
                    ord_extended['Currency'] = sec_ccy

                if not ord_extended.get('CcySettlement'):
                    ord_extended['CcySettlement'] = sec_ccy

            order['Username'] = 'System'
            dc.order.post(order)
            logger.info(
                'Order {} has changed symbol.'.format(order['Id']))


# Invalidate all the event records of the same security and event type

def invalidate_events(sec_key, event_type):
    upcoming_events = dc.calendar_event.get_calendar_events(
        {'Security': sec_key, 'EventType': event_type, 'Status': 1})
    logger.info('Invalidate {} {} events of security {}'.format(
        len(upcoming_events), event_type, sec_key))
    for ue in upcoming_events:
        # Set event records with status 2 Inactive
        ue['Status'] = 2
        dc.calendar_event.update_event(ue)


def process_event_booking_records(event_booking_records, new_sec, old_sec):
    if event_booking_records:
        is_new_sec = False if old_sec else True

        event_type = event_booking_records[0]['EventType']
        sec_key = new_sec['Key']

        if not is_new_sec:
            logger.info(
                'Security {} is an amended security. Need to invalidate the booked event records'.format(sec_key))
            invalidate_events(sec_key, event_type)

        logger.info('{} {} new records of security {}'.format(
            len(event_booking_records), event_type, sec_key))
        for event in event_booking_records:
            # TODO: testing
            dc.calendar_event.insert_event(event)


def process_security_bond(new_security, old_security={}):
    bond_events_manager = BondEventsManager(dc, logger)
    # 1 coupons
    if new_security.get('CouponDateList'):
        events_coupon = bond_events_manager.get_events_coupon(
            new_security, old_security)
        process_event_booking_records(
            events_coupon, new_security, old_security)
    else:
        coupon_schedule = bond_events_manager.get_coupon_schedules(
            new_security)
        if coupon_schedule:
            gekko_sec = dc.sec_master.get_security_by_key(new_security['Key'])
            gekko_sec['CouponDateList'] = coupon_schedule
            dc.sec_master.save_security(gekko_sec)

    # 2 maturity
    events_maturity = bond_events_manager.get_events_maturity(
        new_security, old_security)
    process_event_booking_records(events_maturity, new_security, old_security)

    # 3 put/call dates
    events_put = bond_events_manager.get_events_callable_puttable(
        new_security, old_security, 'Put')
    process_event_booking_records(events_put, new_security, old_security)
    events_call = bond_events_manager.get_events_callable_puttable(
        new_security, old_security, 'Call')
    process_event_booking_records(events_call, new_security, old_security)

    # 4 conversion
    if new_security.get('_type') == 'ConvertibleBond':
        logger.info('Bond security {} is convertible bond.'.format(
            new_security['Key']))
        events_conversion = bond_events_manager.get_events_conversion(
            new_security, old_security)
        process_event_booking_records(
            events_conversion, new_security, old_security)


def process_fx_forward(new_security, old_security={}):
    fx_forward_events_manager = FxForwardEventsManager(dc, logger)
    # fx forward ndf expiry
    if new_security.get('FixingDate'):
        logger.info('Fx forward {} is fx ndf')
        events_ndf_expiry = fx_forward_events_manager.get_events_ndf_expiry(
            new_security, old_security)
        process_event_booking_records(
            events_ndf_expiry, new_security, old_security)
    else:
        # fx forward expiry
        events_expiry = fx_forward_events_manager.get_events_expiry(
            new_security, old_security)
        process_event_booking_records(
            events_expiry, new_security, old_security)


def process_security_futures(new_security, old_security={}):
    futures_events_manager = FuturesEventsManager(dc, logger)
    # expiry
    events_expiry = futures_events_manager.get_events_expiry(
        new_security, old_security)
    process_event_booking_records(events_expiry, new_security, old_security)


def process_equity_options(new_security, old_security={}):
    equity_options_manager = EquityOptionsEventsManager(dc, logger)
    # expiry
    events_expiry = equity_options_manager.get_events_expiry(
        new_security, old_security)
    process_event_booking_records(events_expiry, new_security, old_security)


def process_security_cds(new_security, old_security={}):
    cds_events_manager = CDSEventsManager(dc, logger)
    # 1 coupons
    if new_security.get('CouponDateList'):
        events_coupon = cds_events_manager.get_events_coupon(
            new_security, old_security)
        process_event_booking_records(
            events_coupon, new_security, old_security)
    else:
        coupon_schedule = cds_events_manager.get_coupon_schedules(
            new_security)
        if coupon_schedule:
            gekko_sec = dc.sec_master.get_security_by_key(new_security['Key'])
            gekko_sec['CouponDateList'] = coupon_schedule
            dc.sec_master.save_security(gekko_sec)

    # 2 maturity
    events_maturity = cds_events_manager.get_events_maturity(
        new_security, old_security)
    process_event_booking_records(events_maturity, new_security, old_security)


def lambda_handler(event, context):
    print(event)
    m = json.loads(event['Records'][0]['Sns']['Message'])
    new_security = m['Item']
    old_security = m.get('PrevItem', {})
    security_type = new_security['_type']

    if security_type in ['Bond', 'ConvertibleBond']:
        if old_security:
            # expecting the Status will be removed from the new security
            new_security_status = new_security.get('Status')
            old_security_status = old_security.get('Status')

            if old_security_status == 'Pending' != new_security_status:
                message_key = new_security['Key']
                amend_security = dc.sec_master.get_security_by_key(message_key)
                amend_key = update_bond_key(message_key, amend_security)
                if amend_key:
                    update_bond_orders_symbol(
                        message_key, amend_key, amend_security)
                else:
                    logger.info(
                        'Security {} does not change key'.format(message_key))
                return
        process_security_bond(new_security, old_security)
    elif security_type == 'FxForward':
        process_fx_forward(new_security, old_security)
    elif security_type == 'Futures':
        process_security_futures(new_security, old_security)
    elif security_type == 'EquityOption':
        process_equity_options(new_security, old_security)
    elif security_type == 'CDS':
        process_security_cds(new_security, old_security)