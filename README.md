# vic.py

vic.py (VNA impedance calculator) is a Python script to convert measured S-parameters to complex impedances for the following measurement setups:

* S11 Shunt
* S21 Series
* S21 Shunt Through

## Preparing for Use

### Linux / OS X

```sh
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
python vic.py -h
```

### Windows

```powershell
python3 -m venv .env
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.env/bin/Activate.ps1
pip install -r requirements.txt
python vic.py -h
```
