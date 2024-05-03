# pip install click --upgrade
import librosa
from flask import Flask, request, jsonify, make_response
import os
import alitts
from pydub import AudioSegment
import requests
import time
import json
import configparser
from difflib import SequenceMatcher
import http.client
import mimetypes
from codecs import encode
from threading import Timer
import uuid

config = configparser.ConfigParser()
config.read('./secrets.ini')
app = Flask(__name__)
app.secret_key = 'daowifhsefighsaofhia' # 这里不用改
wav_name = "test.wav"
usd_file_name = "DefaultOfficialInstance.usd"
usd_absolute_path = os.path.abspath(usd_file_name)
a2fserverurl='http://127.0.0.1:10246'

answer_sentence="" # 判断文本相似度
request_end_time = {} # 判断打断
API_KEY = config.get('wenxin', 'apikey') # 文心一言密钥
SECRET_KEY = config.get('wenxin', 'appsecret') # 文心一言密钥

timers = {}
key = uuid.uuid4()

def timer_expired(key):
    print(f"说话结束")

def start_timer(key, timeout):
    timers[key] = Timer(timeout, timer_expired, args=(key,))
    timers[key].start()


def delay_response(delay, response):
    """延时返回响应"""
    time.sleep(delay)
    return make_response(response)

# 问答
# 你是谁？我是公司客服机器人佳慧
# 请介绍下我们公司？ 我们公司是与云计算伴生的一项基于超级计算机系统对外提供计算资源、存储资源等服务的机构或单位，以高性能计算机为基础面向各界提供高性能计算服务。
# 我还想了解更多？我们公司致力于为各行各业提供高性能计算服务，利用高性能计算机系统提供计算资源、存储资源等解决方案。我们的目标是通过云计算技术帮助客户实现更快、更强大的计算能力，以推动科学研究、工程设计和商业创新的发展。我们的团队拥有丰富的经验和专业知识，致力于为客户提供可靠、安全、高效的计算服务，以满足不断增长的需求。

# 获取文心一言token
def get_access_token():
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    return str(requests.post(url, params=params).json().get("access_token"))

# 获取wav时长
def get_duration(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None) # sr=None 保持原始采样率
        duration = librosa.get_duration(y=y, sr=sr)
        return duration
    except Exception as e:
        print(f"Error with librosa: {e}")
        return None

# 清理状态初始化
@app.route('/clearstatus', methods=['POST'])
def clearstatus():
    global answer_sentence
    answer_sentence="" # 判断文本相似度
    data = request.form
    # 接收 JSON 数据
    # F:/audio2face-2023.1.1/exts/omni.audio2face.player_deps/deps/audio2face-data/tracks/
    # {"message":"你好吗"}
    data_message = data.get("message")
    # 根据中文TTS生成wav文件
    output = data_message
    wav_file = wav_name
    alitts.speakword(wav_file,output)
    # 计算音频总长度，秒
    total_length = get_duration(wav_file)
    audio = AudioSegment.from_file(wav_file)
    length = len(audio) / 1000 # 获取的长度单位是毫秒，转换为秒钟
    url = a2fserverurl+'/A2F/Player/SetTrack'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    dat2a = {
        'a2f_player': '/World/audio2face/Player',
        'file_name': wav_name,
        'time_range': [0, -1]
    }
    response = requests.post(url, headers=headers, json=dat2a)
    url = a2fserverurl+'/A2F/Player/Play'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    dat2a = {
        'a2f_player': '/World/audio2face/Player'
    }
    response = requests.post(url, headers=headers, json=dat2a)
    # 返回收到的数据，这只是为了演示
    data={}
    data["message"]=str(data_message)
    data["record_time"]=total_length
    return jsonify(data)

