import docx2txt, os

FOLDER = "input_files"
FILE_NAME = "output.txt"

if os.path.isfile(FILE_NAME):
    print(f"not regenerating '{FILE_NAME}' as it already exists")
else:
    output = open(FILE_NAME, "w")

    for entry in os.scandir(FOLDER):
        text = docx2txt.process(entry.path)

        text = text.replace("\n", " ")
        while text.count("  ") != 0:
            text = text.replace("  ", " ")

        source_file = entry.path.split("/")[-1]

        output.write(f"===SOURCE-FILE:{source_file}===\n")
        output.write(text + "\n")

    output.close()