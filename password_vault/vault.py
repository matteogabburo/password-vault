import os
import logging
import json
import getpass
import hashlib
import cryptography
import time

from base64 import b64decode, b64encode
from cryptography.fernet import Fernet

logging.basicConfig(level="INFO")

class WalletNotFoundException(Exception):
    pass

class NotCorrectMasterPasswordException(Exception):
    pass

class KeyNotInWalletException(Exception):
    pass

class NotWellFormedWalletException(Exception):
    pass

def json_loads(pth):

    if not os.path.exists(pth):
        raise WalletNotFoundException

    try:
        with open(pth, "r") as f:
            wallet = (json.loads(f.read()))
    except json.decoder.JSONDecodeError:
        raise NotWellFormedWalletException()
    return wallet

class Vault:

    def __init__(self, pth, master_password=None, keep_unlocked=10):
        
        self.pth = pth
        self._keep_unlocked = keep_unlocked
        self._last_unlock = None
        self._tmp_master_password = None

        self.init_wallet(pth, master_password)

    def init_wallet(self, pth, master_password=None):

        self.pth = pth
        if not os.path.exists(pth):
            logging.info(f'wallet "{pth}"" does not exist.')
            logging.info(f'creating a new wallet here : "{pth}"...')

            if master_password is None:
                master_password = self.ask_master_password()
            
            with open(pth, "w") as f:
                f.write(json.dumps({
                    "master": self._encrypt(master_password, master_password),
                    "keys": {

                    }
                }))
        
        self.check_wellformed_wallet(pth)

    def check_wellformed_wallet(self, pth, wallet=None):
        # checking wallet
        if wallet is None:
            wallet = json_loads(pth)

        if not ("master" in wallet and "keys" in wallet):
            logging.error(f'"{pth}" does not contain a well-formed wallet')
            raise NotWellFormedWalletException()

    def ask_master_password(self):
        return getpass.getpass(prompt='Password: ', stream=None)

    def check_master_password(self, wallet, password):
        return self._decript(wallet["master"], password) == password
            
    def unlock(self, master_password=None):
        if not os.path.exists(self.pth):
            logging.error(f'"{self.pth}" does not contain wallet')
            raise WalletNotFoundException()
        
        wallet = json_loads(self.pth)

        self.check_wellformed_wallet(self.pth, wallet=wallet)

        if self._last_unlock != None and time.time() - self._last_unlock < self._keep_unlocked:
            master_password = self._tmp_master_password
        else:
            self._tmp_master_password = None

        if master_password is None:
            master_password = self.ask_master_password()

        if not self.check_master_password(wallet, master_password):
            logging.error("master password not recognized")
            raise NotCorrectMasterPasswordException()
        
        if self._keep_unlocked > 0:
            logging.info(f"keeping the wallet open for {self._keep_unlocked} seconds")
            self._last_unlock = time.time()
            self._tmp_master_password = master_password

        return master_password, wallet

    def get(self, key, master_password=None):

        master_password, wallet = self.unlock(master_password)

        keys = {self._decript(k, master_password): k for k in wallet["keys"]} 

        if key not in keys:
            logging.error(f"this key ({key}) is not present in this wallet")
            raise KeyNotInWalletException

        return self._decript(wallet["keys"][keys[key]], master_password)

    def add(self, key, message, master_password=None):

        master_password, wallet = self.unlock(master_password)

        wallet["keys"][self._encrypt(key, master_password)] = self._encrypt(message, master_password)

        with open(self.pth, "w") as f:
            f.write(json.dumps(wallet))

    def ls_keys(self, master_password=None):

        master_password, wallet = self.unlock(master_password)

        keys = {self._decript(k, master_password): k for k in wallet["keys"]} 

        return [key for key in keys]

    @staticmethod
    def _encrypt(dec_message, password):

        password = bytes(password, 'utf-8')
        dec_message = bytes(dec_message, 'utf-8')

        key = b64encode(hashlib.pbkdf2_hmac('sha256', password=password, salt=b"salt", iterations=100000))

        enc_message = Fernet(key).encrypt(dec_message)
        enc_message = enc_message.decode('utf-8')

        return enc_message

    @staticmethod
    def _decript(enc_message, password):
        
        try:
            password = bytes(password, 'utf-8')
            enc_message = bytes(enc_message, 'utf-8')

            key = b64encode(hashlib.pbkdf2_hmac('sha256', password=password, salt=b"salt", iterations=100000))

            dec_message = Fernet(key).decrypt(enc_message)
            dec_message = dec_message.decode('utf-8')
            
            return dec_message
        except cryptography.fernet.InvalidToken:
            logging.error("master password not recognized")
            raise NotCorrectMasterPasswordException()