# 直接说话
@app.route('/apppost', methods=['POST'])
def speak():
    global answer_sentence
    global request_end_time
    global timers
    global key
    data = request.form
    data_message = data.get("message")
    
    if key in timers and timers[key].is_alive():
        print("正在说话，开始打断")
        timers = {}
        output = "你好我在"
        wav_file = wav_name
        alitts.speakword(wav_file,output)
        # 计算音频总长度，秒
        total_length = get_duration(wav_file)
        audio = AudioSegment.from_file(wav_file)
        length = len(audio) / 1000 # 获取的长度单位是毫秒，转换为秒钟
        url = a2fserverurl+'/A2F/Player/SetTrack'
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        dat2a = {
            'a2f_player': '/World/audio2face/Player',
            'file_name': wav_name,
            'time_range': [0, -1]
        }
        response = requests.post(url, headers=headers, json=dat2a)
        url = a2fserverurl+'/A2F/Player/Play'
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        dat2a = {
            'a2f_player': '/World/audio2face/Player'
        }
        response = requests.post(url, headers=headers, json=dat2a)
        # 返回收到的数据，这只是为了演示
        data = {}
        data["message"]=data_message
        data["record_time"]=total_length
        return jsonify(data)
    else:
        # 根据中文TTS生成wav文件
        output = data_message
        # 防止回声干扰
        answer_sentence = output
        wav_file = wav_name
        alitts.speakword(wav_file,output)

        # 计算音频总长度，秒
        total_length = get_duration(wav_file)
        audio = AudioSegment.from_file(wav_file)
        length = len(audio) / 1000 # 获取的长度单位是毫秒，转换为秒钟
        
        url = a2fserverurl+'/A2F/Player/SetTrack'
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        dat2a = {
            'a2f_player': '/World/audio2face/Player',
            'file_name': wav_name,
            'time_range': [0, -1]
        }
        response = requests.post(url, headers=headers, json=dat2a)
        url = a2fserverurl+'/A2F/Player/Play'
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        dat2a = {
            'a2f_player': '/World/audio2face/Player'
        }
        response = requests.post(url, headers=headers, json=dat2a)
        # 返回收到的数据，这只是为了演示
        data = {}
        data["message"]=data_message
        data["record_time"]=total_length
        return jsonify(data)

# 文心一言回答
@app.route('/wenxin', methods=['POST'])
# @timer_limit
def wenxin():
    global answer_sentence
    global timers
    global key
    data = request.form
    data_message = data.get("message")
    # 判断文本相似度
    similarity_ratio = SequenceMatcher(None, answer_sentence, data_message).ratio()
    if similarity_ratio >= 0.3:
        return jsonify({'error': '答案回声传入，并非问题'}), 400
    else:
        if '你是谁' in data_message:
            output = '我是公司客服机器人XXXXX'
        elif '请介绍下我们公司' in data_message:
            output = '我们公司是与云计算伴生的一项基于超级计算机系统对外提供计算资源、存储资源等服务的机构或单位，以高性能计算机为基础面向各界提供高性能计算服务。'
        elif '我还想了解更多' in data_message:
            output = '我还想了解更多？我们公司致力于为各行各业提供高性能计算服务，利用高性能计算机系统提供计算资源、存储资源等解决方案。我们的目标是通过云计算技术帮助客户实现更快、更强大的计算能力，以推动科学研究、工程设计和商业创新的发展。我们的团队拥有丰富的经验和专业知识，致力于为客户提供可靠、安全、高效的计算服务，以满足不断增长的需求。'
        else:
            url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant?access_token=" + get_access_token()
            s=data_message
            # 注意message必须是奇数条
            payload = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": "用最简洁的语言回答“"+s+"”这个问题"
                }
            ]
            })
            headers = {
                'Content-Type': 'application/json'
            }
            res = requests.request("POST", url, headers=headers, data=payload).json()
            # 根据中文TTS生成wav文件
            print(res)
            output = res['result']
            answer_sentence=output
            wav_file = wav_name
            alitts.speakword(wav_file,output)

            # 计算音频总长度，秒
            total_length = get_duration(wav_file)
            audio = AudioSegment.from_file(wav_file)
            length = len(audio) / 1000 # 获取的长度单位是毫秒，转换为秒钟
            
            url = a2fserverurl+'/A2F/Player/SetTrack'
            headers = {
                'accept': 'application/json',
                'Content-Type': 'application/json'
            }
            dat2a = {
                'a2f_player': '/World/audio2face/Player',
                'file_name': wav_name,
                'time_range': [0, -1]
            }
            response = requests.post(url, headers=headers, json=dat2a)
            url = a2fserverurl+'/A2F/Player/Play'
            headers = {
                'accept': 'application/json',
                'Content-Type': 'application/json'
            }
            dat2a = {
                'a2f_player': '/World/audio2face/Player'
            }
            response = requests.post(url, headers=headers, json=dat2a)
 
            timeout = float(total_length) 
            start_timer(key, timeout)
                    
            data = {}
            data["message"]=output
            data["record_time"]=total_length
            return jsonify(data)


