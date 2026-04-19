# Changelog

All notable changes to **Apex Risk Terminal** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [5.0.0] — 2026-04-19

### Added
- **Phase 12 Apex Modules**: Neuromorphic BCI Trading, Nuclear Grid Optimizer, Autonomous AI Vaults, Agri-Tech & Biosphere, Sovereign Wealth Orchestrator
- **Phase 11 Expanse Modules**: GenAI Copilot (RAG), Global REIT Simulator, Cyber Risk & Actuarial, Supply Chain Geopolitics, Private Equity Valuation
- **Phase 10 Singularity Modules**: Astro Finance Engine, GNN Contagion Model, Climate Carbon Trading, Behavioral Finance AI, BioTech R&D Valuation
- **Phase 9 Quantum Modules**: Structured Finance & MBS, DeFi Analytics, L3 HFT Order Matching Engine, Basel IV & CCAR, Quantum Finance Lab
- **Multi-language support**: TR / EN / DE navigation translations
- **Theme system v3**: Glassmorphism dark-mode with multiple palette options

### Changed
- Upgraded from v4 to v5 institutional ensemble model
- UCI German Credit dataset integration (1,000 real records + 9,000 augmented)
- Navigation refactored to selectbox-based routing with 45+ modules

### Fixed
- Deep learning module runtime error (batch size handling)
- Plotly layout rendering issue in portfolio views
- Session state persistence for theme toggle

---

## [4.0.0] — 2026-04-15

### Added
- **Phase 7 Advanced Modules**: Fixed Income, Pairs Trading, Options Greeks, Fama-French Factor Alpha, Macro Regime
- **Phase 5 Institutional Modules**: Market Regime Analysis, Microstructure & Liquidity, Portfolio Optimization, Strategy Backtest
- Governance & Audit portal
- Command Center, Quant Sandbox, Governance Portal institutional hubs

### Changed
- Database schema expanded to 15 tables (pricing scenarios, VaR history, LLM reports)
- Auth system upgraded with account lockout and session timeout

---

## [3.0.0] — 2026-04-13

### Added
- **Phase 2 Modules**: Algorithmic Paper Trading, Regulatory Reports (IFRS 9), Derivatives Math, ESG & Sustainability, AutoML Evolutionary, Deep Learning Center, Live Risk Monitor, Exotic Credit Structuring
- PDF report generation (ReportLab)
- RAROC pricing engine

### Changed
- Ensemble model upgraded to Soft Voting (RF + GBM + LR)
- Credit scoring engine now supports `progress_callback` for live training feedback

---

## [2.0.0] — 2026-04-13

### Added
- Fraud Detection (Isolation Forest)
- Customer Clustering (K-Means, A/B/C/D Tier)
- Early Warning System
- IFRS 9 ECL Stage 1/2/3 calculation
- Macro Stress Test module (4 scenarios)
- Basel III PD/LGD/EAD modeling

### Changed
- Switched from single model to ensemble architecture
- SQLite database introduced for persistent storage

---

## [1.0.0] — 2026-04-13

### Added
- Initial credit risk prediction MVP
- Streamlit web interface with glassmorphism dark-mode theme
- Basic ML scoring engine (Random Forest)
- Login / role-based access control
- Customer analysis form
- Executive summary dashboard
