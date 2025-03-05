import os
from dotenv import load_dotenv
load_dotenv()
# Configuration settings for the Telegram bot
class Config:
    # Telegram Bot API Token
    TOKEN = os.environ.get("BOT_TOKEN")

    # Bot username
    BOT_USERNAME = "@Legit_escrow_bot"

    # Fee configuration
    FEE_AMOUNT = 0.50  # Fixed fee in USD

    # Network-specific wallet addresses
    NETWORK_WALLETS = {
        'BEP20': '0x7646090a2ff41339918505040367b592d0bea9e0',
        'ERC20': '0x00cd23325e916ae47a93b50df1dbf420f50fbd70',
        'OPTIMISM': '0xcab27f050fbe0c011b6b4fb4247b706d1b60dc48',
        'ARBITRUM': '0x79e52eb60ea00cbe2df7afe541554d16e6825a51'
    }

    # Network Configuration with detailed information
    BLOCKCHAIN_INFO = {
        'BEP20': {
            'name': 'Binance Smart Chain',
            'icon': '🟡',
            'gas_fee': '$0.15',
            'speed': '~3s',
            'security': '🔒 High',
            'explorer': 'https://bscscan.com'
        },
        'ERC20': {
            'name': 'Ethereum',
            'icon': '🔷',
            'gas_fee': '$5-15',
            'speed': '~15s',
            'security': '🔒 Very High',
            'explorer': 'https://etherscan.io'
        },
        'OPTIMISM': {
            'name': 'Optimism',
            'icon': '🔴',
            'gas_fee': '$0.3-1',
            'speed': '~2s',
            'security': '🔒 High',
            'explorer': 'https://optimistic.etherscan.io'
        },
        'ARBITRUM': {
            'name': 'Arbitrum',
            'icon': '🔵',
            'gas_fee': '$0.1-0.5',
            'speed': '~1s',
            'security': '🔒 High',
            'explorer': 'https://arbiscan.io'
        }
    }

    # Supported languages with flags
    SUPPORTED_LANGUAGES = {
        'en': 'English 🇬🇧',
        'zh': 'Chinese 🇨🇳',
        'es': 'Spanish 🇪🇸',
        'ru': 'Russian 🇷🇺'
    }


    # Flask settings
    FLASK_HOST = "0.0.0.0"
    FLASK_PORT = 8000