def huansheng(message):
    conn = http.client.HTTPSConnection("readvoice.qnxr.ltd")
    dataList = []
    boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'
    dataList.append(encode('--' + boundary))
    dataList.append(encode('Content-Disposition: form-data; name=text;'))
    dataList.append(encode('Content-Type: {}'.format('text/plain')))
    dataList.append(encode(''))
    dataList.append(encode(message))
    dataList.append(encode('--'+boundary+'--'))
    dataList.append(encode(''))
    body = b'\r\n'.join(dataList)
    payload = body
    headers = {
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'Content-type': 'multipart/form-data; boundary={}'.format(boundary)
    }
    conn.request("POST", "/voice?model_id=0&speaker_name=Yennefer&sdp_ratio=0.2&noise=0.2&noisew=0.9&length=1&language=ZH&auto_translate=false&auto_split=false&emotion=&style_weight=0.7", payload, headers)
    res = conn.getresponse()
    data = res.read()
    with open('test.wav', 'wb') as file:
        file.write(data)

if __name__ == '__main__':
    print(usd_absolute_path)
    url = a2fserverurl+'/A2F/USD/Load'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {
        'file_name': usd_absolute_path
    }
    response = requests.post(url, headers=headers, json=data)
    wav_absolute_pathdir = os.path.abspath(wav_name).replace("\\"+wav_name,"")
    print(wav_absolute_pathdir)
    url = a2fserverurl+'/A2F/Player/SetRootPath'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {
        'a2f_player': '/World/audio2face/Player',
        'dir_path': wav_absolute_pathdir
    }
    response = requests.post(url, headers=headers, json=data)

    
    output = "初始化完成"
    answer_sentence=output
    wav_file = wav_name
    alitts.speakword(wav_file,output)
    # 计算音频总长度，秒
    total_length = get_duration(wav_file)
    audio = AudioSegment.from_file(wav_file)
    length = len(audio) / 1000 # 获取的长度单位是毫秒，转换为秒钟
    url = a2fserverurl+'/A2F/Player/SetTrack'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    dat2a = {
        'a2f_player': '/World/audio2face/Player',
        'file_name': wav_name,
        'time_range': [0, -1]
    }
    response = requests.post(url, headers=headers, json=dat2a)
    url = a2fserverurl+'/A2F/Player/Play'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    dat2a = {
        'a2f_player': '/World/audio2face/Player'
    }
    response = requests.post(url, headers=headers, json=dat2a)
    print("初始化完成")
    app.run(port=5000, debug=True)










# #################### v1 是 vits 换声接口 可以忽略 ####################
# # 清理状态初始化
# @app.route('/clearstatus-v1', methods=['POST'])
# def clearstatusv1():
#     global record_time
#     global startrecord
#     global answer_sentence
#     # 状态初始化
#     record_time=0
#     startrecord=None
#     last_request_time = 0
#     wenxin_length=0
#     answer_sentence="" # 判断文本相似度
#     data = request.form
#     # 接收 JSON 数据
#     # F:/audio2face-2023.1.1/exts/omni.audio2face.player_deps/deps/audio2face-data/tracks/
#     # {"message":"你好吗"}
#     data_message = data.get("message")
#     # 根据中文TTS生成wav文件
#     output = data_message
#     wav_file = wav_name
#     huansheng(output)
#     # 计算音频总长度，秒
#     total_length = get_duration(wav_file)
#     audio = AudioSegment.from_file(wav_file)
#     length = len(audio) / 1000 # 获取的长度单位是毫秒，转换为秒钟
#     url = a2fserverurl+'/A2F/Player/SetTrack'
#     headers = {
#         'accept': 'application/json',
#         'Content-Type': 'application/json'
#     }
#     dat2a = {
#         'a2f_player': '/World/audio2face/Player',
#         'file_name': wav_name,
#         'time_range': [0, -1]
#     }
#     response = requests.post(url, headers=headers, json=dat2a)
#     url = a2fserverurl+'/A2F/Player/Play'
#     headers = {
#         'accept': 'application/json',
#         'Content-Type': 'application/json'
#     }
#     dat2a = {
#         'a2f_player': '/World/audio2face/Player'
#     }
#     response = requests.post(url, headers=headers, json=dat2a)
#     # 返回收到的数据，这只是为了演示
#     data={}
#     data["message"]=str(data_message)
#     data["record_time"]=total_length
#     return jsonify(data)
# # 打断逻辑
# @app.route('/daduan-v1', methods=['POST'])
# def daduanv1():
#     data = request.form
#     global record_time
#     global startrecord
#     global last_request_time
#     # 接收 JSON 数据
#     data_message = data.get("message")
#     # 判断是否在说话
#     start_time = startrecord
#     if start_time is None:
#         response = {'message': 'notstart'}
#         print("从来没有说话")
#         return jsonify(response)  # 返回JSON响应
    
