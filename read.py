import docx2txt, os
import json
from unpack_json import json_unpack
from tika import parser

FOLDER = os.environ.get("CORPUS_INPUT_FOLDER", "input_files")
FILE_NAME = os.environ.get("CORPUS_OUTPUT_FILE", "output.txt")

if os.path.isfile(FILE_NAME):
    print(f"not regenerating '{FILE_NAME}' as it already exists")
else:
    output = open(FILE_NAME, "w", encoding='utf-8')

    for entry in os.scandir(FOLDER):
        if entry.name.endswith(".docx"):
            text = docx2txt.process(entry.path)
        # load json file
        elif entry.name.endswith(".json"):
            with open(entry.path, 'r', encoding='utf8') as j: 
                contents = json.loads(j.read())
                text = json_unpack(contents)
        # load pdf file
        elif entry.name.endswith(".pdf"):
            pdf = parser.from_file(entry.path)
            text = pdf["content"]
        # otherwise 
        else:
            with open(entry.path, 'r', encoding='utf-8') as f:
                text = f.read()

        text = text.replace("\n", "   ")

        source_file = entry.path.split("/")[-1]

        output.write(f"===SOURCE-FILE:{source_file}===\n")
        output.write(text + "\n")

    output.close()