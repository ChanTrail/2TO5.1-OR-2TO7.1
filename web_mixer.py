"""
Web GUI 混音器 - 用于调整多声道混音的音量并实时试听
支持多个音频文件的批量处理
包含设置页面用于选择处理模式和目录
"""

import os
import gc
import json
import threading
import webbrowser
import signal
import shutil
import subprocess
import hashlib
import re
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, redirect, url_for
from pydub import AudioSegment
import numpy as np
import soundfile as sf
import tempfile
import copy
from tkinter import Tk, filedialog

app = Flask(__name__, template_folder='web_templates', static_folder='web_static')


def sanitize_filename(filename):
    """
    将文件名转换为安全的形式，避免特殊字符导致的问题
    保留基本可读性，同时添加短哈希确保唯一性
    """
    base_name = os.path.splitext(filename)[0]
    ext = os.path.splitext(filename)[1]
    
    hash_suffix = hashlib.md5(filename.encode('utf-8')).hexdigest()[:8]
    
    safe_base = re.sub(r'[^\w\u4e00-\u9fff\-]', '_', base_name)
    safe_base = re.sub(r'_+', '_', safe_base)
    safe_base = safe_base.strip('_')
    
    if not safe_base:
        safe_base = "audio"
    
    if len(safe_base) > 50:
        safe_base = safe_base[:50]
    
    return f"{safe_base}_{hash_suffix}{ext}", f"{safe_base}_{hash_suffix}"


class AudioFile:
    """单个音频文件的信息"""
    def __init__(self, name, input_dir, output_file):
        self.name = name
        self.input_dir = input_dir
        self.output_file = output_file
        self.source_segments = {}
        self.channel_config = {}
        self.is_loaded = False
        self.export_completed = False


class MixerSession:
    def __init__(self):
        self.audio_files = []
        self.current_audio_index = 0
        self.channel_count = 5
        self.sample_rate = 48000
        self.is_ready = False
        self.temp_dir = tempfile.mkdtemp()
        self.should_exit = False
        self.default_config = {}
        
        self.setup_mode = False
        self.hardware_choice = '1'
        self.input_directory = ''
        self.output_directory = ''
        self.processing_status = 'idle'
        self.processing_message = ''
        self.processing_progress = ''
        self.processing_error = ''
        self.failed_files = []
        
    def clear(self):
        self.audio_files = []
        self.is_ready = False
        self.processing_status = 'idle'
        gc.collect()
    
    @property
    def current_audio(self):
        if 0 <= self.current_audio_index < len(self.audio_files):
            return self.audio_files[self.current_audio_index]
        return None
    
    def get_all_export_completed(self):
        """检查所有音频是否都已导出"""
        return all(af.export_completed for af in self.audio_files)

mixer_session = MixerSession()


def get_default_channel_config_51():
    """获取 5.1 声道的默认配置"""
    return {
        "left_front": {
            "name": "左前 (L)",
            "sources": [
                {"source": "drums", "channel": "left", "volume": 1.0}
            ]
        },
        "right_front": {
            "name": "右前 (R)",
            "sources": [
                {"source": "drums", "channel": "right", "volume": 1.0}
            ]
        },
        "center": {
            "name": "中置 (C)",
            "sources": [
                {"source": "vocals", "channel": "mono", "volume": 1.0}
            ]
        },
        "lfe": {
            "name": "低音 (LFE)",
            "sources": [
                {"source": "bass", "channel": "mono", "volume": 1.0}
            ]
        },
        "left_surround": {
            "name": "左环绕 (LS)",
            "sources": [
                {"source": "piano", "channel": "left", "volume": 1.0},
                {"source": "guitar", "channel": "left", "volume": 1.0},
                {"source": "instrumental", "channel": "left", "volume": 1.0},
                {"source": "other", "channel": "left", "volume": 1.0},
                {"source": "vocals", "channel": "left", "volume": 1.0}
            ]
        },
        "right_surround": {
            "name": "右环绕 (RS)",
            "sources": [
                {"source": "piano", "channel": "right", "volume": 1.0},
                {"source": "guitar", "channel": "right", "volume": 1.0},
                {"source": "instrumental", "channel": "right", "volume": 1.0},
                {"source": "other", "channel": "right", "volume": 1.0},
                {"source": "vocals", "channel": "right", "volume": 1.0}
            ]
        }
    }