#     elapsed_time = time.time() - start_time  # 计算经过的时间
#     if elapsed_time < record_time:
#         print("执行打断")
#         # api执行暂停说话
#         url = a2fserverurl+'/A2F/Player/Pause'
#         headers = {
#             'accept': 'application/json',
#             'Content-Type': 'application/json'
#         }
#         data = {
#             'a2f_player': '/World/audio2face/Player'
#         }
#         response = requests.post(url, headers=headers, json=data)
#         # 回答，在的，你说
#         output = "在的，你说"
#         wav_file = wav_name
#         huansheng(output)
#         print(2) 
#         # 计算音频总长度，秒
#         total_length = get_duration(wav_file)
#         audio = AudioSegment.from_file(wav_file)
#         length = len(audio) / 1000 # 获取的长度单位是毫秒，转换为秒钟
        
#         url = a2fserverurl+'/A2F/Player/SetTrack'
#         headers = {
#             'accept': 'application/json',
#             'Content-Type': 'application/json'
#         }
#         data = {
#             'a2f_player': '/World/audio2face/Player',
#             'file_name': wav_name,
#             'time_range': [0, -1]
#         }
#         response = requests.post(url, headers=headers, json=data)
#         url = a2fserverurl+'/A2F/Player/Play'
#         headers = {
#             'accept': 'application/json',
#             'Content-Type': 'application/json'
#         }
#         data = {
#             'a2f_player': '/World/audio2face/Player'
#         }
#         response = requests.post(url, headers=headers, json=data)
#         # 返回收到的数据，这只是为了演示
#         response = {'message': 'ok'}
#         wenxin_length=0
#         current_time = time.time()
#         last_request_time = current_time
#     else:
#         print("没有在说话，不执行打断")
#         # 返回收到的数据，这只是为了演示
#         response = {'message': 'failed'}
#     return jsonify(response)  # 返回JSON响应
# # 直接说话
# @app.route('/apppost-v1', methods=['POST'])
# def speakv1():
#     global record_time
#     global startrecord
#     startrecord = time.time()  # 记录开始时间
#     data = request.form
#     # 接收 JSON 数据
#     # F:/audio2face-2023.1.1/exts/omni.audio2face.player_deps/deps/audio2face-data/tracks/
#     # {"message":"你好吗"}
#     data_message = data.get("message")
#     #print(data_message)

#     # 根据中文TTS生成wav文件
#     output = data_message
#     wav_file = wav_name
#     huansheng(output)

#     # 计算音频总长度，秒
#     total_length = get_duration(wav_file)
#     audio = AudioSegment.from_file(wav_file)
#     length = len(audio) / 1000 # 获取的长度单位是毫秒，转换为秒钟
    
