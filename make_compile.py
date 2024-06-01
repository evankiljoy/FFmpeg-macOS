from argparse import ArgumentParser
from multiprocessing import cpu_count
import urllib.request
import tarfile
import pathlib
import sys
import os


def execute(command: str):
    print(f"Execute: {command}.")
    os.system(command)

def download_file(url, local_path):
    # Open the URL
    with urllib.request.urlopen(url) as response:
        # Get the total file size from the header
        file_size = int(response.headers.get('Content-Length', 0))

        # Check if we actually got a valid content length
        if file_size == 0:
            print("Unable to retrieve file size - progress will not be shown.")

        print(f"Downloading: {url}")
        # Open the local file for writing in binary mode
        with open(local_path, 'wb') as out_file:
            # Read and write the content in chunks
            while chunk := response.read(8192):
                out_file.write(chunk)

def collect_sdk(sdk_version):
    dl_path = f"https://github.com/phracker/MacOSX-SDKs/releases/download/11.3/MacOSX{sdk_version}.sdk.tar.xz"
    dest_path = f"/tmp/MacOSX{sdk_version}.sdk.tar.xz"
    
    # Download the file
    download_file(dl_path, dest_path)
    
    # Untar the file
    with tarfile.open(dest_path, 'r:xz') as tar:
        tar.extractall(path='/tmp')
    
    print(f"SDK version {sdk_version} collected and extracted to /tmp")
    

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


    def make(arch: str, config: str):
        n_cpu = cpu_count()
        print("Configure project.")
        osx_version = "10.12" if arch == "x86_64" else "11.0"
        collect_sdk(osx_version)
        osx_sdk = f"/tmp/MacOSX{osx_version}.sdk"
        config_opts = f"--optflags='-Og' --disable-stripping" if config == "Debug" else f"--disable-debug"
        prefix_path = target_dir / f'install_{config}_{arch}/'
        build_opts = [
            f"--enable-cross-compile",
            f"--prefix={prefix_path}",
            f"--enable-shared",
            f"--disable-static",
            f"--arch={arch}",
            f"--cc='clang -arch {arch}'",
            f"--disable-programs",
            f"--disable-avdevice",
            f"--enable-opencl",
            f"--enable-lto",
            f"--extra-ldflags='-isysroot {osx_sdk} -mmacosx-version-min={osx_version} -flto -fuse-linker-plugin'",
            f"--extra-cflags='-isysroot {osx_sdk} -mmacosx-version-min={osx_version}'",
            config_pts
        ]
        execute(
            f"cd {ffmpeg_dir} && ./configure {' '.join(build_opts)}"
        )
        print(f"Make project ({n_cpu} threads).")
        execute(f"cd {ffmpeg_dir} && make -j{n_cpu}")
        print(f"Install project.")
        execute(f"cd {ffmpeg_dir} && make install")


    for config in ["Release", "Debug"]:
        print(f"----------arm64/{config}----------")
        clean()
        make("arm64", config)
        print(f"----------x86_64/{config}----------")
        clean()
        make("x86_64")
