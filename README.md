# Coinbase Execution Algorithm

##### Please use with caution!
*Note: this algorithm is still being worked on and may encounter some unexpected bugs*
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Description
A VWAP algorithm that attempts to beat the VWAP price (i.e tries to get a price for you that is better than what the market is executing at)
The following user parameters must be defined:
- ```product_id``` - the ticker you want to trade (i.e BTC-USD)
- ```side``` - either 'buy' or 'sell'
- ```hours``` - how many hours you want the execute the order over
- ```orderqty``` - size (i.e 1 BTC)
- ```limit``` - a hard limit on all orders
When running the code, the following inputs are entered via the user from the command prompt

## Getting Started
It's pretty simple, you'll need to get an authenticated client setup first on your Coinbase Pro account so you're "hooked-in" appropriately.
- The ```authenticated_client.py``` script is where you'll need to put your relevant keys and is a nice & easy way to switch between virtual trading and live trading. If you need help on how to do this, please refer to the following repo (https://github.com/danpaquin/coinbasepro-python)
- Now run ```python coinbase_algo.py```


## Credits
Credit to the following repo detailing an easy way to interface with the [Coinbase API via Python] (https://github.com/danpaquin/coinbasepro-python)

Credit to this awesome dude Andrés Berejnoi, check out his [YouTube Channel] (https://www.youtube.com/channel/UCvPE2QkDtQnl652gAXNOrgg)
