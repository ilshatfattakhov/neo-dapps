"""
Insurance dApp
===================================

This dApp is an example of an insurance contract that pays out in case of
an external event, that is signalled by an oracle.

It has the following entities: the owner, customer, insurer (can be the owner
or a third party) and the oracle. The owner can initialize an exchange.
The oracle signals the result of the event, after which the customer,
insurer or owner can claim to pay out the insured amount/premium.
The oracle will also be paid for its services/costs.

In case the oracle fails to signal the result, the owner can refund both the
customer and insurer with the 'refundAll' operation.

"""

from boa.interop.Neo.Runtime import Log, Notify, GetTrigger, CheckWitness
from boa.interop.Neo.Blockchain import GetHeight, GetHeader
from boa.interop.Neo.Header import GetTimestamp
from boa.interop.Neo.Action import RegisterAction
from boa.interop.Neo.TriggerType import Application, Verification
from boa.interop.Neo.Storage import GetContext, Get, Put, Delete
from boa.builtins import list

# -------------------------------------------
# DAPP SETTINGS
# -------------------------------------------

OWNER = b'#\xba\'\x03\xc52c\xe8\xd6\xe5"\xdc2 39\xdc\xd8\xee\xe9'
DEPOSIT_WALLET = b'ZPH\xa84\xf1Y\x14\xf1\x91b\x95\x85\xd1\xba\x96\x81\x99\x1f\xd3'
QUARK_WALLET = b'\xa9u\xfcZ\xb9\xa2\x8c\xeey\xf6\x92\xeeG-\x1a\xf8T\xb5\xbcH'
# Script hash of the token owner


# -------------------------------------------
# Events
# -------------------------------------------
#
DispatchOrderEvent = RegisterAction('order-add', 'order_key')
DispatchExchangeEvent = RegisterAction('exchange', 'order_key')
DispatchResultNoticeEvent = RegisterAction('result-notice', 'order_key', 'weather_param', 'oracle_cost')
DispatchClaimEvent = RegisterAction('pay-out', 'order_key')
DispatchTransferEvent = RegisterAction('transfer', 'from', 'to', 'amount')
DispatchRefundAllEvent = RegisterAction('refund-all', 'order_key')
DispatchDeleteOrderEvent = RegisterAction('order-delete', 'order_key')


def Main(operation, args):
    """
    This is the main entry point for the dApp
    :param operation: the operation to be performed
    :type operation: str
    :param args: an optional list of arguments
    :type args: list
    :return: indicating the successful execution of the dApp
    :rtype: bool
    """
    trigger = GetTrigger()

    if trigger == Verification():

        # if the script that sent this is the owner
        # we allow the spend
        is_owner = CheckWitness(OWNER)

        if is_owner:
            return True

        return False

    elif trigger == Application():

        if operation == 'deploy':
            if len(args) == 6:
                dapp_name = args[0]
                oracle = args[1]
                time_margin = args[2]
                min_time = args[3]
                max_time = args[4]
                fee = args[5]
                d = Deploy(dapp_name, oracle, time_margin, min_time, max_time)

                Log("Dapp deployed")
                return d
            else:
                return False

        elif operation == 'name':
            context = GetContext()
            n = Get(context, 'dapp_name')
            return n

        elif operation == 'updateName':
            if len(args) == 1:
                new_name = args[0]
                n = UpdateName(new_name)
                Log("Name updated")
                return n

            else:
                return False

        elif operation == 'oracle':
            context = GetContext()
            o = Get(context, 'oracle')

            return o

        elif operation == 'updateOracle':
            if len(args) == 1:
                new_oracle = args[0]
                o = UpdateOracle(new_oracle)
                Log("Oracle updated")
                return o

            else:
                return False

        elif operation == 'time_margin':
            context = GetContext()
            time_margin = Get(context, 'time_margin')

            return time_margin

        elif operation == 'min_time':
            context = GetContext()
            min_time = Get(context, 'min_time')

            return min_time

        elif operation == 'max_time':
            context = GetContext()
            max_time = Get(context, 'max_time')

            return max_time

        elif operation == 'updateTimeLimits':
            if len(args) == 2:
                time_variable = args[0]
                value = args[1]
                t = UpdateTimeLimits(time_variable, value)
                Log("Time limits updated")
                return t

            else:
                return False

        elif operation == 'order':
            if len(args) == 13:
                # order_key = args[0]
                # timestamp = args[1]
                # src_currency = args[2]
                # dst_currency = args[3]
                # expire = args[4]
                # course = args[5]
                # amount = args[6]
                # src_wallet = args[7]
                # dst_wallet = args[8]
                # deposit_wallet = args[9]
                # dapp_name = args[11]
                # fee = args[12]

                o = Order(order_key, timestamp, src_currency, dst_currency, expire, course, amount, src_wallet,
                          dst_wallet, deposit_wallet, dapp_name, fee)

                # TODO check if exchanges match
                Log("order added!")
                return o

            else:
                return False

        elif operation == 'resultNotice':
            if len(args) == 3:
                order_key = args[0]
                weather_param = args[1]
                oracle_cost = args[2]
                return ResultNotice(order_key, weather_param, oracle_cost)

            else:
                return False

        elif operation == 'deleteOrder':
            if len(args) == 1:
                order_key = args[0]
                return DeleteOrder(order_key)

            else:
                return False
        elif operation == 'match':
            if len(args) == 1:
                order_key = args[0]
                # TODO call match method
                return DoMatch(order_key)

            else:
                return False

        result = 'unknown operation'

        return result

    return False


