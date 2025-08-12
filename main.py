import shutil
import subprocess
import os
import sys
import gc
from pydub import AudioSegment
from tkinter import Tk, filedialog


def update_progress(current_step, total_steps):
    done = int(100 * current_step / total_steps)
    progress_bar = f"{'=' * done}{' ' * (100 - done)}"
    print(f"\r混音进度: [{progress_bar}] {done}%", end="")
    sys.stdout.flush()


def remix_channels(input_dir, output_file, channel_count):
    print(f"开始混音为 {channel_count}.1 通道，由 {input_dir} 到 {output_file}")

    total_steps = 5
    current_step = 0

    # 定义声道文件列表
    channels = ["vocals", "bass", "drums", "guitar", "instrumental", "piano", "other"]
    mono_segments = []

    for channel in channels:
        channel_file = os.path.join(input_dir, f"{channel}.wav")
        if os.path.isfile(channel_file):
            audio = AudioSegment.from_file(channel_file)
            mono_segments.append(audio)
        else:
            # 如果文件不存在，添加静音音频段作为占位符
            print(f"文件 {channel_file} 不存在，添加静音占位符")
            mono_segments.append(AudioSegment.silent(duration=0, frame_rate=48000))

    current_step += 1
    update_progress(current_step, total_steps)

    # 调整音频文件的采样率
    for i, segment in enumerate(mono_segments):
        mono_segments[i] = segment.set_frame_rate(48000)

    current_step += 1
    update_progress(current_step, total_steps)

    # 创建一个静音的声道音频对象（采样率 48kHz）
    silence = AudioSegment.silent(duration=len(mono_segments[0]), frame_rate=48000)

    current_step += 1
    update_progress(current_step, total_steps)

    # 混音为指定声道格式
    if channel_count == 5:
        # 中置声道：将 vocals 左右声道合并为单声道
        center_channel = AudioSegment.from_mono_audiosegments(
            mono_segments[0].set_channels(1)  # vocals
        ).set_channels(1)

        # 低音声道：将 bass 左右声道合并为单声道
        lfe_channel = AudioSegment.from_mono_audiosegments(
            mono_segments[1].set_channels(1)  # bass
        ).set_channels(1)

        # 左右主声道：使用 drums 的左右声道
        left_main = mono_segments[2].split_to_mono()[0].set_channels(1)  # drums 左声道
        right_main = mono_segments[2].split_to_mono()[1].set_channels(1)  # drums 右声道

        # 左右环绕声道：混合 piano、guitar、instrumental、other 和 vocals 的左右声道
        left_surround = AudioSegment.from_mono_audiosegments(
            mono_segments[5].split_to_mono()[0].set_channels(1),  # piano
            mono_segments[3].split_to_mono()[0].set_channels(1),  # guitar
            mono_segments[4].split_to_mono()[0].set_channels(1),  # instrumental
            mono_segments[6].split_to_mono()[0].set_channels(1),  # other
            mono_segments[0].split_to_mono()[0].set_channels(1),  # vocals
        ).set_channels(1)

        right_surround = AudioSegment.from_mono_audiosegments(
            mono_segments[5].split_to_mono()[1].set_channels(1),  # piano
            mono_segments[3].split_to_mono()[1].set_channels(1),  # guitar
            mono_segments[4].split_to_mono()[1].set_channels(1),  # instrumental
            mono_segments[6].split_to_mono()[1].set_channels(1),  # other
            mono_segments[0].split_to_mono()[1].set_channels(1),  # vocals
        ).set_channels(1)

        mono_segments = [
            left_main,  # 左前
            right_main,  # 右前
            center_channel,  # 中置
            lfe_channel,  # 低音
            left_surround,  # 左后
            right_surround,  # 右后
        ]

    elif channel_count == 7:
        # 中置声道：将 vocals 左右声道合并为单声道
        center_channel = AudioSegment.from_mono_audiosegments(
            mono_segments[0].set_channels(1)  # vocals
        ).set_channels(1)

        # 低音声道：将 bass 左右声道合并为单声道
        lfe_channel = AudioSegment.from_mono_audiosegments(
            mono_segments[1].set_channels(1)  # bass
        ).set_channels(1)

        # 左右主声道：使用 drums 的左右声道
        left_main = mono_segments[2].split_to_mono()[0].set_channels(1)  # drums 左声道
        right_main = mono_segments[2].split_to_mono()[1].set_channels(1)  # drums 右声道

        # 左右环绕声道：混合 piano、instrumental 和 vocals 的左右声道
        left_surround = AudioSegment.from_mono_audiosegments(
            mono_segments[4].split_to_mono()[0].set_channels(1),  # instrumental
            mono_segments[5].split_to_mono()[0].set_channels(1),  # piano
            mono_segments[0].split_to_mono()[0].set_channels(1),  # vocals
        ).set_channels(1)

        right_surround = AudioSegment.from_mono_audiosegments(
            mono_segments[4].split_to_mono()[1].set_channels(1),  # instrumental
            mono_segments[5].split_to_mono()[1].set_channels(1),  # piano
            mono_segments[0].split_to_mono()[1].set_channels(1),  # vocals
        ).set_channels(1)

        # 左后环绕和右后环绕：混合 guitar、other 和 vocals 的左右声道
        rear_left_surround = AudioSegment.from_mono_audiosegments(
            mono_segments[3].split_to_mono()[0].set_channels(1),  # guitar
            mono_segments[6].split_to_mono()[0].set_channels(1),  # other
            mono_segments[4].split_to_mono()[0].set_channels(1),  # instrumental
            mono_segments[0].split_to_mono()[0].set_channels(1),  # vocals
        ).set_channels(1)

        rear_right_surround = AudioSegment.from_mono_audiosegments(
            mono_segments[3].split_to_mono()[1].set_channels(1),  # guitar
            mono_segments[6].split_to_mono()[1].set_channels(1),  # other
            mono_segments[4].split_to_mono()[1].set_channels(1),  # instrumental
            mono_segments[0].split_to_mono()[1].set_channels(1),  # vocals
        ).set_channels(1)

        mono_segments = [
            left_main,  # 左前
            right_main,  # 右前
            center_channel,  # 中置
            lfe_channel,  # 低音
            left_surround,  # 左后
            right_surround,  # 右后
            rear_left_surround,  # 左后环绕
            rear_right_surround,  # 右后环绕
        ]

    current_step += 1
    update_progress(current_step, total_steps)

    mixed_audio = AudioSegment.from_mono_audiosegments(*mono_segments).set_channels(
        channel_count + 1
    )

    current_step += 1
    update_progress(current_step, total_steps)
    print()

    # 导出为多声道音频文件
    mixed_audio.export(output_file, format="flac")

    gc.collect()


