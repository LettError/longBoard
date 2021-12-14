import difflib

original = "AVATAR"
edited = "RAVVTARO"

d = difflib.Differ()
difference = d.compare(original, edited)

for element in difference:
    print()
    print(element)
    if element.startswith('- '):
        print('unique to 1')
    elif element.startswith('+ '):
        print('unique to 2')
    elif element.startswith(' '):
        print('common')
    else:
        raise NotImplementedError("difflib issue!")

# print('\n'.join(diff))
