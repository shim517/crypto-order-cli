# About this repo

- This repo is a simple trading bot that buys a cryptocurrency from the best exchange.
- It used testnet for Binance and OKX.
- Follows DDD.

# Preparation

## Generate API key for Binance and OKX

- For Binance, see https://testnet.binance.vision/
  - You will use the API key and secret key to use the API.
- For OKX, see https://www.okx.com/help/api-faq#how-to-create-a-demo-disk-apikey
  - You will use the API key, secret key, and passphrase to use the API.

## Environment

- Linux ubuntu 6.8.0-1018-raspi #20-Ubuntu SMP PREEMPT_DYNAMIC Fri Jan 17 12:35:36 UTC 2025 aarch64 aarch64 aarch64 GNU/Linux
- Python 3.13.2 (using pyenv)

\* Other environments may work, but not tested.

# Usage

```bash
cd crypto-order
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt -r requirements.test.txt

# Set API key and secret keys. Input your API key, secret key, and passphrase.
read -s BINANCE_API_KEY; export BINANCE_API_KEY;
read -s BINANCE_API_SECRET; export BINANCE_API_SECRET;
read -s OKX_API_KEY; export OKX_API_KEY;
read -s OKX_API_SECRET; export OKX_API_SECRET;
read -s OKX_API_PASSPHRASE; export OKX_API_PASSPHRASE;

export PYTHONPATH=$PYTHONPATH:$(pwd)/src
# Run the CLI
python src/trading/interface/cli.py --side buy --quantity 1 --log-level debug
```


# Run test

```bash
cd crypto-order
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
pytest
coverage run -m pytest
coverage report
```

# Known issues

- When I run the cli.py with --quantity 0.01 and OKX is chosen as the best exchange, the following error occurs:
  - `All operations failed`
  - I have not found the cause yet.
  - `--quantity 1` works fine though.
