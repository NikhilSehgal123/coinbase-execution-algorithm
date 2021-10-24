import cbpro
import numpy as np
import datetime
import dateutil.parser
from authenticated_client import auth_client, LIVE

# Product to trade
product_id = 'BTC-USD'
side = input('Enter side [buy/sell] ')
hours = input('Enter hours to execute over [i.e 2] ')
orderqty = input('Enter quantity in BTC [i.e 1] ')
limit = input('Enter limit [i.e 65000 OR 0 if no limit] ')


# Init global values to store L1 orderbook information
current_last = 0
current_bid_price = 0
current_ask_price = 0
current_spread = 0
current_volume = 0


# Initiate empty arrays to track volume & price
volume_array = []
price_array = []


# Define the websocket to connect to
class TextWebsocketClient(cbpro.WebsocketClient):
    def on_open(self):
        if LIVE:
            self.url = 'wss://ws-feed.pro.coinbase.com'
        else:
            self.url = 'wss://ws-feed.pro.coinbase.com' # 'wss://ws-feed-public.sandbox.pro.coinbase.com'
      
        self.message_count = 0
        self.initial_date = datetime.datetime.now()
        self.vwap_algo = VWAP_Execution_Algorithm(
                                                side=side,
                                                hours=hours,
                                                orderqty=orderqty,
                                                limit=limit,
                                                )
    
    def on_message(self,msg):

        self.message_count += 1
        msg_type = msg.get('type',None)
        if msg_type == 'ticker':
            time_val =   msg.get('time',('-'*27))
            price_val =  msg.get('price',None)
            bid_val =    msg.get('best_bid', None)
            ask_val =    msg.get('best_ask', None)
            volume =     msg.get('last_size', None)
            
            if price_val is not None:
                price_val = float(price_val)
            if bid_val is not None:
                bid_val = float(bid_val)
            if ask_val is not None:
                ask_val = float(ask_val)
                
            spread_val = ask_val - bid_val
            product_id = msg.get('product_id',None)

            print('Product %s | Time_val %s | Price %s | Bid %s | Ask %s | Volume %s' % (product_id, time_val, price_val, bid_val, ask_val, volume))
            
            # Gathering global variables
            volume_array.append(volume)
            price_array.append(price_val)

            # ----------------------------------------------------------------
            # ---------------- VWAP EXECUTION ALGO ---------------------------
            # ----------------------------------------------------------------

            # Updating info in the VWAP class
            self.vwap_algo.update_info(open=None, 
                                    bid=bid_val, 
                                    ask=ask_val, 
                                    last=price_val, 
                                    spread=spread_val)
            # Run the executor
            self.vwap_algo.Execute()

    
    def on_close(self):
        print(f"<---Websocket connection closed--->\n\tTotal messages: {self.message_count}")


