import json
import asyncio
import os
import sys

# Patch execution pathing context for modular folder imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web3 import AsyncWeb3, AsyncHTTPProvider
from config.constants import RPC_URL, CONTRACT_ADDRESS, DECIMALS
from config.abis import FLASH_ARB_ABI, UNI_V3_POOL_ABI, VELO_V2_POOL_ABI

print(f"🔗 Connected to Private RPC: {RPC_URL[:35]}...")
w3 = AsyncWeb3(AsyncHTTPProvider(RPC_URL))

flash_arb_contract = w3.eth.contract(address=w3.to_checksum_address(CONTRACT_ADDRESS), abi=FLASH_ARB_ABI)
trade_lock = asyncio.Lock()

def load_tracked_pairs():
    with open("config/verified_tokens.json", "r") as f:
        return json.load(f)

def log_trade(message):
    print(message) 
    with open("logs/trades.log", "a") as f:
        f.write(message + "\n")

async def trigger_flash_execution(flash_pool, target_pool, velo_type, token_in, token_out, base_borrow_amount, zero_for_one, velo_stable, pair_name):
    log_trade(f"\n⚡ INITIATING FLASH SWAP ROUTE FOR {pair_name}...")
    try:
        private_key = os.getenv("PRIVATE_KEY")
        if not private_key: return

        ACCOUNT_ADDRESS = w3.eth.account.from_key(private_key).address

        eth_balance = await w3.eth.get_balance(ACCOUNT_ADDRESS)
        eth_balance_formatted = eth_balance / 10**18
        if eth_balance_formatted < 0.003: 
            log_trade(f"   🛑 STOP LOSS HIT: ETH balance is {eth_balance_formatted:.4f}. Halting execution.")
            return

        size_multipliers = [1.0, 0.5, 0.1]
        
        for multiplier in size_multipliers:
            borrow_amount = int(base_borrow_amount * multiplier)
            display_pct = int(multiplier * 100)
            
            try:
                nonce = await w3.eth.get_transaction_count(ACCOUNT_ADDRESS)

                tx_call = flash_arb_contract.functions.executeFlashSwap(
                    w3.to_checksum_address(flash_pool), w3.to_checksum_address(target_pool), 
                    velo_type, w3.to_checksum_address(token_in), w3.to_checksum_address(token_out), 
                    borrow_amount, zero_for_one, velo_stable
                )

                log_trade(f"   -> Simulating on-chain at {display_pct}% size...")
                estimated_gas = await asyncio.wait_for(
                    tx_call.estimate_gas({'from': ACCOUNT_ADDRESS}), 
                    timeout=4.0
                )

                log_trade(f"   -> 🟢 SIMULATION PASSED AT {display_pct}% SIZE! Broadcasting fast...")
                latest_block = await w3.eth.get_block('latest')
                base_fee = latest_block.get('baseFeePerGas', 0)
                
                priority_tip = w3.to_wei(0.1, 'gwei')
                max_fee = base_fee + priority_tip
                
                tx = await tx_call.build_transaction({
                    'from': ACCOUNT_ADDRESS, 
                    'nonce': nonce, 
                    'gas': int(estimated_gas * 1.05),
                    'maxFeePerGas': max_fee, 
                    'maxPriorityFeePerGas': priority_tip
                })

                signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
                tx_hash = await w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                log_trade(f"🚀 TRANSACTION BROADCASTED! Hash: {w3.to_hex(tx_hash)}")
                
                receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
                if receipt.status == 1:
                    log_trade(f"💰 SUCCESS! Arbitrage completed on {pair_name} at {display_pct}% capacity!")
                    return
                else:
                    log_trade(f"⚠️ REVERTED ON-CHAIN: Final network execution failed.")
                    return

            except asyncio.TimeoutError:
                log_trade(f"   ⏳ TIMEOUT: RPC simulation hung at {display_pct}% size.")
            except Exception as e:
                error_str = str(e).lower()
                if "execution reverted" in error_str or "0x42301c23" in error_str:
                    log_trade(f"   🛡️  SLIPPAGE BLOCKED: Size of {display_pct}% caused negative returns. Scaling down...")
                    continue 
                else:
                    log_trade(f"   ❌ Execution Error at {display_pct}% size: {type(e).__name__} - {e}")
                    return 

        log_trade(f"   ❌ SKIPPED PAIR: Evaluated all tiers down to 10% on {pair_name}, but slippage was too high across the board.")

    except Exception as e:
        log_trade(f"   ❌ Systemic Trigger Failure: {e}")

