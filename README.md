# CUE files fixer

Classic problem with .cue file is that people rip a CD to a wav file and create the cue file which refers to the wav in the FILE section, and then convert the wav to flac. This procedure comes from the old filesharing days when people used to burn audio CD-Rs from such downloads, after converting the flac back to wav. This procedure leads to invalid .cue file that point to absent file.wav file while only file.flac present.
 

In that case, one needs to open the cue file with any text editor and check the FILE entry is the same as the actual name of the music file.

This script allow you to automate this procedure


## Dependencies
```bash
pip install -r requirements.txt
```

## Usage
To fix all the cue files in your Music directory: 
```bash
./fix_cue_files.py ~/Music
```