def Deploy(dapp_name, oracle, time_margin, min_time, max_time):
    """
    Method for the dApp owner initiate settings in storage

    :param dapp_name: name of the dapp
    :type dapp_name: str

    :param oracle: oracle that is used
    :type oracle: bytearray

    :param time_margin: time margin in seconds
    :type time_margin: int

    :param min_time: minimum time until the datetime of the event in seconds
    :type min_time: int

    :param max_time: max_time until the datetime of the event in seconds
    :type max_time: int

    :return: whether the update succeeded
    :rtype: bool
    """

    # if not CheckWitness(OWNER):
    #     Log("Must be owner to deploy dApp")
    #     return False

    context = GetContext()
    Put(context, 'dapp_name', dapp_name)
    Put(context, 'oracle', oracle)

    if time_margin < 0:
        Log("time_margin must be positive")
        return False

    Put(context, 'time_margin', time_margin)

    if min_time < 3600 + time_margin:
        Log("min_time must be greater than 3600 + time_margin")
        return False

    Put(context, 'min_time', min_time)

    if max_time <= (min_time + time_margin):
        Log("max_time must be greather than min_time + time_margin")
        return False

    Put(context, 'max_time', max_time)

    return True


def UpdateName(new_name):
    """
    Method for the dApp owner to update the dapp name

    :param new_name: new name of the dapp
    :type new_name: str

    :return: whether the update succeeded
    :rtype: bool
    """

    if not CheckWitness(OWNER):
        Log("Must be owner to update name")
        return False

    context = GetContext()
    Put(context, 'dapp_name', new_name)

    return True


def UpdateOracle(new_oracle):
    """
    Method for the dApp owner to update oracle that is used to signal events

    :param new_name: new oracle for the dapp
    :type new_name: bytearray

    :return: whether the update succeeded
    :rtype: bool
    """

    if not CheckWitness(OWNER):
        Log("Must be owner to update oracle")
        return False

    context = GetContext()
    Put(context, 'oracle', new_oracle)

    return True


def UpdateTimeLimits(time_variable, value):
    """
    Method for the dApp owner to update the time limits

    :param time_variable: the name of the time variable to change
    :type time_variable: str

    :param value: the value for the time variable to change in seconds
    :type value: int

    :return: whether the update succeeded
    :rtype: bool
    """

    if not CheckWitness(OWNER):
        Log("Must be owner to update time limits")
        return False

    if value < 0:
        Log("Time limit value must be positive")
        return False

    context = GetContext()

    if time_variable == 'time_margin':
        time_margin = value
        Put(context, 'time_margin', time_margin)

    elif time_variable == 'min_time':
        min_time = value
        Put(context, 'min_time', min_time)

    elif time_variable == 'max_time':
        max_time = value
        Put(context, 'max_time', max_time)

    else:
        Log("Time variable name not existing")
        return False

    return True

# TODO add oracle contract call
def GetCurrencyRate(currency):
    # url = 'https://api.coinmarketcap.com/v1/ticker/NEO/?convert=%s'%currency
    # r = requests.get(url)
    # r_json = r.json()
    # last_updated = r_json[0]['last_updated']
    # price_usd = r_json[0]['price_usd']
    # return last_updated, price_usd
    return 100

