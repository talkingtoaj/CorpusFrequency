file_contents = []

with open("output.txt", "r") as file:
    file_contents = file.read().split("\n")

file_contents = [(file_contents[2*index], file_contents[2*index+1]) for index in range(int(len(file_contents)/2))]


def search(phrase):
    phrase = phrase.replace("%20", " ")
    results = []
    for name, content in file_contents:
        lower_content = content.lower()
        upto = 0
        while True:
            location = lower_content.find(phrase, upto)
            if location == -1: break
            results.append({
                "fileName": name, 
                "phrase": content[max(0, location-100): location + 100]
            })
            upto = location + 1
    return results
