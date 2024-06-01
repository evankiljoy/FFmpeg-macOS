from argparse import ArgumentParser
from multiprocessing import cpu_count
import pathlib
import sys
import os


def execute(command: str):
    print(f"Execute: {command}.")
    os.system(command)

def get_macos_sdk_path():
    try:
        sdk_path = subprocess.check_output(['xcrun', '--show-sdk-path']).strip()
        return sdk_path.decode('utf-8')
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"An error occurred: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    parser = ArgumentParser(description="Configure & Make & Install FFmpeg.")
    parser.add_argument("--ffmpeg_dir", type=str, default=os.getcwd(), help='indicate FFmpeg dir.')
    parser.add_argument("--target_dir", type=str, default=os.getcwd(), help='indicate target dir.')
    args = parser.parse_args()
    ffmpeg_dir = pathlib.Path(args.ffmpeg_dir).absolute()
    target_dir = pathlib.Path(args.target_dir).absolute()
    print(f"Compile... {ffmpeg_dir}")


    def clean():
        print("Clean project.")
        execute(f"cd {ffmpeg_dir} && make clean && make distclean")


    def make(arch: str):
        n_cpu = cpu_count()
        print("Configure project.")
        osx_sdk = get_macos_sdk_path()
        osx_version = "10.12" if arch == "x86_64" else "11.0"
        execute(
            f"cd {ffmpeg_dir} && ./configure --enable-cross-compile --prefix={target_dir / ('install_' + arch + '/')} "
            f"--enable-shared --disable-static --arch={arch} --cc='clang -arch {arch}' "
            f"--disable-programs --disable-avdevice --enable-avresample --enable-opencl --enable-lto "
            f"--extra-ldflags='-isysroot {osx_sdk} -mmacosx-version-min={osx_version} -flto -fuse-linker-plugin' "
            f"--extra-cflags='-isysroot {osx_sdk} -mmacosx-version-min={osx_version}' "
        )
        print(f"Make project ({n_cpu} threads).")
        execute(f"cd {ffmpeg_dir} && make -j{n_cpu}")
        print(f"Install project.")
        execute(f"cd {ffmpeg_dir} && make install")


    print("----------arm64----------")
    clean()
    make("arm64")
    print("----------x86_64----------")
    clean()
    make("x86_64")
