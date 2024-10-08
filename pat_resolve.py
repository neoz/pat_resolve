import os
import re
import sys

TEST_MODE = False
GROUPS_LENGTH_MAX = 1000

def select_best_name(names : list):
    # find the best name in the list by criteria: min length
    best_name = min(names, key=len)
    return best_name

class local_response:
    def __init__(self, text):
        self.text = text

def query_local(groups : list):
    name_list = []
    for group in groups:
        name_list.append(select_best_name(group))

    return local_response(",".join(name_list)), "local_request"

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

    print(f"Total of pattern groups: {len(grouped_lines)}")

    pattern = r'^(.*?)\t(\w+)\s(\w+)\s(.*)$'
    # process data
    groups = []
    i = 0
    lst_group = []
    for group in grouped_lines:
        lines = group.splitlines()
        names = []
        for line in lines:
            if line == "":
                continue
            match = re.match(pattern, line)
            if match:
                name, data1, data2, signature = match.groups()
                #ignore sub_ functions
                if name.startswith("sub_"):
                    continue
                names.append(name.strip())
            else:
                print(f"Could not process: {line}")
        if len(names) > 1:
            groups.append(names)
            if len(groups) == GROUPS_LENGTH_MAX:
                lst_group.append(groups)
                groups = []   
        # else:
        #     print(f"ignore group names {names} has less than 2 names")

    if len(groups) != 0:
        lst_group.append(groups)

    name_list = []
    for i, group in enumerate(lst_group):
        print(f"Group {i+1}: {len(group)}")
        if len(group) != 0:
            # using generativeai to determine the most appropriate name
            resp, input = query_local(group)
            print(resp.text)
            names = resp.text.split(',')
            if len(names) != len(group):
                print("----- Request -----")
                print(input)
                print("----- Response -----")
                print(resp)
                raise ValueError(f"Number of names {len(names)} does not match number of groups {len(group)}")
            name_list.append(",".join(names))
        else:
            raise ValueError("No groups found")
    
    data = ",".join(name_list)
    file_content = handle_exclude(file_content=file_content, names_to_exclude=data)

    # rename the file to .old
    # if file_name+".old" exists then remove it
    if os.path.isfile(file_name+".old"):
        os.remove(file_name+".old")
    os.rename(file_name, file_name+".old")
    # write to file
    with open(file_name, 'w') as f:
        f.write(file_content)


