apt update
apt install software-properties-common
add-apt-repository ppa:deadsnakes/ppa
apt install python3.7 python3-pip virtualenv git
python3.7 -m pip install pip

# установка скрипта
cd ~
git clone https://github.com/bakatrouble/spb_elections_recorder_2019/
cd spb_elections_recorder_2019
virtualenv -p python3.7 venv
source venv/bin/activate
pip install -r requirements.txt

# запуск
cd ~/spb_elections_recorder_2019
source venv/bin/activate
python cli.py --start N --end N [--output /dir/name]  # default ./output