# VWAP Execution Algorithm
class VWAP_Execution_Algorithm():
    
    def __init__(self, side, hours, orderqty, limit):
        # Initiate some useful variables that we'll need to monitor
        self.open_positions = 0
        self.best_bid = 0
        self.best_ask = 0
        self.last_trade = 0
        self.spread = 0
        self.account_balance = 0
        self.urgency = 0
        self.vwap = 0

        # Initiate user parameters
        self.side = side
        self.hours = float(hours)
        self.size = float(orderqty) #Bitcoin size
        self.limit = float(limit)
        self.min_size = self.size*0.01

        # Tracking our fills
        self.fills = []
        self.QuantityExecuted = 0
        self.average_executed_price = 0
        self.average_fees = 0

        # Tracking how much size we have exposed
        self.exposed_size = 0

        # Tracking our orders
        self.orders = []

        # Get current time
        self.start_time = datetime.datetime.now()
        self.start_timestamp = datetime.datetime.timestamp(self.start_time)
        print(' ----------------> Schedule starting at %s' % (self.start_time))

        # Get end time
        self.end_timestamp = self.start_timestamp + (self.hours * 3600)
        self.end_time = datetime.datetime.fromtimestamp(self.end_timestamp)
        print(' ----------------> Schedule ending at %s' % (self.end_time))
        
    def update_info(self, open, bid, ask, last, spread):
        self.open_positions = open
        self.best_bid = bid
        self.best_ask = ask
        self.last_trade = last
        self.spread = spread
        self.account_balance = 0
        self.calculate_vwap(volume_array, price_array)

        # Print some useful logging info
        print('\n')
        print('**************************************************************')
        print('************************* LOGGING ****************************')
        print('**************************************************************')
        print('\n')
        print('------------------------- FILLS INFO -------------------------')
        print('Average Executed Price = %s' % (self.average_executed_price))
        print('No. Of Fills So Far = %s' % (len(self.fills)))
        print('--------------------------------------------------------------')
        print('\n')
    
    def calculate_vwap(self, volume, price):
        # Here we are calculating the current Intraday VWAP price based on incoming volume & price data Σ PiVi / Σ Vi
        # @param volume = volume array
        # @param price = price array
        # @return vwap price

        volume = np.asarray(volume).astype(float)
        price = np.asarray(price).astype(float)
        assert(len(volume) == len(price))

        if len(volume) > 1:
            current_vwap = np.sum(price * volume)/np.sum(volume)
            self.vwap = current_vwap
           
            return current_vwap
        else:
            return

    def time_complete(self):
        current_time = datetime.datetime.now()
        current_timestamp = datetime.datetime.timestamp(current_time)
        time_elapsed = (current_timestamp - self.start_timestamp)/(self.end_timestamp - self.start_timestamp) * 100
        
        return time_elapsed

    def Execute(self):
        'Execution model that attempts to beat the vwap price'

        pct_to_complete = self.time_complete()

        # total_filled_size, remaining_quantity, order_pct_complete = self.GetRemainingQuantity()

        should_have_executed = np.round(pct_to_complete/100*self.size,decimals=3)
        executed_so_far = self.QuantityExecuted
        execution_slice = np.round(should_have_executed - executed_so_far - self.exposed_size,decimals=7) # Need to round this up or you'll get into a sizing issue

        # Print some useful execution logs info
        print('------------------------- EXECUTION INFO -------------------------')
        print('Order progress --------------------------------> %d/100' %(pct_to_complete))
        print('Order Qty = %s' % (self.size))
        print('Should have executed so far = %s' % (should_have_executed))
        print('Executed so far = %s' % (self.QuantityExecuted))
        print('Exposed size in the market = %s' % (self.exposed_size))
        print('\n')
        print('Order slice queuing up = %s' % (execution_slice))
        print('Min execution size set to = %s' % (self.min_size))
        print('-------------------------------------------------------------------')
        print('\n')
        print('------------------------- ORDER BOOK INFO -------------------------')
        print('VWAP Price = %s' % (self.vwap))
        print('L1 Order Book -----> Bid %s | Ask %s' % (self.best_bid, self.best_ask))
        print('-------------------------------------------------------------------')
        print('\n')

        
        # Check we are not going over
        if (pct_to_complete <= 100) & (executed_so_far < self.size):
            
            # Check that the order size is above our min size
            if execution_slice < self.min_size:
                print('[MIN_SIZE_BLOCK] Minimum size blocker kicking in | Currently set to %s' % (self.min_size))
            elif execution_slice > self.min_size:
                # Check if the price is favorable
                if self.PriceIsFavorable() and self.limit == 0:
                    order = auth_client.place_market_order(product_id=product_id,
                                            side='buy',
                                            size=execution_slice)
                    print(order)
                    self.orders.append(order)
                    # Update the fills post execution
                    self.UpdateFills()
                              
                elif self.PriceIsFavorable() and (self.limit != 0):
                    order = auth_client.place_limit_order(product_id=product_id,
                                            side='buy',
                                            size=execution_slice,
                                            price=self.limit)
                    print(order)
                    self.orders.append(order)
                    # Update the fills post execution
                    self.UpdateFills()
               
        elif (pct_to_complete > 100) & (executed_so_far < self.size):
            remaining_quantity = np.round(self.size - executed_so_far,decimals=4)
            print('------------------------- ORDER SUMMARY -------------------------')
            print('Executed = %s' % (self.QuantityExecuted))
            print('Average Executed Price = %s' % (self.average_executed_price))
            print('Remaining quantity = %s ------> You can finish this off manually on Coinbase Pro' % (remaining_quantity))
            print('Now cancelling all open orders.....')
            print('----------------------------------------------------------------')
            print('\n')
            auth_client.cancel_all(product_id=product_id)
            raise ValueError('********************* \n [Order Complete] Current time has now passed the scheduled end time \n *********************')


    def PriceIsFavorable(self, threshold=3):
        """
        Checks if the price is more favourable than VWAP
        :param self
        :param threshold: a value in basis points of how passive to be vs VWAP
        :return: bool
        """
        
        if (self.side == 'buy') & (self.vwap != 0):
            if self.best_ask < self.vwap*(1-threshold/10000):
                print('--------------------->>> [BUY ORDER] Current ask is more favorable than VWAP')
                return True
            else:
                return False
        elif (self.side == 'sell') & (self.vwap != 0):
            if self.best_bid > self.vwap*((1+threshold/10000)):
                ('--------------------->>> [SELL ORDER] Current bid is more favorable than VWAP')
                return True
            else:
                return False
        else:
            return False
    

    def UpdateFills(self):
        'This function will be used to track all our fills so far'

        # Example of fill dictionary from Coinbase
        # {'created_at': '2021-05-21T06:32:21.912Z', 'trade_id': 29877009, 'product_id': 'BTC-GBP', 
        # 'order_id': '1b7f96a9-95da-4511-b6d2-a4b18829742e', 'user_id': '6097b5f91b6ace17ba390d66', 
        # 'profile_id': '4a687ef0-818f-4475-826c-c2e9585a106c', 'liquidity': 'T', 'price': '39844.21000000', 
        # 'size': '1.00000000', 'fee': '199.2210500000000000', 'side': 'buy', 'settled': True, 'usd_volume': '39844.2100000000000000'}

        # Retrieve all the fills so far
        self.fills = []
        fills = auth_client.get_fills(product_id=product_id)
        for fill in fills:
            fill_time = fill['created_at']
            fill_time = dateutil.parser.isoparse(fill_time)
            fill_timestamp = datetime.datetime.timestamp(fill_time)
            if fill_timestamp > self.start_timestamp:
                self.fills.append(fill)
        
        # Update any exposed positions
        self.CheckOpenOrders()
        
        # Update the average executed price
        self.AverageExecutedPrice()


    def CheckOpenOrders(self):
        
        open_orders_array = []

        open_orders = auth_client.get_orders()
        for o in open_orders:
            if o['filled_size'] == '0':
                open_orders_array.append(o['size'])
        
        self.exposed_size = np.sum(np.asarray(open_orders_array).astype(float))


    def AverageExecutedPrice(self):
        filled_prices = []
        filled_size = []

        for fill in self.fills:
            filled_prices.append(fill['price'])
            filled_size.append(fill['size'])
        
        # Force arrays into floats
        filled_prices = np.asarray(filled_prices).astype(float)
        filled_size = np.asarray(filled_size).astype(float)
        self.QuantityExecuted = np.sum(filled_size)

        # Calculate AVG executed price so far
        self.average_executed_price = np.sum(filled_prices*filled_size)/np.sum(filled_size)


    def GetRemainingQuantity(self):
        'Gets the remaining quantity left from the order'

        filled_size = []

        for fill in self.fills:
            filled_size.append(fill.size)
        
        total_filled_size = np.sum(np.asarray(filled_size).astype(float))
        remaining_quantity = self.size - total_filled_size
        pct_complete = total_filled_size/self.size * 100

        return total_filled_size, remaining_quantity, pct_complete


if __name__ == '__main__':

    # ------------------------ MAIN ------------------------ #
    auth_client.cancel_all(product_id=product_id) # Make sure there is no existing orders in the market
    stream = TextWebsocketClient(products=[product_id],channels=['ticker'])
    stream.start()



    
    


 
