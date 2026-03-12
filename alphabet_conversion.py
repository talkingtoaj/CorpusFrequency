turkey = {
    'A': 'a', 'B': 'b', 'C':'c', 'Ç': 'ç','D': 'd','E': 'e','F': 'f','G': 'g','Ğ': 'ğ','H':'h','I':'ı','İ': 'i', 'J':'j','K': 'k', 'L':'l', 'M':'m','N':'n', 'O':'o','Ö': 'ö','P': 'p','R': 'r','S': 's','Ş': 'ş','T': 't','U': 'u','Ü': 'ü','V':'v','Y': 'y','Z':'z',
    'a':'a', 'b':'b', 'c':'c', 'ç': 'ç', 'd': 'd', 'e':'e', 'f':'f','g':'g','ğ':'ğ','h':'h','ı':'ı', 'i':'i', 'j': 'j','k':'k','l':'l','m':'m','n':'n','o':'o','ö':'ö','p':'p','r':'r','s':'s','ş':'ş','t':'t','u':'u','ü':'ü','v':'v','y':'y','z':'z',' ':' '
} #Dictionary mapping lower cae to upper case and lower case to lower case for effective selection#

def convert_to_lower_case(sentence):
    #function converting upper case to lower case 
    lower_case_list = []
    for letter in sentence:
        if letter in turkey:
            lower_case_list.append(turkey[letter])
        else:
            lower_case_list.append(letter)
    return ''.join(lower_case_list) 