async def get_clean_uni_v3_price(pool_address, base_address, target_address):
    try:
        pool = w3.eth.contract(address=w3.to_checksum_address(pool_address), abi=UNI_V3_POOL_ABI)
        slot0, token0 = await asyncio.gather(pool.functions.slot0().call(), pool.functions.token0().call())
        raw_price = (slot0[0] / (2**96)) ** 2
        dec_base, dec_target = DECIMALS.get(base_address.lower(), 18), DECIMALS.get(target_address.lower(), 18)
        return raw_price * (10**dec_target) / (10**dec_base) if token0.lower() == target_address.lower() else (1 / raw_price) * (10**dec_target) / (10**dec_base)
    except Exception as e: 
        return None

async def get_clean_velo_price(pool_address, base_address, target_address, velo_type):
    try:
        if "v2" in velo_type or "volatile" in velo_type:
            pool = w3.eth.contract(address=w3.to_checksum_address(pool_address), abi=VELO_V2_POOL_ABI)
            reserves, token0 = await asyncio.gather(pool.functions.getReserves().call(), pool.functions.token0().call())
            if reserves[0] == 0 or reserves[1] == 0: return None
            dec_base, dec_target = DECIMALS.get(base_address.lower(), 18), DECIMALS.get(target_address.lower(), 18)
            return (reserves[1] / reserves[0]) * (10**dec_target) / (10**dec_base) if token0.lower() == target_address.lower() else (reserves[0] / reserves[1]) * (10**dec_target) / (10**dec_base)
        else: 
            return await get_clean_uni_v3_price(pool_address, base_address, target_address)
    except Exception as e: 
        return None

async def monitor_pair(pair_name, data):
    try:
        base_address, target_address = data["base_address"], data["address"]
        uni_price, velo_price = await asyncio.gather(
            get_clean_uni_v3_price(data["uni_pool"], base_address, target_address),
            get_clean_velo_price(data["velo_pool"], base_address, target_address, data["velo_type"])
        )

        if not uni_price or not velo_price: return

        spread = abs(uni_price - velo_price) / min(uni_price, velo_price) * 100
        
        velo_stable = "stable" in data["velo_type"]
        min_required_spread = 0.15 if velo_stable else 0.85
        
        if min_required_spread < spread < 15.0:
            log_trade(f"🚨 SPREAD DETECTED: {pair_name} | {spread:.2f}%")
            dec_base = DECIMALS.get(base_address.lower(), 18)
            borrow_amount = int(0.3 * (10 ** dec_base)) if data['base_asset'] == "WETH" else int(1000 * (10 ** dec_base))
            zero_for_one = base_address.lower() < target_address.lower()

            if trade_lock.locked(): return

            if uni_price < velo_price:
                async with trade_lock:
                    await trigger_flash_execution(data["uni_pool"], data["velo_pool"], data["velo_type"], base_address, target_address, borrow_amount, zero_for_one, velo_stable, pair_name)
            else:
                async with trade_lock:
                    await trigger_flash_execution(data["velo_pool"], data["uni_pool"], "v3", base_address, target_address, borrow_amount, not zero_for_one, False, pair_name)
    except Exception as e:
        pass

async def main():
    print("🤖 Production Daemon Initialized. Scanning active pipelines...\n")
    while True:
        try:
            tracked_pairs = load_tracked_pairs()
            for name, data in tracked_pairs.items():
                await asyncio.wait_for(monitor_pair(name, data), timeout=4.0)
                await asyncio.sleep(0.2) 
        except Exception:
            pass
        await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())
