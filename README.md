### Консольная версия
Необходимы установленные Python 3.6+, pip, virtualenv, git

#### Установка
```bash
$ git clone https://github.com/bakatrouble/spb_elections_recorder_2019/
$ virtualenv -p python3 venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

#### Использование
`X`, `Y` - начало и конец диапазона номеров УИКов для загрузки трансляций
```bash
$ source venv/bin/activate
$ python cli.py --start X --end Y
```