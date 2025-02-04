import os
import shutil
import argparse
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
import eyed3
from tqdm import tqdm

def has_embedded_lyrics(audio):
    if isinstance(audio, FLAC):
        return 'LYRICS' in audio
    elif isinstance(audio, MP4):
        return '\xa9lyr' in audio.tags
    elif isinstance(audio, eyed3.core.AudioFile):
        return audio.tag.lyrics is not None
    return False

def embed_lrc(directory, skip_existing, reduce_lrc, recursive):
    total_audio_files = 0
    embedded_lyrics_files = 0
    failed_files = []
    
    audio_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.flac') or file.endswith('.mp3') or file.endswith('.m4a'):
                audio_files.append(os.path.join(root, file))
    
    with tqdm(total=len(audio_files), desc='Embedding LRC files', unit='file') as pbar:
        for audio_path in audio_files:
            file = os.path.basename(audio_path)
            lrc_file = os.path.splitext(file)[0] + '.lrc'
            lrc_path = os.path.join(os.path.dirname(audio_path), lrc_file)
            
            if os.path.exists(lrc_path):
                if skip_existing:
                    audio = None
                    if file.endswith('.flac'):
                        audio = FLAC(audio_path)
                    elif file.endswith('.mp3'):
                        audio = eyed3.load(audio_path)
                    elif file.endswith('.m4a'):
                        audio = MP4(audio_path)
                    if has_embedded_lyrics(audio):
                        pbar.set_postfix({"status": "skipped"})
                        pbar.update(1)
                        continue
                
                try:
                    if file.endswith('.flac'):
                        audio = FLAC(audio_path)
                        audio['LYRICS'] = open(lrc_path, 'r', encoding='utf-8').read()
                        audio.save()
                    elif file.endswith('.mp3'):
                        audio = eyed3.load(audio_path)
                        tag = audio.tag
                        tag.lyrics.set(open(lrc_path, 'r', encoding='utf-8').read())
                        tag.save(version=eyed3.id3.ID3_V2_3)
                    elif file.endswith('.m4a'):
                        audio = MP4(audio_path)
                        audio.tags['\xa9lyr'] = open(lrc_path, 'r', encoding='utf-8').read()
                        audio.save()
                    
                    embedded_lyrics_files += 1
                    pbar.set_postfix({"status": f"embedded: {file}"})
                    pbar.update(1)
                    pbar.refresh()
                    
                    if reduce_lrc:
                        os.remove(lrc_path)
                        pbar.set_postfix({"status": f"embedded, LRC reduced: {file}"})
                        pbar.update(1)
                        pbar.refresh()
                
                except Exception as e:
                    print(f"Error embedding LRC for {file}: {str(e)}")
                    pbar.set_postfix({"status": f"error: {file}"})
                    pbar.update(1)
                    pbar.refresh()
                    failed_files.append(file)
                    if os.path.exists(lrc_path):
                        shutil.move(lrc_path, lrc_path + ".failed")
                    continue

    return len(audio_files), embedded_lyrics_files, failed_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Embed LRC files into audio files (FLAC, MP3, and M4A) and optionally reduce LRC files.')
    parser.add_argument('-d', '--directory', required=True, help='Directory containing audio and LRC files')
    parser.add_argument('-s', '--skip', action='store_true', help='Skip files that already have embedded lyrics')
    parser.add_argument('-r', '--reduce', action='store_true', help='Reduce (delete) LRC files after embedding')
    parser.add_argument('-R', '--recursive', action='store_true', help='Recursively process subdirectories')
    args = parser.parse_args()
    
    banner = """
██╗     ██████╗  ██████╗██████╗ ██╗   ██╗████████╗
██║     ██╔══██╗██╔════╝██╔══██╗██║   ██║╚══██╔══╝
██║     ██████╔╝██║     ██████╔╝██║   ██║   ██║   
██║     ██╔══██╗██║     ██╔═══╝ ██║   ██║   ██║   
███████╗██║  ██║╚██████╗██║     ╚██████╔╝   ██║   
╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝      ╚═════╝    ╚═╝   
Scripted by TheRedSpy15"""
    print(banner)

    directory_path = args.directory
    skip_existing = args.skip
    reduce_lrc = args.reduce
    recursive = args.recursive
    total, embedded, failed = embed_lrc(directory_path, skip_existing, reduce_lrc, recursive)
    percentage = (embedded / total) * 100 if total > 0 else 0
    
    print(f"Total audio files: {total}")
    print(f"Embedded lyrics in {embedded} audio files.")
    print(f"Percentage of audio files with embedded lyrics: {percentage:.2f}%")
    
    if failed:
        print("\nFailed to embed LRC for the following files:")
        for file in failed:
            print(file)
