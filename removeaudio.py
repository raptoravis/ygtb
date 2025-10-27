import argparse
import os
import glob
import re
from moviepy.editor import VideoFileClip


def remove_audio(src_mp4_file: str, output_dir: str):
    if os.path.exists(src_mp4_file) and os.path.isfile(src_mp4_file):
        try:
            videoclip = VideoFileClip(src_mp4_file)
            new_clip = videoclip.without_audio()

            src_file_basename = os.path.basename(src_mp4_file)
            output_file = os.path.join(output_dir, src_file_basename)

            # print(f"remove audio {src_mp4_file} -> {output_file} ...")
            # new_clip.write_videofile(output_file, verbose=False, logger=None)
            new_clip.write_videofile(output_file, verbose=False)
            pass
        except Exception as ex:
            print(ex)
    else:
        print(f"{src_mp4_file} not exists or not a file")
    pass


def rename_file(file_name) -> str:
    if os.path.isfile(file_name):
        dn = os.path.dirname(file_name)
        base, ext = os.path.splitext(os.path.basename(file_name))
        base_fn = re.sub(
            r"twitter_(.+)_(\d+)-(\d+)_(\d+)_.*",
            r"x_\2_\3_\4",
            base,
        )

        if base_fn and base_fn != base:
            new_file_name = os.path.join(dn, base_fn)
            new_file_name = new_file_name + ext
            try:
                os.rename(file_name, new_file_name)
                print(f"{file_name} -> {new_file_name}")
                return new_file_name
            except Exception as ex:
                print(f"{ex} when renaming {file_name}")
        return file_name

    return None


def handle_dir(src_dir: str, out_dir: str, dirmp4: str = None, log: bool = True):
    try:
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
            pass
    except Exception as ex:
        print(ex)
        return False

    wild_dir: str = os.path.join(src_dir, "*.mp4")
    if log:
        print(f"remove audio from {wild_dir} and output to {out_dir}")

    files = []
    for file_name in glob.iglob(wild_dir, recursive=False):
        if os.path.isfile(file_name):
            fn = rename_file(file_name)
            files.append(fn)
            pass
        pass
    pass

    if dirmp4:
        files_new = []
        for f in files:
            if os.path.exists(f) and os.path.isfile(f):
                try:
                    src_file_basename = os.path.basename(f)
                    output_file = os.path.join(dirmp4, src_file_basename)
                    print(f"{f} -> {output_file}")
                    os.rename(f, output_file)
                    files_new.append(output_file)
                except Exception as ex:
                    print(ex)
            pass

        files = [*files_new]
        pass

    for f in files:
        remove_audio(f, out_dir)
        pass

    return True


def handle_dir_move(src_dir: str, out_dir: str):
    print(f"move non-mp4 files from {src_dir} to {out_dir}")

    # wild_dir: str = os.path.join(src_dir, "[!*.mp4]")
    wild_dir: str = os.path.join(src_dir, "**")

    files = []
    for file_name in glob.iglob(wild_dir, recursive=False):
        # if os.path.isfile(file_name) and file_name.find(".mp4") == -1:
        if os.path.isfile(file_name):
            file_base_name, ext = os.path.splitext(os.path.basename(file_name))
            # print(file_name, file_base_name, ext)
            # if ext.lower() != ".mp4":
            if ext.lower() in [".jpg", ".jpeg", ".png"]:
                fn = rename_file(file_name)
                files.append(fn)
            pass
        pass
    pass

    for f in files:
        if os.path.exists(f) and os.path.isfile(f):
            try:
                src_file_basename = os.path.basename(f)
                output_file = os.path.join(out_dir, src_file_basename)
                print(f"{f} -> {output_file}")
                os.rename(f, output_file)
            except Exception as ex:
                print(ex)
        pass

    pass


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--src",
        type=str,
        required=True,
        help="source directory with *.mp4 and pictures",
    )
    parser.add_argument("--out", type=str, required=True, help="output directory")
    parser.add_argument("--dirmp4", type=str, required=False, help="output direction")
    parser.add_argument("--move", help="move non-mp4 files", action="store_true")

    args = parser.parse_args()

    #     # parser.print_usage()
    #     parser.print_help()

    handle_dir(args.src, args.out, dirmp4=args.dirmp4)

    if args.move:
        handle_dir_move(args.src, args.out)
        pass

    pass


if __name__ == "__main__":
    main()
    pass
