# Real-time speech recognition from a microphone with sherpa-ncnn Python API
# with endpoint detection.
#
# Please refer to
# https://k2-fsa.github.io/sherpa/ncnn/pretrained_models/index.html
# to download pre-trained models

# pip install websockets

import sys
import asyncio
import websockets
import json

async def send_message_to_websocket(message):
    async with websockets.connect('ws://localhost:60001') as websocket:
        await websocket.send(message)  # 发送消息给服务器
        print("Message sent")

def send_message(message):
    asyncio.run(send_message_to_websocket(message))

try:
    import sounddevice as sd
except ImportError as e:
    print("Please install sounddevice first. You can use")
    print()
    print("  pip install sounddevice")
    print()
    print("to install it")
    sys.exit(-1)

import sherpa_ncnn

# 设置状态变量
is_listening = False
question_queue = []

def create_recognizer():
    # Please replace the model files if needed.
    # See https://k2-fsa.github.io/sherpa/ncnn/pretrained_models/index.html
    # for download links.
    recognizer = sherpa_ncnn.Recognizer(
        tokens="./tokens.txt",
        encoder_param="./encoder_jit_trace-pnnx.ncnn.param",
        encoder_bin="./encoder_jit_trace-pnnx.ncnn.bin",
        decoder_param="./decoder_jit_trace-pnnx.ncnn.param",
        decoder_bin="./decoder_jit_trace-pnnx.ncnn.bin",
        joiner_param="./joiner_jit_trace-pnnx.ncnn.param",
        joiner_bin="./joiner_jit_trace-pnnx.ncnn.bin",
        num_threads=4,
        decoding_method="modified_beam_search",
        enable_endpoint_detection=True,
        rule1_min_trailing_silence=2.4,
        rule2_min_trailing_silence=1.2,
        rule3_min_utterance_length=300,
        hotwords_file="",
        hotwords_score=1.5,
    )
    return recognizer


def main():
    print("开始识别，请说话")
    recognizer = create_recognizer()
    sample_rate = recognizer.sample_rate
    samples_per_read = int(0.1 * sample_rate)  # 0.1 second = 100 ms
    last_result = ""
    segment_id = 0

    with sd.InputStream(channels=1, dtype="float32", samplerate=sample_rate) as s:
        while True:
            samples, _ = s.read(samples_per_read)  # a blocking read
            samples = samples.reshape(-1)
            recognizer.accept_waveform(sample_rate, samples)

            is_endpoint = recognizer.is_endpoint

            result = recognizer.text
            if result and (last_result != result):
                last_result = result
                #print("\r{}:{}".format(segment_id, result), end="", flush=True)

            if is_endpoint:
                if result:
                    print("\r{}:{}".format(segment_id, result), flush=True)
                    global is_listening
                    text=result
                    if "小红小红" in str(text.lower()):
                        is_listening = True
                        print("唤醒数字人...")
                        my_dict = {
                            "type": "nihao",
                            "content": "你好我在"
                        }
                        json_string = json.dumps(my_dict, ensure_ascii=False)
                        result = json_string
                        print("ws 60001发送数据："+result)
                        send_message(result)

                    elif is_listening and "你好我在" not in text:
                        is_listening = False
                        print(f"提问文心一言: {text}")
                        my_dict = {
                            "type": "tiwen",
                            "content": text
                        }
                        json_string = json.dumps(my_dict, ensure_ascii=False)
                        result = json_string
                        print("ws 60001发送数据："+result)
                        send_message(result)

                    result=""
                    segment_id += 1
                recognizer.reset()


if __name__ == "__main__":
    devices = sd.query_devices()
    #print(devices)
    default_input_device_idx = sd.default.device[0]
    #print(f'Use default device: {devices[default_input_device_idx]["name"]}')

    try:
        main()
    except KeyboardInterrupt:
        print("\nCaught Ctrl + C. Exiting")