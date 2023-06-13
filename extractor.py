import patoolib
import os

def extract_archives(directory):
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            if filename.endswith(".7z") or filename.endswith(".zip") or filename.endswith(".rar"):
                output_path = f"./mods/{filename.replace(' ', '-').replace('.', '-')[:-3]}"
                if not os.path.exists(output_path):
                    os.mkdir(output_path)
                patoolib.extract_archive(filepath, outdir=output_path)

if __name__ == "__main__":
    extract_archives('./downloads')