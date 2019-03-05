from datetime import datetime
 from datetime import timedelta
 import pandas as pd
 from messer import DataCube
 from packages.core.messercore.container import ContainerApp
 from packages.core.messercore.utils import get_datacube
 from services.LifeCycleTask.packages.BondTransactions import BondTransactions
 from services.LifeCycleTask.packages.CdsTransactions import CdsTransactions
 from services.LifeCycleTask.packages.FuturesTransactions import FuturesTransactions
 from services.LifeCycleTask.packages.EquityOptionTransactions import EquityOptionTransactions

  app = ContainerApp(__name__)
 dc = get_datacube(app)

 
  def get_position_df(ref_date_str):
     app.logger.info('Get open positions.')
     positions = dc.positions.get(ref_date_str,
                                  ['Strategy.Id', 'Strategy.ShortCode', 'CounterpartyAccount.Id',
                                   'CounterpartyAccount.ShortCode', 'TradeType'], None, None, False, 'MarketValue')

      positions = [pos for pos in positions if pos.get('Quantity') > 0]
     if not positions:
         app.logger.error(
             'No open position found on {}.'.format(positions))
     else:
         app.logger.info('{} positions found'.format(len(positions)))
     positions_df = pd.DataFrame(positions)
     positions_df['RefDate'] = pd.to_datetime(ref_date_str)
     return positions_df

 
  def get_security_positions(ref_date_str):
     positions_df = get_position_df(ref_date_str)
     if positions_df.empty:
         return positions_df

      app.logger.info('Get securities.')
     sec_keys = positions_df.Security.unique().tolist()
     securities = dc.sec_master.get_securities({'Key': sec_keys}, flatten=True)
     securities_df = pd.DataFrame(securities)
     securities_df.drop(
         columns=['TradeType', '_type', 'Multiplier', 'Underlying'], inplace=True)
     security_positions_df = pd.merge(
         positions_df, securities_df, left_on='Security', right_on='Key', how='left')

      return security_positions_df

 
  def run_eod_life_cycle_task(ref_date_str):
     transactions = []
     positions_df = get_security_positions(ref_date_str)
     handlers = [BondTransactions(dc), FuturesTransactions(
         dc), EquityOptionTransactions(dc), CdsTransactions(dc)]
     if not positions_df.empty:
         for handler in handlers:
             trans_positions_df = handler.get_positions(positions_df)
             if not trans_positions_df.empty:
                 transactions.extend(handler.get_transactions(
                     trans_positions_df, ref_date_str))

      for tran in transactions:
         result = dc.transaction.create(tran)

 
  def main(start_date_str, end_date_str):
     run_date = datetime.strptime(start_date_str, '%Y%m%d')
     end_date = datetime.strptime(end_date_str, '%Y%m%d')
     while run_date <= end_date:
         run_date_str = datetime.strftime(run_date, DataCube.DATE_JSON_FORMAT)
         run_eod_life_cycle_task(run_date_str)
         run_date = run_date + timedelta(days=1)

 
  if __name__ == '__main__':
     start_date_str = app.get_env('start_date')
     if not start_date_str:
         start_date_str = datetime.today().strftime('%Y%m%d')

      end_date_str = app.get_env('end_date')
     if not end_date_str:
         end_date_str = datetime.today().strftime('%Y%m%d')

      app.start(main, start_date_str=start_date_str, end_date_str=end_date_str)