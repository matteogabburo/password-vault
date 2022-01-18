# password-vault
A simple python library to safely store your passwords using encription

## Install
To install from master branch just do:
```
pip install git+https://github.com/matteogabburo/password-vault.git
```

If you want to install a specific development branch, use
```
pip install git+https://github.com/matteogabburo/password-vault.git@<branch_name>
```

## Usage

### TL;DR Example

```
# instantiate the wallet (using keep_unlocked=<NUM>, the system will not ask for a new password for <NUM> seconds)
vault = Vault("newwallet", keep_unlocked=20)

# add a new item to the wallet
vault.add("key1", "value1")

# get the value assiciated with the key "key1"
print(vault.get("key1"))

# the password can be also specified as a parameter (the system will not ask any password to the user)
vault.add("key2", "value2", master_password="superstrongpassword")
print(vault.get("key2", master_password="superstrongpassword"))

# you can also have a list with the keys contained in the wallet
print(vault.ls_keys(master_password="superstrongpassword"))

# if the key is not present in the wallet, the system will return a "KeyNotInWalletException"
print(vault.get("key3", master_password="ciao"))
```