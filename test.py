from flask import Flask, request
from threading import Timer

app = Flask(__name__)

timers = {}  # 存储计时器的字典

def start_timer(key, timeout):
    timers[key] = Timer(timeout, timer_expired, args=(key,))
    timers[key].start()

def timer_expired(key):
    print(f"计时器 {key} 结束")

@app.route('/wenxin', methods=['POST'])
def wenxin():
    timeout = float(request.form.get('timeout'))  # 从 POST 请求的表单数据中获取计时参数
    key = request.form.get('key')  # 从 POST 请求的表单数据中获取计时器的唯一键

    start_timer(key, timeout)
    return "Timer started"

@app.route('/apppost', methods=['POST'])
def apppost():
    key = request.form.get('key')  # 从 POST 请求的表单数据中获取计时器的唯一键

    if key in timers and timers[key].is_alive():
        print("正在说话")
    else:
        print("计时结束")
    return "Done"

if __name__ == '__main__':
    app.run()