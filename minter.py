import random
from loguru import logger
import csv
import asyncio

from config import shuffle, mode, amount_wallets_in_batch, number
from utils import mint


async def write_to_csv(key, address, result):
    with open('result.csv', 'a', newline='') as file:
        writer = csv.writer(file)

        if file.tell() == 0:
            writer.writerow(['key', 'address', 'result'])

        writer.writerow([key, address, result])

async def main():
    with open("keys.txt", "r") as f:
        keys = [row.strip() for row in f]
    print(f'\n{" " * 32}автор - https://t.me/iliocka{" " * 32}\n')
    if shuffle:
        random.shuffle(keys)
    logger.info(f'Начинаю работу на {len(keys)} кошельках...')

    batches = [keys[i:i + amount_wallets_in_batch] for i in range(0, len(keys), amount_wallets_in_batch)]

    tasks = []
    for batch in batches:
        for key in batch:
            tasks.append(mint(key, mode, number))
        res = await asyncio.gather(*tasks)

        for res_ in res:
            adress, result = res_
            await write_to_csv(key, adress, result)

        tasks = []

    logger.success(f'Успешно сделал {len(keys)} кошельков...')
    logger.success(f'muнетинг закончен...')
    print(f'\n{" " * 32}автор - https://t.me/iliocka{" " * 32}\n')
    print(f'\n{" " * 32}donate - EVM 0xFD6594D11b13C6b1756E328cc13aC26742dBa868{" " * 32}\n')
    print(f'\n{" " * 32}donate - trc20 TMmL915TX2CAPkh9SgF31U4Trr32NStRBp{" " * 32}\n')

if __name__ == '__main__':
    asyncio.run(main())
