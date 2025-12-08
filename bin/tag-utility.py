import os
import re
import shutil


def find_and_replace(inputfile: str, outputfile: str, dryrun=True) -> None:
    # Prepare regular expression for finding and replacing lines starting “tags” string  
    tagPattern = re.compile('^tags:\s*.*$')
    if dryrun:
        print(f"Dry Run: Would process file {inputfile} and write to {outputfile}")
        inputfile = outputfile
        outputfile = "/home/scott/dryrun_output.md"  # Dummy output file for dry run
    with open(inputfile, 'r') as input:
        with open(outputfile, 'w', newline='') as out:
            for line in input:
                matchObject = tagPattern.match(line)  # check if the current text matches our pattern
                if matchObject is not None:  # found a matching string
                    tags = [x.strip() for x in line[len('tags:'):].split(",")]
                    for i in range(0, len(tags), 2):
                        _str = f"[tag:{tags[i].strip()}]"
                        if dryrun:
                            print(f"Dry Run: Would write tag: {_str}")
                        else:
                            out.write(f"{_str}\n")  # write each tag on a new line
                # otherwise write line as it was
                else:
                    if dryrun:
                        print(f"Dry Run: Would write line: {line.strip()}")
                    else:
                        out.write(line.strip() + "\n")


def backup_markdown_file(root: str, filename: str, dryrun=True) -> None:
    try:
        src = os.path.join(root, filename)
        dest = os.path.join(root, filename + '.bak')
        if dryrun:
            print(f"Dry Run: Would copy {src} to {dest}")
        else:
            shutil.copy(src, dest)  # copy the source markdown file
    except Exception as e:
        print(f"Error occurred while backing up file {filename}: {e}")


if __name__ == "__main__":
    # Walk through the directory and its contents, looking for .md files
    dryrun = True
    directory = "/mnt/raid1/lib/tasks.md/tasks"
    for root, dirs, files in os.walk(directory):
        print('Searching:', root)
        for file in files:
            if file.endswith(".md"):
                # Print full path of the markdown file found                            
                print("Markdown File Found!", os.path.join(root, file))
                backup_markdown_file(root, file, dryrun)
                filepath = os.path.join(root, file)
                find_and_replace(filepath + ".bak", filepath, dryrun)
