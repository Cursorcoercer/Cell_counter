from PIL import Image, ImageFilter
import os

HELP_TEXT = """help: the help command displays this text, try help <function> for more detail about a specific function
quit: exits the program
count <filename>: counts the number of cells in the given file
threshold <number>: sets the threshold of the image to the given number
blur <number>: sets the blur factor, 0 is no blur
show: saves an image """

HELP_COMMANDS = {"help": "the help command explains the purpose of a function",
                 "quit": "the quit command exits the program",
                 "count": "the count function takes a filename as an argument, and counts "
                          "the number of cells in that image based on the current settings. "
                          "If no argument is passed, it counts the most recent image again",
                 "threshold": "the threshold function takes an integer as an argument, "
                              "and sets the threshold for what counts as a cell wall to that integer. "
                              "If no argument is passed, it will output the current threshold",
                 "blur": "the blur function takes an integer as an argument, "
                         "and sets that as the amount of blur that is applied to the image before "
                         "counting. If no argument is passed, it will output the current blur",
                 "show": "the show function will save a border image with the most recent settings applied"}

TO_STRIP = " \"'<>"


def is_command(inp, com):
    return inp.lower().startswith(com)


def strip(string):
    """strips unwanted characters from the start and end of words"""
    start = 0
    end = len(string)
    for start in range(len(string)):
        if string[start] not in TO_STRIP:
            break
    for end in range(len(string), start, -1):
        if string[end-1] not in TO_STRIP:
            break
    if end == start + 1 and string[start] in TO_STRIP:
        return ""
    return string[start:end]


def get_arg(inp, com):
    return strip(inp[len(com):])


def find_cells(img, thresh, blr):
    """returns a bool array describing which pixels of an image are cells and which are cell walls"""
    if blr:
        img = img.filter(ImageFilter.GaussianBlur(blr))
    size = img.size
    bool_array = []
    for f in range(size[1]):
        bool_array.append(size[0]*[None])
    for y in range(size[1]):
        for x in range(size[0]):
            pixel = img.getpixel((x, y))[1]
            bool_array[y][x] = bool(pixel > thresh)
    return bool_array


def unchecked(bools, blobs, to_fill, x, y):
    """helper function for count_fill, detects if location needs filling"""
    try:
        bools[y][x]
    except IndexError:
        # out of bounds
        return False
    if x < 0 or y < 0:
        # out of bounds
        return False
    if bools[y][x]:
        # inside wall
        return False
    if blobs[y][x] == to_fill:
        # already seen
        return False
    return True


def count_fill(bools, blobs, to_fill, x, y):
    """helper function for count, fills in current blob"""
    moves = ((0, 1), (0, -1), (1, 0), (-1, 0))
    queue = [(x, y)]
    blobs[y][x] = to_fill
    while queue:
        front = queue.pop(0)
        for move in moves:
            if unchecked(bools, blobs, to_fill, front[0]+move[0], front[1]+move[1]):
                blobs[front[1]+move[1]][front[0]+move[0]] = to_fill
                queue.append((front[0]+move[0], front[1]+move[1]))


def count(bool_array):
    """counts the number of non-continuous blobs in a bool array"""
    total = 0
    area = 0
    blob_num = []
    for f in bool_array:
        blob_num.append(len(f)*[None])
    for y in range(len(bool_array)):
        for x in range(len(bool_array[y])):
            if not bool_array[y][x]:
                area += 1
            if bool_array[y][x] or blob_num[y][x]:
                continue
            total += 1
            count_fill(bool_array, blob_num, total, x, y)
    if not total:
        return total, 0
    return total, area/total


def get_new_file_name(file):
    """given a filename, converts it to an unused name"""
    n = 1
    file_stub = file[:-4]
    while os.path.exists(file):
        n += 1
        file = file_stub + " (%s).png" % n
    return file


def show_bool(bool_array, file):
    """Save an image at the same location as file that demonstrates the bool array"""
    size = (len(bool_array[0]), len(bool_array))
    img = Image.new("RGB", size)
    for y in range(size[1]):
        for x in range(size[0]):
            if bool_array[y][x]:
                img.putpixel((x, y), (0, 255, 0))
            else:
                img.putpixel((x, y), (0, 0, 0))
    directory, name = os.path.split(file)
    try:
        name = name[:name.index('.')]
    except ValueError:
        pass
    name += " borders.png"
    img.save(get_new_file_name(os.path.join(directory, name)))


if __name__ == "__main__":
    threshold = 20
    blur = 4
    img_path = None
    image = None
    bool_walls = None

    while 1:
        command = input(">>> ")
        if is_command(command, "help"):
            arg = get_arg(command, "help")
            if arg in HELP_COMMANDS:
                print(HELP_COMMANDS[arg])
            else:
                print(HELP_TEXT)
        elif is_command(command, "quit") or is_command(command, "exit"):
            break
        elif is_command(command, "count"):
            arg = get_arg(command, "count")
            if arg:
                img_path = get_arg(command, "count")
                try:
                    image = Image.open(img_path)
                except FileNotFoundError:
                    print("invalid image path")
            if image is not None:
                bool_walls = find_cells(image, threshold, blur)
                temp = count(bool_walls)
                print(str(temp[0]) + " cells were found, giving an average cell area of " +
                      str(temp[1]) + " pixels per cell.")
            else:
                print("You need to enter an image to count")
        elif is_command(command, "threshold"):
            arg = get_arg(command, "threshold")
            if arg:
                try:
                    threshold = abs(int(arg))
                except ValueError:
                    print("Invalid threshold value")
            else:
                print("The current threshold value is " + str(threshold))
        elif is_command(command, "blur"):
            arg = get_arg(command, "blur")
            if arg:
                try:
                    blur = abs(int(arg))
                except ValueError:
                    print("Invalid blur value")
            else:
                print("The current blur value is " + str(blur))
        elif is_command(command, "show"):
            if image is not None:
                bool_walls = find_cells(image, threshold, blur)
                show_bool(bool_walls, img_path)
                print("Border image generated")
            else:
                print("No image to show")
        print("")
