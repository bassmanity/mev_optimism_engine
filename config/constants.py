import os
from dotenv import load_dotenv

load_dotenv()

# --- RPC CONFIGURATION ---
# Defaulting to the public Optimism endpoint for open-source safety.
# ⚠️ WARNING: Public nodes are rate-limited and will be too slow for live MEV execution.
# To run this in production, replace this with your private Alchemy/Infura URL or
# inject it securely via your .env file: RPC_URL = os.getenv("RPC_URL")
RPC_URL = "https://mainnet.optimism.io"

# Target Flash Arbitrage Contract Address
CONTRACT_ADDRESS = "0xf3D284341CB248CE06C0044d7D98Ab88C8e44feb"

# --- MASTER ERC20 DECIMALS ---
DECIMALS = {
    "0x4200000000000000000000000000000000000006": 18, # WETH
    "0x0b2c639c533813f4aa9d7837caf62653d097ff85": 6,  # Native USDC
    "0x7f5c764cbc14f9669b88837ca1490cca17c31607": 6,  # Bridged USDC
    "0x4200000000000000000000000000000000000042": 18, # OP
    "0x8700daec35af8ff88c16bdf0418774cb3d7599b4": 18, # SNX
    "0x350a791bfc2c21f9ed5d10980dad2e2638ffa7f6": 18, # LINK
    "0x68f180fcce6836688e9084f035309e29bf0a2095": 8,  # WBTC
    "0x94b008aa00579c1307b0ef2c499ad98a8ce58e58": 6,  # USDT
    "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1": 18, # DAI
    "0x940181a94a35a4569e4529a3cdfb74e38fd98631": 18, # AERO
    "0x6c84a8f1c29108f47a79964b5fe888d4f4d0de40": 18, # tBTC
    "0x6fd9d7ad17242c41f7131d257212c54a0e816691": 18, # UNI
    "0x9560e827af36c94d2ac33a39bce1fe78631088db": 18, # VELO
    "0xdc6ff44d5d932cbd77b52e5612ba0529dc6226f1": 18, # WLD
    "0x1f32b1c2345538c0c6f582fcb022739c4a194ebb": 18  # wstETH
}