#     url = a2fserverurl+'/A2F/Player/SetTrack'
#     headers = {
#         'accept': 'application/json',
#         'Content-Type': 'application/json'
#     }
#     dat2a = {
#         'a2f_player': '/World/audio2face/Player',
#         'file_name': wav_name,
#         'time_range': [0, -1]
#     }
#     response = requests.post(url, headers=headers, json=dat2a)
#     url = a2fserverurl+'/A2F/Player/Play'
#     headers = {
#         'accept': 'application/json',
#         'Content-Type': 'application/json'
#     }
#     dat2a = {
#         'a2f_player': '/World/audio2face/Player'
#     }
#     response = requests.post(url, headers=headers, json=dat2a)
#     record_time=total_length
#     # 返回收到的数据，这只是为了演示
#     data = {}
#     data["message"]=data_message
#     data["record_time"]=total_length
#     return jsonify(data)
# # 文心一言回答
# @app.route('/wenxin-v1', methods=['POST'])
# # @timer_limit
# def wenxinv1():
#     global wenxin_length
#     global record_time
#     global startrecord
#     global answer_sentence
#     startrecord = time.time()  # 记录开始时间
#     data = request.form
#     data_message = data.get("message")
#     # 判断文本相似度
#     similarity_ratio = SequenceMatcher(None, answer_sentence, data_message).ratio()
#     print("文本相似度")
#     print(similarity_ratio)
#     if similarity_ratio >= 0.3:
#         return jsonify({'error': '回声传入，并非问题'}), 400
#     else:
#         if '你是谁' in data_message:
#             output = '我是公司客服机器人佳慧'
#         elif '请介绍下我们公司' in data_message:
#             output = '我们公司是与云计算伴生的一项基于超级计算机系统对外提供计算资源、存储资源等服务的机构或单位，以高性能计算机为基础面向各界提供高性能计算服务。'
#         elif '我还想了解更多' in data_message:
#             output = '我还想了解更多？我们公司致力于为各行各业提供高性能计算服务，利用高性能计算机系统提供计算资源、存储资源等解决方案。我们的目标是通过云计算技术帮助客户实现更快、更强大的计算能力，以推动科学研究、工程设计和商业创新的发展。我们的团队拥有丰富的经验和专业知识，致力于为客户提供可靠、安全、高效的计算服务，以满足不断增长的需求。'
#         else:
#             url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant?access_token=" + get_access_token()
#             s=data_message
#             # 注意message必须是奇数条
#             payload = json.dumps({
#             "messages": [
#                 {
#                     "role": "user",
#                     "content": s
#                 }
#             ]
#             })
#             headers = {
#                 'Content-Type': 'application/json'
#             }
#             res = requests.request("POST", url, headers=headers, data=payload).json()
#             # 根据中文TTS生成wav文件
#             print(res)
#             output = res['result']
#         answer_sentence=output
#         wav_file = wav_name
#         huansheng(output)

#         # 计算音频总长度，秒
#         total_length = get_duration(wav_file)
#         wenxin_length=total_length
#         audio = AudioSegment.from_file(wav_file)
#         length = len(audio) / 1000 # 获取的长度单位是毫秒，转换为秒钟
        
#         url = a2fserverurl+'/A2F/Player/SetTrack'
#         headers = {
#             'accept': 'application/json',
#             'Content-Type': 'application/json'
#         }
#         dat2a = {
#             'a2f_player': '/World/audio2face/Player',
#             'file_name': wav_name,
#             'time_range': [0, -1]
#         }
#         response = requests.post(url, headers=headers, json=dat2a)
#         url = a2fserverurl+'/A2F/Player/Play'
#         headers = {
#             'accept': 'application/json',
#             'Content-Type': 'application/json'
#         }
#         dat2a = {
#             'a2f_player': '/World/audio2face/Player'
#         }
#         response = requests.post(url, headers=headers, json=dat2a)

#         data_message = data.get("message")
#         # 根据中文TTS生成wav文件
#         output = data_message
#         wav_file = wav_name
#         alitts.speakword(wav_file,output)
#         # 计算音频总长度，秒
#         total_length = get_duration(wav_file)
#         audio = AudioSegment.from_file(wav_file)
#         length = len(audio) / 1000 # 获取的长度单位是毫秒，转换为秒钟
#         url = a2fserverurl+'/A2F/Player/SetTrack'
#         headers = {
#             'accept': 'application/json',
#             'Content-Type': 'application/json'
#         }
#         dat2a = {
#             'a2f_player': '/World/audio2face/Player',
#             'file_name': wav_name,
#             'time_range': [0, -1]
#         }
#         response = requests.post(url, headers=headers, json=dat2a)
#         url = a2fserverurl+'/A2F/Player/Play'
#         headers = {
#             'accept': 'application/json',
#             'Content-Type': 'application/json'
#         }
#         dat2a = {
#             'a2f_player': '/World/audio2face/Player'
#         }
#         response = requests.post(url, headers=headers, json=dat2a)
#         record_time=total_length
#         data = {}
#         data["message"]=output
#         return jsonify(data)
# ################################################################################