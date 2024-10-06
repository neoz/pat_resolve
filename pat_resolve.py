import os
import re
import sys
import google.generativeai as client
from ratelimit import limits, sleep_and_retry

CALLS = 1
RATE_LIMIT = 1
TEST_MODE = False

#template = "Given the following list of function names: {list}. Choose the most appropriate name in the list and respond only with choosen name string."
template = "Given the following list of list function names: {list}. From each list ,choose the most appropriate name in the list and respond only with choosen name string with seperate by comma."

model_name = "gemini-1.5-flash"

api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    raise ValueError("API key is required, please set the GEMINI_API_KEY environment variable")

# Set API key cho google-generativeai
client.configure(api_key=api_key)
model = client.GenerativeModel(model_name=model_name)

@sleep_and_retry
@limits(calls=CALLS, period=RATE_LIMIT)
def query(groups : list, isTest = True) -> str:
    lst_str = str(groups)
    input = template.format(list=lst_str)
    print("----- Request -----")
    print(input)
    if isTest:
        return "Test, Test1, Test2"
    response = model.generate_content(contents=input)
    resp_text = response.text #response.text.replace('```json\n', '').replace('```', '')
    print("----- Response -----")
    print(resp_text)
    return resp_text

def handle_exclude(file_content : str, names_to_exclude : str) -> str:
    names = names_to_exclude.split(',')
    for name in names:
        if name.startswith("sub_"):
            continue
        format_name = name.strip()

        # check if format_name is unique in the file
        if file_content.startswith(format_name):
            # only replace the first occurence
            file_content = file_content.replace(format_name, '+'+format_name, 1)
        elif file_content.count(format_name) == 1:
            file_content = file_content.replace(format_name, '+'+format_name)
        elif file_content.count('\n'+format_name+" ") == 1:
            file_content = file_content.replace('\n'+format_name+" ", '\n+'+format_name+" ")
        elif file_content.count('\n'+format_name+"\t") == 1:
            file_content = file_content.replace('\n'+format_name+"\t", '\n+'+format_name+"\t")

    # also remove the follow line
    # ;--------- (delete these lines to allow sigmake to read this file)
    # ; add '+' at the start of a line to select a module
    # ; add '-' if you are not sure about the selection
    # ; do nothing if you want to exclude all modules

    file_content = file_content.replace(";--------- (delete these lines to allow sigmake to read this file)\n", "")
    file_content = file_content.replace("; add '+' at the start of a line to select a module\n", "")
    file_content = file_content.replace("; add '-' if you are not sure about the selection\n", "")
    file_content = file_content.replace("; do nothing if you want to exclude all modules\n", "")

    return file_content
    
if __name__ == '__main__': 
    if TEST_MODE:
        print(f"Test mode: {TEST_MODE}")

    if len(sys.argv) != 2:
        print("Usage: python pat_resolve.py <file_name>")
        print("\t<file_name>: file exc needed to be resolved (*.exc)")
        sys.exit(1)

    # get file name from argument
    file_name = sys.argv[1]
    # check if not exist then raise error
    if not os.path.isfile(file_name):
        raise ValueError(f"File {file_name} not found")

    with open(file_name, 'r') as f:
        file_content = f.read()

    cleaned_content = "\n".join([line for line in file_content.splitlines()])

    # find '; do nothing if you want to exclude all modules' and this line and all lines before it
    if file_content.find('; do nothing if you want to exclude all modules') == -1:
        raise ValueError("exc file is processed already")
    cleaned_content = cleaned_content.split('; do nothing if you want to exclude all modules')[1]

    grouped_lines = cleaned_content.split('\n\n')

    pattern = r'^(.*?)\t(\w+)\s(\w+)\s(.*)$'
    # process data
    groups = []
    
    for group in grouped_lines:
        lines = group.splitlines()
        names = []
        for line in lines:
            if line == "":
                continue
            match = re.match(pattern, line)
            if match:
                name, data1, data2, signature = match.groups()
                names.append(name.strip())
            else:
                print(f"Could not process: {line}")
        if len(names) > 1:
            groups.append(names)
        else:
            print(f"ignore group names {names} has less than 2 names")

    # using generativeai to determine the most appropriate name
    if len(groups) != 0:
            # print some statistics
        print(f"Total groups: {len(groups)}")
        resp_text = query(groups, TEST_MODE)
    else:
        resp_text = ""
    file_content = handle_exclude(file_content=file_content, names_to_exclude=resp_text)

    # rename the file to .old
    # if file_name+".old" exists then remove it
    if os.path.isfile(file_name+".old"):
        os.remove(file_name+".old")
    os.rename(file_name, file_name+".old")
    # write to file
    with open(file_name, 'w') as f:
        f.write(file_content)