def get_default_channel_config_71():
    """获取 7.1 声道的默认配置"""
    return {
        "left_front": {
            "name": "左前 (L)",
            "sources": [
                {"source": "drums", "channel": "left", "volume": 1.0}
            ]
        },
        "right_front": {
            "name": "右前 (R)",
            "sources": [
                {"source": "drums", "channel": "right", "volume": 1.0}
            ]
        },
        "center": {
            "name": "中置 (C)",
            "sources": [
                {"source": "vocals", "channel": "mono", "volume": 1.0}
            ]
        },
        "lfe": {
            "name": "低音 (LFE)",
            "sources": [
                {"source": "bass", "channel": "mono", "volume": 1.0}
            ]
        },
        "left_surround": {
            "name": "左环绕 (LS)",
            "sources": [
                {"source": "instrumental", "channel": "left", "volume": 1.0},
                {"source": "piano", "channel": "left", "volume": 1.0},
                {"source": "vocals", "channel": "left", "volume": 1.0}
            ]
        },
        "right_surround": {
            "name": "右环绕 (RS)",
            "sources": [
                {"source": "instrumental", "channel": "right", "volume": 1.0},
                {"source": "piano", "channel": "right", "volume": 1.0},
                {"source": "vocals", "channel": "right", "volume": 1.0}
            ]
        },
        "rear_left_surround": {
            "name": "左后环绕 (LB)",
            "sources": [
                {"source": "guitar", "channel": "left", "volume": 1.0},
                {"source": "other", "channel": "left", "volume": 1.0},
                {"source": "instrumental", "channel": "left", "volume": 1.0},
                {"source": "vocals", "channel": "left", "volume": 1.0}
            ]
        },
        "rear_right_surround": {
            "name": "右后环绕 (RB)",
            "sources": [
                {"source": "guitar", "channel": "right", "volume": 1.0},
                {"source": "other", "channel": "right", "volume": 1.0},
                {"source": "instrumental", "channel": "right", "volume": 1.0},
                {"source": "vocals", "channel": "right", "volume": 1.0}
            ]
        }
    }


def load_source_audio(input_dir):
    """加载分离后的音频文件"""
    channels = ["vocals", "bass", "drums", "guitar", "instrumental", "piano", "other"]
    source_segments = {}
    
    for channel in channels:
        channel_file = os.path.join(input_dir, f"{channel}.wav")
        if os.path.isfile(channel_file):
            audio = AudioSegment.from_file(channel_file)
            audio = audio.set_frame_rate(48000)
            source_segments[channel] = audio
            print(f"已加载: {channel}.wav")
        else:
            print(f"文件 {channel_file} 不存在")
            source_segments[channel] = None
    
    return source_segments


def get_channel_audio_data(source_segments, source_name, channel_type):
    """获取指定音源的声道数据"""
    audio = source_segments.get(source_name)
    if audio is None:
        return None
    
    if channel_type == "mono":
        mono = audio.set_channels(1)
        return np.array(mono.get_array_of_samples(), dtype=np.float32) / 32768.0
    elif channel_type == "left":
        if audio.channels == 2:
            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            samples = samples.reshape((-1, 2))
            return samples[:, 0] / 32768.0
        else:
            return np.array(audio.get_array_of_samples(), dtype=np.float32) / 32768.0
    elif channel_type == "right":
        if audio.channels == 2:
            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            samples = samples.reshape((-1, 2))
            return samples[:, 1] / 32768.0
        else:
            return np.array(audio.get_array_of_samples(), dtype=np.float32) / 32768.0
    
    return None


def mix_channel(source_segments, channel_config):
    """根据配置混合单个输出声道"""
    mixed = None
    source_count = 0
    
    for source_config in channel_config.get("sources", []):
        source_name = source_config["source"]
        channel_type = source_config["channel"]
        volume = source_config.get("volume", 1.0)
        
        audio_data = get_channel_audio_data(source_segments, source_name, channel_type)
        if audio_data is not None:
            audio_data = audio_data * volume
            if mixed is None:
                mixed = audio_data.copy()
            else:
                min_len = min(len(mixed), len(audio_data))
                mixed = mixed[:min_len] + audio_data[:min_len]
            source_count += 1
    
    if mixed is not None and source_count > 1:
        mixed = mixed / np.sqrt(source_count)
    
    return mixed


