# EVM Atomic Flash-Arbitrage Engine (Optimism L2)

An asynchronous, cross-DEX atomic arbitrage engine designed to detect and exploit localized price discrepancies between Uniswap V3 (Concentrated Liquidity) and Velodrome (V2/Slipstream) on the Optimism network. 

This project serves as a comprehensive case study in low-latency Web3 infrastructure, asynchronous block-space monitoring, and automated on-chain risk mitigation.

## 🛠️ System Architecture

The system consists of a high-performance Python daemon paired with a custom Solidity execution contract utilizing atomic flash swaps to eliminate principal capital risk.

```text
                  ┌──────────────────────────────┐
                  │   Optimistic RPC Provider    │
                  └──────────────┬───────────────┘
                                 │ (Async JSON-RPC)
                                 ▼
                    ┌──────────────────────────┐
                    │  Async Monitor Daemon    │
                    │       (Python)           │
                    └────────────┬─────────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
┌─────────────────────────────────┐             ┌────────────────────────────────┐
│   Local Simulation Firewall     │             │     Execution Trigger          │
│ (estimate_gas Sandbox Profiling)│             │  (Dynamic Position Sizing)     │
└─────────────────────────────────┘             └────────────────────────────────┘

Key Engineering Features

    Asynchronous Blockchain Ingestion: Built using Web3.py (AsyncWeb3) and Python's asyncio framework to scan multiple liquidity pools simultaneously with staggered rate-limit throttling.

    Local Simulation Firewall: Implements pre-flight transaction profiling via Alchemy's estimate_gas RPC method, automatically trapping and dropping toxic trades (ghost spreads) before wasting network gas.

    Adaptive Sizing Module: Dynamically downscales position targeting ($1,000 → $500 → $100 equivalent) upon local simulation failure to isolate executable liquidity thresholds.

    EIP-1559 Dynamic Gas Engine: Bypasses standard node gas estimates to poll raw block headers, combining real-time base fees with custom priority tips to compete in Priority Gas Auctions (PGAs).

    Atomic Risk Profile: Deployed Solidity contract ensures all legs of the trade complete in a single atomic transaction block; if the routing yields a negative return, the entire execution reverts, entirely protecting trade principal.

📈 Production Insights & Technical Post-Mortem

Running this engine in a live production environment on the Optimism Mainnet highlighted several critical low-level protocol behaviors:

    The Shared RPC Bottleneck: Relying on public cloud infrastructure (e.g., standard Alchemy nodes) over the open internet introduces a ~100-200ms latency penalty. In hyper-competitive micro-environments like L2 DEX arbitrage, this latency window allows co-located actors using direct sequencer peering to frontrun atomic spreads.

    Phantom Liquidity Spreads: Spot price variations frequently present lucrative arbitrage percentages that fail during transaction simulation. This is due to localized price impact on thin, volatile asset pools where even small order sizes shift the constant product formula past profitable thresholds.

    On-Chain Guardrails as a Success Metric: While production logs showed trade reversions on-chain during high-slippage intervals, the custom smart contract performed flawlessly—acting as a capital shield by choosing to revert (wasting only minimal L2 gas) rather than letting trading capital execute at a net loss.

💻 Tech Stack

    Languages: Python 3.10+, Solidity ^0.8.0

    Libraries: Web3.py (AsyncHTTPProvider), Asyncio, Dotenv

    Target Network: Optimism Mainnet (L2 EVM)

    Protocols Targeted: Uniswap V3, Velodrome V2 (Volatile), Velodrome Slipstream (V3)
