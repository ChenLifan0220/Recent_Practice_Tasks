import pandas as pd
import numpy as np


def get_coupon_positions_df(positions_df):
    positions_df = positions_df.apply(
        lambda x: calculate_previous_next_coupon_date(x), axis=1)
    positions_df['PreviousCouponDateStr'] = positions_df.PreviousCouponDate
    positions_df.PreviousCouponDate = pd.to_datetime(
        positions_df.PreviousCouponDate, errors='coerce')
    positions_df.NextCouponDate = pd.to_datetime(
        positions_df.NextCouponDate, errors='coerce')

    positions_df = day_year_conventions(positions_df)
    positions_df['PeriodCoupon'] = (positions_df.Coupon / 100) * positions_df.Quantity * (
        positions_df.NextCouponDate - positions_df.PreviousCouponDate).dt.days \
        / positions_df.YearBase
    positions_df['DailyAccrual'] = (positions_df.Coupon / 100) * positions_df.Quantity * (positions_df.DaysPeriod / positions_df.YearBase) / (
        positions_df.RefDate - positions_df.PreviousCouponDate).dt.days
    return positions_df


def calculate_previous_next_coupon_date(sec):
    ref_date = sec['RefDate']
    format_coupon_dates = sec.get('CouponDateList')
    if pd.isna(format_coupon_dates) is True:
        sec['PreviousCouponDate'] = np.nan
        sec['NextCouponDate'] = np.nan
    else:
        coupon_date_list = pd.to_datetime(format_coupon_dates).tolist()
        coupon_date_list.insert(0, ref_date)
        coupon_date_list.sort()
        location = coupon_date_list.index(ref_date)

        sec['PreviousCouponDate'] = format_coupon_dates[location - 1]
        if location == len(format_coupon_dates):
            sec['NextCouponDate'] = np.nan
        else:
            sec['NextCouponDate'] = format_coupon_dates[location]
    return sec


def day_year_conventions(df):
    df['IsLeapYear'] = pd.to_datetime(df['RefDate']).dt.is_leap_year
    df.loc[df.IsLeapYear == True, 'YearDays'] = 366
    df.loc[df.IsLeapYear == False, 'YearDays'] = 365

    df.loc[:, 'YearBase'] = 360
    df.loc[df.DayCount == 'ACT/365', 'YearBase'] = 365
    df.loc[df.DayCount == 'NL/365', 'YearBase'] = 365
    df.loc[df.DayCount == 'ACT/ACT', 'YearBase'] = df.YearDays
    df.loc[df.DayCount == 'Actual', 'YearBase'] = df.YearDays

    df.loc[df.Frequency == 'Annual', 'CouponFrequency'] = 1
    df.loc[df.Frequency == 'SemiAnnual', 'CouponFrequency'] = 2
    df.loc[df.Frequency == 'TriAnnual', 'CouponFrequency'] = 3
    df.loc[df.Frequency == 'Quarterly', 'CouponFrequency'] = 4
    df.loc[df.Frequency == 'Monthly', 'CouponFrequency'] = 12
    df.loc[df.Frequency == 'Biweekly', 'CouponFrequency'] = 26
    df.loc[df.Frequency == 'Weekly', 'CouponFrequency'] = 52
    df.loc[df.Frequency == 'Daily', 'CouponFrequency'] = df.YearBase

    ref_date = pd.to_datetime(df['RefDate'])
    previous_coupon_date = pd.to_datetime(df['PreviousCouponDate'])
    df['DaysPeriod'] = (ref_date - previous_coupon_date).dt.days
    df.loc[(df.DayCount == '30E/360') & (ref_date.dt.day == 31) & (
        previous_coupon_date.dt.day != 31), 'DaysPeriod'] = (
        ref_date.dt.year - previous_coupon_date.dt.year) * 360 + \
        (ref_date.dt.month - previous_coupon_date.dt.month) * \
        30 + (30 - previous_coupon_date.dt.day)
    df.loc[(df.DayCount == '30E/360') & (ref_date.dt.day != 31) & (
        previous_coupon_date.dt.day == 31), 'DaysPeriod'] = (
        ref_date.dt.year - previous_coupon_date.dt.year) * 360 + \
        (ref_date.dt.month - previous_coupon_date.dt.month) * \
        30 + (ref_date.dt.day - 30)
    df.loc[(df.DayCount == '30E/360') & (ref_date.dt.day == 31) & (
        previous_coupon_date.dt.day == 31), 'DaysPeriod'] = (
        ref_date.dt.year - previous_coupon_date.dt.year) * 360 + \
        (ref_date.dt.month - previous_coupon_date.dt.month) * \
        30 + (30 - previous_coupon_date.dt.day)
    df.loc[df.DayCount == '30/360', 'DaysPeriod'] = (ref_date.dt.year - previous_coupon_date.dt.year) * 360 + \
        (ref_date.dt.month - previous_coupon_date.dt.month) * \
        30 + (ref_date.dt.day - previous_coupon_date.dt.day)
    df.loc[df.DayCount == 'ISMA-30/360', 'DaysPeriod'] = (ref_date.dt.year - previous_coupon_date.dt.year) * 360 + (
        ref_date.dt.month - previous_coupon_date.dt.month) * 30 + (ref_date.dt.day - previous_coupon_date.dt.day)
    return df