def Order(order_key, timestamp, src_currency, dst_currency, course, amount, src_wallet, dst_wallet, deposit_wallet, dapp_name, fee):
    """
    Method to create an order to change currencies

    :param order_key: unique identifier for the exchange
    :type order_key: str

    :param customer: customer party of the exchange
    :type customer: bytearray

    :param insurer: insurer party of the exchange
    :type insurer: bytearray

    :param location: location were the event occurs, typically a city
    :type location: str

    :param timestamp: timezone naive datetime of the day of the event
    :type timestamp: int

    :param amount: the insured amount of NEO
    :type amount: int

    :param premium: the amount of NEO to be paid as a premium to the insurer
    :type premium: int

    :param dapp_name: the name of the dApp
    :type dapp_name: str

    :param fee: the fee to be charged
    :type fee: int

    :return: whether the exchange was successful
    :rtype: bool
    """

    if not CheckWitness(OWNER):
        Log("Must be owner to add an exchange")
        return False

    # Check if amount is not zero or below
    if amount <= 0:
        Log("Exchange amount is zero or negative")
        return False

    # TODO add checks for wallets
    # TODO checks for expire
    # TODO add checks for course

    # Check if the contract is deployed
    context = GetContext()
    if not Get(context, dapp_name):
        Log("Must first deploy contract with the deploy operation")
        return False

    # Get timestamp of current block
    currentHeight = GetHeight()
    currentBlock = GetHeader(currentHeight)
    current_time = currentBlock.Timestamp
    # Compute timezone adjusted time
    timezone_timestamp = timestamp + (utc_offset * 3600)
    timezone_current_time = current_time + (utc_offset * 3600)

    # Get contract settings
    dapp_name = Get(context, 'dapp_name')
    oracle = Get(context, 'oracle')
    time_margin = Get(context, 'time_margin')
    min_time = Get(context, 'min_time')
    max_time = Get(context, 'max_time')

    # Check if timestamp is not out of boundaries
    if timezone_timestamp < (timezone_current_time + min_time - time_margin):
        Log("Datetime must be > 1 day ahead")
        return False

    elif timezone_timestamp > (timezone_current_time + max_time + time_margin):
        Log("Datetime must be < 30 days ahead")
        return False

    status = 'initialized'

    # Set place holder variables
    weather_param = 0
    oracle_cost = 0

    # TODO deposit value depends on oracle that returns a deposit amount depends on source_currency
    deposit_amount = GetCurrencyRate(src_currency)[1] * amount
    d = DoTransfer(QUARK_WALLET, DEPOSIT_WALLET, deposit_amount)

    order_data = [timestamp, utc_offset, expire, src_currency, dst_currency, course, amount, src_wallet, dst_wallet,
                  deposit_wallet, deposit_amount, fee, oracle, time_margin, min_time, max_time, status, oracle_cost]

    if d == True:
        Put(context, order_key, order_data)
        DispatchOrderEvent(order_key)
        return True

    return False


def ResultNotice(order_key, funds_transfered, oracle_cost):
    """
    Method to signal results by oracle

    :param order_key: the key of the exchange
    :type order_key: bytearray

    :param funds_transfered: funds on external blockchain transfered
    :type weather_param: int

    :param oracle_cost: costs made by the oracle to do this assignment
    :type oracle_cost: int

    :return: whether a pay out to the customer is done
    :rtype: bool
    """

    # Check if the method is triggered by the oracle for this exchange
    context = GetContext()
    order_data = Get(context, order_key)
    oracle = order_data[8]

    if not CheckWitness(oracle):
        Log("Must be oracle to notice results")
        return False

    timestamp = order_data[3]
    utc_offset = order_data[4]
    status = order_data[12]

    if not status == 'initialized':
        Log("Contract has incorrect status to do a result notice")
        return False

    order_data[12] = 'funds-transfered' # order status
    order_data[13] = funds_transfered
    order_data[14] = oracle_cost

    # Get timestamp of current block
    currentHeight = GetHeight()
    currentBlock = GetHeader(currentHeight)
    current_time = currentBlock.Timestamp
    Put(context, order_key, order_data)

    timezone_timestamp = timestamp + (3600 * utc_offset)
    timezone_current_time = current_time + (3600 * utc_offset)

    if timezone_current_time < timezone_timestamp:
        Log("Datetime of result notice is lower than agreed datetime")
        return False
    else:
        DispatchResultNoticeEvent(order_key, funds_transfered, oracle_cost)
        return True


