# walnavi
Wallet Navigator

it works in 2 modes:
1. easy cli wallet
2. wallet deamon for remote control via e2ee email (recommended with gpgon app)

To start configure config/deamons and config/currencies accordingly:
1. if yo uwant to use only Verus or Pirate - edit "config\deamons" to set specific path
2. if other currency - additionally you need to make relevant json file in "config\currencies"
3. Deamon mode requires to set up some credentials to send notifications and get commands via email. Credentials are stored in AES encrypted file, that's why at start it requires a good password you remember. I recommend to follow gpgon mailbox setup instructions pdf.

Basic python libs required (see gpgon app Android instructions)

Should work on both linux and Windows

Features:
1. address book with aliases
2. addres validation
3. wallet status, balances
4. sending tx with confirmation
- step1: send am=0.01 fr=fromalias to=myfavaddr
- step2: confirm
5. tx limits setup for remote usage
6. use symetric or asymetric keys - PGP or AES256 encryption
7. in case of using PGP wallet secred key is suggested to be set up