def separate_audio(input_dir, hardware_choice):
    os.environ["TORCH_HOME"] = "./model"
    tempPath = "./temp/separate"
    if not os.path.exists(tempPath):
        os.mkdir(tempPath)

    if hardware_choice == "1":
        os.environ["PYTORCH_NO_CUDA_MEMORY_CACHING"] = "0"
        args = [
            ".\\Python\\python",
            "logic_bsroformer\\inference.py",
            "--model_type",
            "bs_roformer",
            "--config_path",
            "logic_bsroformer\\configs/logic_pro_config_v1.yaml",
            "--start_check_point",
            "logic_bsroformer\\models/logic_roformer.pt",
            "--input_folder",
            os.path.dirname(input_dir),
            "--store_dir",
            tempPath,
            "--extract_instrumental",
        ]
    elif hardware_choice == "2":
        args = [
            ".\\Python\\python",
            "logic_bsroformer\\inference.py",
            "--model_type",
            "bs_roformer",
            "--config_path",
            "logic_bsroformer\\configs/logic_pro_config_v1.yaml",
            "--start_check_point",
            "logic_bsroformer\\models/logic_roformer.pt",
            "--input_folder",
            os.path.dirname(input_dir),
            "--store_dir",
            tempPath,
            "--extract_instrumental",
            "--force_cpu",
        ]
    else:
        args = []

    if args:
        print(f"执行命令: {' '.join(args)}")
        result = subprocess.run(args, check=True)


