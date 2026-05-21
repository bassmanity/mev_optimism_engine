# EVM Atomic Flash-Arbitrage Engine (Optimism L2)

An asynchronous, cross-DEX atomic arbitrage engine designed to detect and exploit localized price discrepancies between Uniswap V3 (Concentrated Liquidity) and Velodrome (V2/Slipstream) on the Optimism network. 

This project serves as a comprehensive case study in low-latency Web3 infrastructure, asynchronous block-space monitoring, and automated on-chain risk mitigation.

## 🛠️ System Architecture

The system consists of a high-performance Python daemon paired with a custom Solidity execution contract utilizing atomic flash swaps to eliminate principal capital risk.
