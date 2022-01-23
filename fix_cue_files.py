#! /usr/bin/env python
import argparse
import csv
import logging
import os
import shutil
from io import StringIO

from chardet.universaldetector import UniversalDetector

logging.basicConfig(format="%(levelname)s - %(msg)s", level=logging.INFO)
logger = logging.getLogger("app")


def guess_encoding(detector: UniversalDetector, path: str) -> str:
    detector.reset()
    with open(path, 'rb') as f:
        for line in f:
            detector.feed(line)
            if detector.done:
                break

    detector.close()
    return detector.result['encoding']


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", help="Directory with .cue files to fix")

    return parser


def read_file_cue(cue_file_path: str) -> str:
    """Reads target audio file name from cue file content.

    Example input:
        FILE "The Beatles - Yellow Submarine.wav" WAVE

    Output:
        The Beatles - Yellow Submarine.wav
    """
    with open(cue_file_path, encoding=guess_encoding(detector=detector, path=cue_file_path)) as f:
        for line in f:
            if line.startswith("FILE "):
                reader = csv.DictReader(
                    StringIO(line),
                    fieldnames=["FILE_command", "filename", "filetype"],
                    delimiter=" ",
                )
                for row in reader:
                    return row['filename']


def set_file_cue(cue_file_path: str, audio_file_name: str, backup: bool = True):
    """Sets target audio file name in cue file, in place.

    Cue file:
        The Beatles - Yellow Submarine.cue

    FILE command line inside (before):
        FILE "The Beatles - Yellow Submarine.wav" WAVE

    function called with parameters:
        set_file_cue("The Beatles - Yellow Submarine.cue", "The Beatles - Yellow Submarine.flac")

    FILE command line inside (after):
        FILE "The Beatles - Yellow Submarine.flac" WAVE

    """
    if backup:
        shutil.copy(cue_file_path, f"{cue_file_path}.bak")

    encoding = guess_encoding(detector=detector, path=cue_file_path)
    lines = []
    with open(cue_file_path, encoding=encoding) as f:
        for line in f:
            lines.append(line)
            if line.startswith("FILE "):
                reader = csv.DictReader(
                    StringIO(line),
                    fieldnames=["FILE_command", "filename", "filetype"],
                    delimiter=" ",
                )
                for row in reader:
                    file_command_row_dict = row
                    break

    target_file_command_row_dict = file_command_row_dict.copy()
    target_file_command_row_dict["filename"] = audio_file_name

    with open(cue_file_path, encoding=encoding, mode="w") as f:
        for line in lines:
            if line.startswith("FILE "):
                writer = csv.DictWriter(
                    f,
                    fieldnames=["FILE_command", "filename", "filetype"],
                    delimiter=" ",
                )
                writer.writerow(target_file_command_row_dict)
                continue

            f.writelines([line])


if __name__ == '__main__':
    parser = make_parser()
    args = parser.parse_args()

    source_dir_path = os.path.abspath(os.path.expanduser(args.dir))

    detector = UniversalDetector()
    for dir_path, _, filenames in os.walk(source_dir_path):
        cue_filenames = [name for name in filenames if name.endswith('.cue')]
        for cue_filename in cue_filenames:
            cue_file_path = os.path.join(dir_path, cue_filename)
            target_audio_filename = read_file_cue(cue_file_path)

            target_audio_filepath = os.path.join(dir_path, target_audio_filename)
            if os.path.exists(target_audio_filepath):
                continue

            # try to find .flac with the same name
            flac_filename_candidate = f"{os.path.splitext(target_audio_filename)[0]}.flac"
            if not os.path.exists(os.path.join(dir_path, flac_filename_candidate)):
                # no luck, can't fix
                msg = f"Target audio file not found. Cue file: {cue_file_path}, " \
                      f"current audio file set: {target_audio_filename}"
                logger.error(msg)
                continue

            # fix .cue file by replacing filename in FILE command
            set_file_cue(cue_file_path=cue_file_path, audio_file_name=flac_filename_candidate)
            msg = f"Cue file: {cue_file_path}, " \
                  f"previous audio file set: {target_audio_filename}, " \
                  f"new audio file set: {flac_filename_candidate}"
            logger.info(msg)
