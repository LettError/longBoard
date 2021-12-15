import difflib

original = list("AVATAR")
edited = list("RAVVTARO")

d = difflib.Differ()
difference = d.compare(original, edited)

for element in difference:
    print()
    print(element)
    if element.startswith('- '):
        print('remove')
    elif element.startswith('+ '):
        print('add')
    elif element.startswith(' '):
        print('common')
    else:
        raise NotImplementedError("difflib issue!")

# print('\n'.join(diff))