def delete_files_only(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # 删除文件或符号链接
            # 如果是目录则不处理
        except Exception as e:
            print(f"无法删除 {file_path}. 原因: {e}")


def main(isContinue=0):
    hardware_choice = ""
    choice = ""
    if isContinue == 0 or isContinue == 2:
        print("立体声转5.1声道&7.1声道混音工具 v2.0 by 陈缘科技")
        print()

        hardware_choice = input(
            "请选择处理模式：\n1 .GPU (3G 以上显存推荐)\n2 .CPU\n> "
        )
        if hardware_choice not in ["1", "2"]:
            print("\n输入错误，请重新输入")
            main(2)

        choice = input("请选择混音模式：\n1. 2 TO 5.1\n2. 2 TO 7.1\n> ")
        if choice not in ["1", "2"]:
            print("\n输入错误，请重新输入")
            main(2)

    elif isContinue == 1:
        print("继续处理...")

    # 创建Tk实例并隐藏主窗口
    root = Tk()
    root.withdraw()

    print("请选择需要转换的音频文件所在目录")
    input_directory = filedialog.askdirectory(
        title="选择音频文件所在目录", initialdir="."
    )
    print("请选择输出目录")
    output_directory = filedialog.askdirectory(title="选择输出目录", initialdir=".")

    for filename in os.listdir(input_directory):
        file_path = os.path.join(input_directory, filename)
        if not os.path.isfile(file_path):
            print(f"跳过子文件夹: {filename}")
            continue

        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, filename)

        # 删除临时目录中的复制音频文件
        delete_files_only(temp_dir)

        # 复制文件到临时目录
        shutil.copy(file_path, temp_file_path)

        isfull = False

        # 检查输出目录下是否已存在最终输出的音频文件
        output_file_51 = os.path.join(
            output_directory, filename.split(".")[0] + "_5.1.flac"
        )
        output_file_71 = os.path.join(
            output_directory, filename.split(".")[0] + "_7.1.flac"
        )
        if os.path.isfile(output_file_51) or os.path.isfile(output_file_71):
            print(f"最终输出的音频文件已存在，跳过文件: {filename}")

            delete_files_only(temp_dir)

            # 清理分离后的音频文件
            separate_dir = os.path.join(temp_dir, "separate", filename.split(".")[0])
            if os.path.exists(separate_dir):
                delete_files_only(separate_dir)
                os.rmdir(separate_dir)
                print(f"已删除分离后的音频文件")

            continue

        print(f"正在处理文件: {filename}")

        for sound in [
            "vocals.wav",
            "bass.wav",
            "drums.wav",
            "guitar.wav",
            "instrumental.wav",
            "piano.wav",
            "other.wav",
        ]:
            if os.path.isfile(
                os.path.join(temp_dir, "separate", filename.split(".")[0], sound)
            ):
                isfull = True
                print(f"{filename} 分离音频文件 {sound} 已存在，跳过分离")

        if not isfull:
            separate_audio(
                temp_file_path,
                hardware_choice,
            )

        if choice == "1":
            output_file = os.path.join(
                output_directory, filename.split(".")[0] + "_5.1.flac"
            )
            if not os.path.isfile(output_file):
                remix_channels(
                    os.path.join(temp_dir, "separate", filename.split(".")[0]),
                    output_file,
                    5,
                )
            else:
                print(f"\n5.1混音已存在，请查看输出文件 {output_file}")

        elif choice == "2":
            output_file = os.path.join(
                output_directory, filename.split(".")[0] + "_7.1.flac"
            )
            if not os.path.isfile(output_file):
                remix_channels(
                    os.path.join(temp_dir, "separate", filename.split(".")[0]),
                    output_file,
                    7,
                )
            else:
                print(f"\n7.1混音已存在，请查看输出文件 {output_file}")

        delete_files_only(temp_dir)
        print("temp 中留有分离的音频文件，可自行删除，或者程序再次运行将自动清理")

        gc.collect()

    input("按任意键退出...")


if __name__ == "__main__":
    main()
