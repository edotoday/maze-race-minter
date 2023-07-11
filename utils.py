import random
import time
from web3 import Web3
from web3.eth import AsyncEth
import asyncio
from loguru import logger
from eth_abi import *

from config import delay

async def check_status_tx(address, w3, tx_hash):
    logger.info(
        f'{address} - жду подтверждения транзакции  https://explorer.zksync.io/tx/{w3.to_hex(tx_hash)}...')

    start_time = int(time.time())
    while True:
        current_time = int(time.time())
        if current_time >= start_time + 100:
            logger.info(
                f'{address} - транзакция не подтвердилась за 100 cекунд, начинаю повторную отправку...')
            return 0
        try:
            status = (await w3.eth.get_transaction_receipt(tx_hash))['status']
            if status == 1:
                return status
            await asyncio.sleep(1)
        except Exception as error:
            await asyncio.sleep(1)


async def sleep_indicator(address, secs):
    logger.info(f'{address} - жду {secs} секунд...')
    await asyncio.sleep(secs)


async def mint(key, mode, number=0):
    w3 = Web3(Web3.AsyncHTTPProvider('https://rpc.ankr.com/zksync_era'), modules={'eth': (AsyncEth,)}, middlewares=[])
    account = w3.eth.account.from_key(key)
    address = account.address
    mint_data = '0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000001a0000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
    if mode == 'all':
        datas = []
        for num in range(5):
            data = '0x57bc3d78' + encode(['address', 'uint8'], [address, num]).hex() + mint_data
            datas.append(data)
    if mode == 'exact':
        datas = []
        data = '0x57bc3d78' + encode(['address', 'uint8'], [address, number]).hex() + mint_data
        datas.append(data)

    if mode == 'final':
        datas = []
        data = f'0x57bc3d78000000000000000000000000{address[2:]}00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000001a0000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
        datas.append(data)
    for n, data in enumerate(datas):
        try:
            nonce = await w3.eth.get_transaction_count(address)
            tx = {
                'from': address,
                'to': Web3.to_checksum_address('0x54948AF9D4220aCee7aA5340C818865F6B313f96') if mode == 'final'
                else Web3.to_checksum_address('0x3F9931144300f5Feada137d7cfE74FAaa7eF6497'),
                'nonce': nonce,
                'value': 0,
                'data': data,
                'chainId': await w3.eth.chain_id,
                'maxFeePerGas': int(await w3.eth.gas_price * 1.1),
                'maxPriorityFeePerGas': await w3.eth.gas_price
            }
            tx['gas'] = int(await w3.eth.estimate_gas(tx) * 1.1)
            sign = account.sign_transaction(tx)
            hash_ = await w3.eth.send_raw_transaction(sign.rawTransaction)
            logger.info(f'{address} - пробую минтить...')
            status = await check_status_tx(address, w3, hash_)
            if status == 1:
                if mode == 'exact':
                    logger.success(f'{address} - успешно заминтил maze-race {number}...')
                else:
                    logger.success(f'{address} - успешно заминтил maze-race {n}...')
                await sleep_indicator(address, random.randint(delay[0], delay[1]))
                if mode == 'all':
                    if data != datas[-1]:
                        continue
                await sleep_indicator(address, random.randint(delay[0], delay[1]))
                return address, 'successfully minted'
            else:
                return await mint(key, mode, number)

        except Exception as e:
            error = str(e)
            if 'INTERNAL_ERROR: insufficient funds' in error or 'insufficient funds for gas' in error or 'gas required exceeds allowance' in error:
                logger.error(f'{address} - не хватает денег на газ, заканчиваю работу через 5 секунд...')
                await asyncio.sleep(5)
                return address, 'error'
            elif 'execution reverted: !Qty' in error:
                logger.error(f'{address} - уже заминчено...')
                if data == datas[-1]:
                    return address, 'already minted'
            else:
                logger.error(f'{address}- {e}')
                return address, 'error'