# def Claim(order_key):
#     """
#     Method to handle the pay out
#
#     :param order_key: the key of the exchange
#     :type order_key: bytearray
#
#     :return: whether a pay out to the customer is done
#     :rtype: bool
#     """
#
#     context = GetContext()
#     exchange_data = Get(context, order_key)
#     customer = exchange_data[0]
#     insurer = exchange_data[1]
#     oracle = exchange_data[8]
#     status = exchange_data[12]
#     amount = exchange_data[5]
#     premium = exchange_data[6]
#     fee = exchange_data[7]
#     weather_param = exchange_data[13]
#     oracle_cost = exchange_data[14]
#
#     # Check if the pay out is triggered by the owner, customer, or insurer.
#     valid_witness = False
#
#     if CheckWitness(OWNER):
#         valid_witness = True
#
#     elif CheckWitness(customer):
#         valid_witness = True
#
#     elif CheckWitness(insurer):
#         valid_witness = True
#
#     if not valid_witness:
#         Log("Must be owner, customer or insurer to claim")
#         return False
#
#     # Check whether this contract has the right status to do a claim
#     if status == 'initialized':
#         Log("Status must be result-noticed to be able to do a claim")
#         return False
#
#     elif status == 'claimed':
#         Log("Contract pay out is already claimed")
#         return False
#
#     elif status == 'refunded':
#         Log("Contract is already refunded")
#         return False
#
#     net_premium = premium - fee
#
#     if weather_param >= THRESHOLD:
#         Notify("Day was sunny, no pay out to customer")
#         DoTransfer(OWNER, insurer, net_premium)
#         DispatchTransferEvent(OWNER, insurer, net_premium)
#         return False
#
#     elif weather_param < THRESHOLD:
#         Notify("Day was not sunny, pay out insured amount to customer")
#         DoTransfer(OWNER, insurer, net_premium)
#         DispatchTransferEvent(OWNER, insurer, net_premium)
#         DoTransfer(OWNER, customer, amount)
#         DispatchTransferEvent(OWNER, customer, amount)
#
#     DoTransfer(OWNER, oracle, oracle_cost)
#     DispatchTransferEvent(OWNER, oracle, oracle_cost)
#
#     exchange_data[12] = 'claimed'
#     Put(context, order_key, exchange_data)
#     DispatchClaimEvent(order_key)
#
#     return True
#
#
def DoTransfer(sender, receiver, amount):
    """
    Method to transfer tokens from one account to another

    :param sender: the address to transfer from
    :type sender: bytearray

    :param receiver: the address to transfer to
    :type receiver: bytearray

    :param amount: the amount of tokens to transfer
    :type amount: int

    :return: whether the transfer was successful
    :rtype: bool

    """

    if amount <= 0:
        Log("Cannot transfer negative amount")
        return False

    from_is_sender = CheckWitness(sender)

    if not from_is_sender:
        Log("Not owner of funds to be transferred")
        return False

    if sender == receiver:
        Log("Sending funds to self")
        return True

    context = GetContext()
    from_val = Get(context, sender)

    if from_val < amount:
        Log("Insufficient funds to transfer")
        return False

    if from_val == amount:
        Delete(context, sender)

    else:
        difference = from_val - amount
        Put(context, sender, difference)

    to_value = Get(context, receiver)

    to_total = to_value + amount

    Put(context, receiver, to_total)
    DispatchTransferEvent(sender, receiver, amount)

    return True


def DeleteOrder(order_key):
    """
    Method for the dApp owner to delete claimed or refunded exchanges

    :param order_key: order_key
    :type order_key: str

    :return: whether the deletion succeeded
    :rtype: bool
    """

    if not CheckWitness(OWNER):
        Log("Must be owner to delete an exchange")
        return False

    context = GetContext()
    order_data = Get(context, order_key)
    status = order_data[12]

    if status == 'claimed':
        Delete(context, order_key)
        DispatchDeleteOrderEvent(order_key)

    elif status == 'refunded':
        Delete(context, order_key)
        DispatchDeleteOrderEvent(order_key)

    return False


def DoMatch(src_order_key, dst_order_key, course):
    """
    Method for the dApp owner to match exchange requests
    Input data: all not matched requests.
    Output data: matched pairs
    """

    # Check if the method is triggered by the oracle for this exchange
    context = GetContext()
    src_order_data = Get(context, src_order_key)
    oracle = src_order_data[12]
    src_deposit_amount = src_order_data[10]

    dst_order_data = Get(context, dst_order_key)
    dst_deposit_amount = dst_order_data[10]

    if not CheckWitness(oracle):
        Log("Must be oracle to notice results")
        return False

    # refund deposit of the source wallet
    t1 = DoTransfer(DEPOSIT_WALLET, QUARK_WALLET, src_deposit_amount)

    # refund deposit of the source wallet
    t2 = DoTransfer(DEPOSIT_WALLET, QUARK_WALLET, dst_deposit_amount)
    if t1 and t2:
        DispatchExchangeEvent(src_order_key)
        DispatchExchangeEvent(dst_order_key)
        return True
    return False


