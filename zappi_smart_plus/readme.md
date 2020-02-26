# Zappi Smart Plus App

Python 3 Script that checks the battery level of a Nissan Leaf at a specific time (e.g. start of night rate electricity) & sets the boost amount on a Zappi unit to the required level. This ensures that your car is always at a minimum level each morning.

This script is written in Python 3 but unfortunately of a horrific standard, lots of scope for improvement! Use with significant caution!

To setup:
1. Install pycarwings2 from github (https://github.com/filcole/pycarwings2) to interact with the Nissan Leaf:
    pip3 install pycarwings2
2. Edit config.ini with your login details
3. Run the python script

Further details on the Zappi API can be found here:

https://github.com/twonk/MyEnergi-App-Api