def normalize_audio_array(audio_array, target_peak=0.95):
    """
    对音频数组进行归一化，防止削波
    
    Parameters:
    ----------
    audio_array : np.ndarray
        音频数组
    target_peak : float
        目标峰值 (0-1)
    
    Returns:
    -------
    np.ndarray
        归一化后的音频数组
    """
    max_val = np.max(np.abs(audio_array))
    if max_val > target_peak:
        audio_array = audio_array * (target_peak / max_val)
    return audio_array


def generate_preview_audio(source_segments, channel_config, channel_count):
    """生成预览音频文件"""
    if channel_count == 5:
        channel_order = ["left_front", "right_front", "center", "lfe", "left_surround", "right_surround"]
    else:
        channel_order = ["left_front", "right_front", "center", "lfe", "left_surround", "right_surround", "rear_left_surround", "rear_right_surround"]
    
    mixed_channels = []
    for ch_name in channel_order:
        ch_config = channel_config.get(ch_name, {})
        mixed = mix_channel(source_segments, ch_config)
        if mixed is not None:
            mixed_channels.append(mixed)
        else:
            duration = 0
            for seg in source_segments.values():
                if seg is not None:
                    duration = max(duration, len(seg.get_array_of_samples()) // seg.channels)
                    break
            mixed_channels.append(np.zeros(duration, dtype=np.float32))
    
    min_len = min(len(ch) for ch in mixed_channels if len(ch) > 0)
    mixed_channels = [ch[:min_len] for ch in mixed_channels]
    
    multi_channel = np.column_stack(mixed_channels)
    
    multi_channel = normalize_audio_array(multi_channel, target_peak=0.9)
    
    return multi_channel



@app.route('/')
def index():
    """根据模式决定显示设置页面还是混音器"""
    if mixer_session.setup_mode and not mixer_session.is_ready:
        return render_template('setup.html')
    return redirect(url_for('mixer_page'))


@app.route('/setup')
def setup_page():
    """设置页面"""
    return render_template('setup.html')


@app.route('/mixer')
def mixer_page():
    """混音器页面"""
    return render_template('mixer.html')


import queue
_dir_request_queue = queue.Queue()
_dir_response_queue = queue.Queue()
_tk_initialized = False


@app.route('/api/browse_dir', methods=['POST'])
def browse_dir():
    """请求打开目录选择对话框"""
    data = request.json
    dir_type = data.get('type', 'input')
    
    try:
        _dir_request_queue.put(dir_type)
        
        try:
            path = _dir_response_queue.get(timeout=60)
            if path:
                return jsonify({"path": path})
            return jsonify({"path": None})
        except queue.Empty:
            return jsonify({"error": "选择超时"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def process_dir_requests(root):
    """在主线程中处理目录选择请求"""
    try:
        while True:
            dir_type = _dir_request_queue.get_nowait()
            title = "选择音频文件所在目录" if dir_type == 'input' else "选择输出目录"
            path = filedialog.askdirectory(parent=root, title=title, initialdir=".")
            _dir_response_queue.put(path if path else None)
    except queue.Empty:
        pass
    root.after(100, lambda: process_dir_requests(root))


def separate_audio_internal(input_file, hardware_choice, mixer_session=None):
    """分离音频（内部使用）
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    tempPath = os.path.join("temp", "separate")
    os.makedirs(tempPath, exist_ok=True)
    
    if hardware_choice == "1":
        args = [
            ".\\Python\\python",
            "logic_bsroformer\\inference.py",
            "--model_type", "bs_roformer",
            "--config_path", "logic_bsroformer\\configs/logic_pro_config_v1.yaml",
            "--start_check_point", "logic_bsroformer\\models/logic_roformer.pt",
            "--input_folder", os.path.dirname(input_file),
            "--store_dir", tempPath,
            "--extract_instrumental",
        ]
    else:
        args = [
            ".\\Python\\python",
            "logic_bsroformer\\inference.py",
            "--model_type", "bs_roformer",
            "--config_path", "logic_bsroformer\\configs/logic_pro_config_v1.yaml",
            "--start_check_point", "logic_bsroformer\\models/logic_roformer.pt",
            "--input_folder", os.path.dirname(input_file),
            "--store_dir", tempPath,
            "--extract_instrumental",
            "--force_cpu",
        ]
    
    import re
    error_lines = []
    
    try:
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding='utf-8',
            errors='replace'
        )
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                if 'error' in line.lower() or 'exception' in line.lower() or 'traceback' in line.lower():
                    error_lines.append(line)
                elif line.startswith('Error') or line.startswith('Exception'):
                    error_lines.append(line)
                
                if mixer_session:
                    progress_match = re.search(r'(\d+)%\|', line)
                    if progress_match:
                        progress = int(progress_match.group(1))
                        mixer_session.processing_progress = progress
                        mixer_session.processing_message = f"音频分离中: {progress}%"
                    elif 'Processing' in line or 'loading' in line.lower() or 'Loading' in line:
                        mixer_session.processing_message = f"分离进行中: {line[:60]}..." if len(line) > 60 else f"分离进行中: {line}"
        
        process.wait()
        
        if process.returncode != 0:
            error_msg = "\\n".join(error_lines[-5:]) if error_lines else f"分离进程退出码: {process.returncode}"
            return False, error_msg
        
        return True, None
        
    except Exception as e:
        return False, f"分离进程启动失败: {str(e)}"


def delete_files_only(folder_path):
    """仅删除文件夹中的文件"""
    if not os.path.exists(folder_path):
        return
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"无法删除 {file_path}: {e}")


def process_audio_files_thread(config):
    """在后台线程中处理音频文件"""
    global mixer_session
    
    try:
        input_directory = config['inputDir']
        output_directory = config['outputDir']
        hardware_choice = config['hardware']
        channel_choice = config['channel']
        
        mixer_session.hardware_choice = hardware_choice
        mixer_session.input_directory = input_directory
        mixer_session.output_directory = output_directory
        mixer_session.channel_count = 5 if channel_choice == '1' else 7
        
        if mixer_session.channel_count == 5:
            mixer_session.default_config = get_default_channel_config_51()
        else:
            mixer_session.default_config = get_default_channel_config_71()
        
        audio_files_to_process = []
        files = [f for f in os.listdir(input_directory) if os.path.isfile(os.path.join(input_directory, f))]
        total_files = len(files)
        
        for idx, filename in enumerate(files):
            file_path = os.path.join(input_directory, filename)
            
            mixer_session.processing_message = f'正在处理: {filename}'
            mixer_session.processing_progress = f'{idx + 1}/{total_files}'
            
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            
            delete_files_only(temp_dir)
            
            original_base_name = os.path.splitext(filename)[0]
            
            safe_temp_name, safe_base_name = sanitize_filename(filename)
            
            temp_file_path = os.path.join(temp_dir, safe_temp_name)
            shutil.copy(file_path, temp_file_path)
            
            suffix = "_5.1.flac" if mixer_session.channel_count == 5 else "_7.1.flac"
            output_file = os.path.join(output_directory, original_base_name + suffix)
            
            if os.path.isfile(output_file):
                mixer_session.processing_message = f'跳过已存在: {filename}'
                delete_files_only(temp_dir)
                continue
            
            separate_dir = os.path.join(temp_dir, "separate", safe_base_name)
            need_separate = True
            
            for sound in ["vocals.wav", "bass.wav", "drums.wav", "guitar.wav", 
                         "instrumental.wav", "piano.wav", "other.wav"]:
                if os.path.isfile(os.path.join(separate_dir, sound)):
                    need_separate = False
                    break
            
            if need_separate:
                mixer_session.processing_message = f'正在分离: {filename}'
                mixer_session.processing_progress = 0
                success, error_msg = separate_audio_internal(temp_file_path, hardware_choice, mixer_session)
                
                if not success:
                    error_detail = f'{filename}: {error_msg}' if error_msg else f'{filename}: 分离失败（未知错误）'
                    mixer_session.failed_files.append(error_detail)
                    mixer_session.processing_message = f'分离失败: {filename}'
                    delete_files_only(temp_dir)
                    gc.collect()
                    continue
            
            audio_files_to_process.append({
                "name": original_base_name,
                "input_dir": separate_dir,
                "output_file": output_file
            })
            
            delete_files_only(temp_dir)
            gc.collect()
        
        mixer_session.audio_files = []
        for info in audio_files_to_process:
            af = AudioFile(info["name"], info["input_dir"], info["output_file"])
            af.channel_config = copy.deepcopy(mixer_session.default_config)
            mixer_session.audio_files.append(af)
        
        if mixer_session.audio_files:
            mixer_session.processing_message = '正在加载音频预览...'
            first_audio = mixer_session.audio_files[0]
            first_audio.source_segments = load_source_audio(first_audio.input_dir)
            first_audio.is_loaded = True
        
        mixer_session.is_ready = True
        mixer_session.processing_status = 'ready'
        
        success_count = len(mixer_session.audio_files)
        fail_count = len(mixer_session.failed_files)
        if fail_count > 0:
            mixer_session.processing_message = f'处理完成，成功 {success_count} 个，失败 {fail_count} 个'
            mixer_session.processing_error = '\n'.join(mixer_session.failed_files)
        else:
            mixer_session.processing_message = '处理完成'
            mixer_session.processing_error = ''
        
    except Exception as e:
        mixer_session.processing_status = 'error'
        mixer_session.processing_message = str(e)
        mixer_session.processing_error = str(e)
        print(f"处理错误: {e}")


@app.route('/api/start_processing', methods=['POST'])
def start_processing():
    """开始处理音频文件"""
    data = request.json
    
    if not data.get('inputDir') or not data.get('outputDir'):
        return jsonify({"status": "error", "error": "请选择输入和输出目录"})
    
    mixer_session.processing_status = 'processing'
    mixer_session.processing_message = '正在扫描音频文件...'
    mixer_session.processing_progress = ''
    mixer_session.processing_error = ''
    mixer_session.failed_files = []
    
    thread = threading.Thread(target=process_audio_files_thread, args=(data,))
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "ok"})


@app.route('/api/processing_status')
def processing_status():
    """获取处理状态"""
    return jsonify({
        "status": mixer_session.processing_status,
        "message": mixer_session.processing_message,
        "progress": mixer_session.processing_progress,
        "error": mixer_session.processing_error,
        "failed_files": mixer_session.failed_files
    })




@app.route('/api/status')
def get_status():
    """获取当前状态"""
    current = mixer_session.current_audio
    audio_list = [{
        "index": i,
        "name": af.name,
        "is_loaded": af.is_loaded,
        "export_completed": af.export_completed
    } for i, af in enumerate(mixer_session.audio_files)]
    
    return jsonify({
        "is_ready": mixer_session.is_ready,
        "channel_count": mixer_session.channel_count,
        "audio_files": audio_list,
        "current_audio_index": mixer_session.current_audio_index,
        "current_audio_name": current.name if current else None,
        "input_dir": current.input_dir if current else "",
        "output_file": current.output_file if current else "",
        "available_sources": list(k for k, v in (current.source_segments if current else {}).items() if v is not None),
        "all_exported": mixer_session.get_all_export_completed()
    })


@app.route('/api/audio_files')
def get_audio_files():
    """获取所有音频文件列表"""
    return jsonify({
        "audio_files": [{
            "index": i,
            "name": af.name,
            "is_loaded": af.is_loaded,
            "export_completed": af.export_completed,
            "output_file": af.output_file
        } for i, af in enumerate(mixer_session.audio_files)],
        "current_index": mixer_session.current_audio_index,
        "total": len(mixer_session.audio_files)
    })


@app.route('/api/select_audio/<int:index>', methods=['POST'])
def select_audio(index):
    """选择要编辑的音频文件"""
    if index < 0 or index >= len(mixer_session.audio_files):
        return jsonify({"error": "无效的音频索引"}), 400
    
    mixer_session.current_audio_index = index
    audio = mixer_session.current_audio
    
    if not audio.is_loaded:
        audio.source_segments = load_source_audio(audio.input_dir)
        audio.is_loaded = True
    
    return jsonify({
        "status": "ok",
        "name": audio.name,
        "channel_config": audio.channel_config,
        "is_loaded": audio.is_loaded
    })


@app.route('/api/config')
def get_config():
    """获取当前声道配置"""
    current = mixer_session.current_audio
    return jsonify({
        "channel_config": current.channel_config if current else {},
        "channel_count": mixer_session.channel_count,
        "default_config": mixer_session.default_config,
        "current_audio_name": current.name if current else None
    })


@app.route('/api/config', methods=['POST'])
def update_config():
    """更新当前音频的声道配置"""
    data = request.json
    current = mixer_session.current_audio
    if current:
        current.channel_config = data.get('channel_config', current.channel_config)
    return jsonify({"status": "ok"})


@app.route('/api/default_config')
def get_default_config():
    """获取服务器端默认配置"""
    return jsonify({
        "default_config": mixer_session.default_config,
        "channel_count": mixer_session.channel_count
    })


@app.route('/api/switch_channel_mode', methods=['POST'])
def switch_channel_mode():
    """切换声道模式 (5.1 <-> 7.1)"""
    data = request.json
    new_channel_count = data.get('channel_count')
    
    if new_channel_count not in [5, 7]:
        return jsonify({"error": "无效的声道数量"}), 400
    
    mixer_session.channel_count = new_channel_count
    
    if new_channel_count == 5:
        new_default_config = get_default_channel_config_51()
    else:
        new_default_config = get_default_channel_config_71()
    
    mixer_session.default_config = new_default_config
    
    suffix = "_5.1.flac" if new_channel_count == 5 else "_7.1.flac"
    for af in mixer_session.audio_files:
        af.channel_config = copy.deepcopy(new_default_config)
        base_name = af.name
        af.output_file = os.path.join(mixer_session.output_directory, base_name + suffix)
        af.export_completed = False
    
    return jsonify({
        "status": "ok",
        "channel_count": new_channel_count,
        "channel_config": new_default_config,
        "default_config": new_default_config
    })


@app.route('/api/apply_config_to_all', methods=['POST'])
def apply_config_to_all():
    """将当前配置应用到所有音频文件"""
    data = request.json
    config = data.get('channel_config')
    if not config:
        current = mixer_session.current_audio
        if current:
            config = current.channel_config
    
    if config:
        for af in mixer_session.audio_files:
            af.channel_config = copy.deepcopy(config)
        return jsonify({
            "status": "ok",
            "applied_to": len(mixer_session.audio_files)
        })
    return jsonify({"error": "没有可用的配置"}), 400


@app.route('/api/apply_config_to_remaining', methods=['POST'])
def apply_config_to_remaining():
    """将当前配置应用到所有未导出的音频文件"""
    data = request.json
    config = data.get('channel_config')
    if not config:
        current = mixer_session.current_audio
        if current:
            config = current.channel_config
    
    if config:
        count = 0
        for af in mixer_session.audio_files:
            if not af.export_completed:
                af.channel_config = copy.deepcopy(config)
                count += 1
        return jsonify({
            "status": "ok",
            "applied_to": count
        })
    return jsonify({"error": "没有可用的配置"}), 400


@app.route('/api/reset_to_default', methods=['POST'])
def reset_to_default():
    """重置当前音频的配置为服务器端默认配置"""
    current = mixer_session.current_audio
    if current:
        current.channel_config = copy.deepcopy(mixer_session.default_config)
        return jsonify({
            "status": "ok",
            "channel_config": current.channel_config
        })
    return jsonify({"error": "没有选中的音频"}), 400


@app.route('/api/preview', methods=['POST'])
def generate_preview():
    """生成预览音频"""
    current = mixer_session.current_audio
    if not mixer_session.is_ready or not current:
        return jsonify({"error": "会话未就绪"}), 400
    
    data = request.json
    if data and 'channel_config' in data:
        current.channel_config = data['channel_config']
    
    try:
        multi_channel = generate_preview_audio(
            current.source_segments,
            current.channel_config,
            mixer_session.channel_count
        )
        
        preview_path = os.path.join(mixer_session.temp_dir, "preview.wav")
        sf.write(preview_path, multi_channel, mixer_session.sample_rate)
        
        return jsonify({
            "status": "ok",
            "preview_url": "/api/preview_audio",
            "channels": mixer_session.channel_count + 1
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/preview_audio')
def get_preview_audio():
    """获取预览音频文件"""
    preview_path = os.path.join(mixer_session.temp_dir, "preview.wav")
    if os.path.exists(preview_path):
        return send_file(preview_path, mimetype='audio/wav')
    return jsonify({"error": "预览文件不存在"}), 404


@app.route('/api/source_audio/<source_name>')
def get_source_audio(source_name):
    """获取原始音源文件"""
    current = mixer_session.current_audio
    if not current:
        return jsonify({"error": "没有选中的音频"}), 404
    source_file = os.path.join(current.input_dir, f"{source_name}.wav")
    if os.path.exists(source_file):
        return send_file(source_file, mimetype='audio/wav')
    return jsonify({"error": "源文件不存在"}), 404


@app.route('/api/export', methods=['POST'])
def export_final():
    """导出当前音频的最终混音文件"""
    current = mixer_session.current_audio
    if not mixer_session.is_ready or not current:
        return jsonify({"error": "会话未就绪"}), 400
    
    data = request.json
    if data and 'channel_config' in data:
        current.channel_config = data['channel_config']
    
    try:
        multi_channel = generate_preview_audio(
            current.source_segments,
            current.channel_config,
            mixer_session.channel_count
        )
        
        sf.write(current.output_file, multi_channel, mixer_session.sample_rate, format='FLAC')
        
        current.export_completed = True
        
        return jsonify({
            "status": "ok",
            "output_file": current.output_file,
            "all_exported": mixer_session.get_all_export_completed()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/export_all', methods=['POST'])
def export_all():
    """导出所有音频文件"""
    if not mixer_session.is_ready:
        return jsonify({"error": "会话未就绪"}), 400
    
    results = []
    for i, af in enumerate(mixer_session.audio_files):
        if af.export_completed:
            results.append({"name": af.name, "status": "already_exported"})
            continue
        
        if not af.is_loaded:
            af.source_segments = load_source_audio(af.input_dir)
            af.is_loaded = True
        
        try:
            multi_channel = generate_preview_audio(
                af.source_segments,
                af.channel_config,
                mixer_session.channel_count
            )
            sf.write(af.output_file, multi_channel, mixer_session.sample_rate, format='FLAC')
            af.export_completed = True
            results.append({"name": af.name, "status": "ok", "output_file": af.output_file})
        except Exception as e:
            results.append({"name": af.name, "status": "error", "error": str(e)})
    
    return jsonify({
        "status": "ok",
        "results": results,
        "all_exported": mixer_session.get_all_export_completed()
    })


@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    """关闭服务器"""
    data = request.json or {}
    delete_temp = data.get('delete_temp', False)
    
    if delete_temp:
        import shutil
        temp_dir = os.path.join(os.getcwd(), 'temp')
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"已删除临时目录: {temp_dir}")
            except Exception as e:
                print(f"删除临时目录失败: {e}")
    
    mixer_session.should_exit = True
    return jsonify({"status": "shutting down"})


_server = None


def start_web_mixer(input_dir, output_file, channel_count, port=5000):
    """
    启动 Web 混音器（单文件模式 - 保持向后兼容）
    
    Parameters:
    ----------
    input_dir : str
        分离后的音频文件目录
    output_file : str
        输出文件路径
    channel_count : int
        声道数 (5 或 7)
    port : int
        Web 服务端口
    
    Returns:
    -------
    bool
        是否成功导出
    """
    audio_name = os.path.basename(os.path.dirname(output_file)) or "audio"
    audio_files = [{
        "name": audio_name,
        "input_dir": input_dir,
        "output_file": output_file
    }]
    return start_web_mixer_batch(audio_files, channel_count, port)


def start_web_mixer_batch(audio_files_info, channel_count, port=5000):
    """
    启动 Web 混音器（批量模式）
    
    Parameters:
    ----------
    audio_files_info : list
        音频文件信息列表，每项包含:
        - name: 音频文件名
        - input_dir: 分离后的音频目录
        - output_file: 输出文件路径
    channel_count : int
        声道数 (5 或 7)
    port : int
        Web 服务端口
    
    Returns:
    -------
    bool
        是否所有文件都成功导出
    """
    global mixer_session, _server
    
    mixer_session = MixerSession()
    mixer_session.channel_count = channel_count
    mixer_session.sample_rate = 48000
    
    if channel_count == 5:
        mixer_session.default_config = get_default_channel_config_51()
    else:
        mixer_session.default_config = get_default_channel_config_71()
    
    for info in audio_files_info:
        af = AudioFile(info["name"], info["input_dir"], info["output_file"])
        af.channel_config = copy.deepcopy(mixer_session.default_config)
        mixer_session.audio_files.append(af)
    
    if mixer_session.audio_files:
        first_audio = mixer_session.audio_files[0]
        print(f"正在加载音频文件: {first_audio.name}...")
        first_audio.source_segments = load_source_audio(first_audio.input_dir)
        first_audio.is_loaded = True
    
    mixer_session.is_ready = True
    
    file_count = len(audio_files_info)
    print(f"\n{'='*50}")
    print(f"Web 混音器已启动!")
    print(f"共 {file_count} 个音频文件待处理")
    print(f"请在浏览器中打开: http://localhost:{port}")
    print(f"{'='*50}\n")
    
    def open_browser():
        import time
        time.sleep(1)
        webbrowser.open(f'http://localhost:{port}')
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    def check_exit():
        import time
        while not mixer_session.should_exit:
            time.sleep(0.5)
        if _server:
            _server.shutdown()
    
    threading.Thread(target=check_exit, daemon=True).start()
    
    try:
        from werkzeug.serving import make_server
        _server = make_server('0.0.0.0', port, app, threaded=True)
        print(f"服务器启动在端口 {port}...")
        _server.serve_forever()
    except Exception as e:
        print(f"服务器已关闭: {e}")
    
    print("Web 混音器已关闭")
    
    return mixer_session.get_all_export_completed()


def start_web_mixer_setup(port=5000):
    """
    启动 Web 混音器（设置模式）
    从设置页面开始，用户在 Web GUI 中选择所有配置
    
    Parameters:
    ----------
    port : int
        Web 服务端口
    
    Returns:
    -------
    bool
        是否所有文件都成功导出
    """
    global mixer_session, _server, _tk_initialized
    
    mixer_session = MixerSession()
    mixer_session.setup_mode = True
    mixer_session.is_ready = False
    
    print(f"\n{'='*50}")
    print(f"多声道混音工具 Web GUI")
    print(f"请在浏览器中打开: http://localhost:{port}")
    print(f"{'='*50}\n")
    
    tk_root = Tk()
    tk_root.withdraw()
    _tk_initialized = True
    
    def open_browser():
        import time
        time.sleep(1)
        webbrowser.open(f'http://localhost:{port}')
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    def check_exit():
        import time
        while not mixer_session.should_exit:
            time.sleep(0.5)
        if _server:
            _server.shutdown()
        tk_root.quit()
    
    threading.Thread(target=check_exit, daemon=True).start()
    
    def run_server():
        global _server
        try:
            from werkzeug.serving import make_server
            _server = make_server('0.0.0.0', port, app, threaded=True)
            print(f"服务器启动在端口 {port}...")
            _server.serve_forever()
        except Exception as e:
            print(f"服务器已关闭: {e}")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    process_dir_requests(tk_root)
    try:
        tk_root.mainloop()
    except:
        pass
    
    print("Web 混音器已关闭")
    
    return mixer_session.get_all_export_completed()


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        input_dir = sys.argv[1]
        output_file = sys.argv[2]
        channel_count = int(sys.argv[3])
        start_web_mixer(input_dir, output_file, channel_count)
    elif len(sys.argv) == 2 and sys.argv[1] == '--setup':
        start_web_mixer_setup()
    else:
        start_web_mixer_setup()
