import docx2txt, os

output = open("output.txt", "w")

for entry in os.scandir("input_files"):
    text = docx2txt.process(entry.path)

    text = text.replace("\n", " ")
    
    source_file = entry.path.split("/")[-1]

    output.write(f"===SOURCE-FILE:{source_file}===\n")
    output.write(text + "\n")

output.close()