"""
立体声转5.1&7.1声道混音工具 v3.1.0 by ChanTrail
Web GUI 版本
"""

from web_mixer import start_web_mixer_setup


def main():
    print("=" * 50)
    print("立体声转5.1&7.1声道混音工具 v3.1.0")
    print("by ChanTrail")
    print("=" * 50)
    print()
    print("正在启动 Web GUI...")
    print()

    start_web_mixer_setup()


if __name__ == "__main__":
    main()
