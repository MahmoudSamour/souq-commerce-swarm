#!/usr/bin/env bash
set -euo pipefail
cd /home/mm/Souq/souq-commerce-swarm
exec .venv/bin/python agents/treasury/payment_gateway_agent.py
