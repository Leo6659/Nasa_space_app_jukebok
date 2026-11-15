import numpy as np
import pygame
import test_map_key 
import os 

WIDTH_WINDOW = 1282
HEIGHT_WINDOW  = 922
clock = pygame.time.Clock()

MAP_KEY =  "<Enter your key here>"

def index_files(base_name:str, tab:[str], n_files:int):
    """
    Every file has the same pattern: `base_name` + `_%d % i`
    We will manually load them.
    """
    for i in range(n_files):
        tmp = base_name + "_%03d.png" % i
        tab.append(tmp)

def check_key():

    global MAP_KEY
    if not os.path.exists("checked_key.py"):
        if MAP_KEY == "<Enter your key here>":
            print("The program don't check if the key is valide")
            print("If you want to enter a new key, remove checked_key.py")
            MAP_KEY = str(input())
            with open("checked_key.py", "w", encoding="utf8") as f:
                f.write(MAP_KEY)
            f.close()
        else:
            print("You already have a key. You changed source code :) !")
    else:
        f = open("checked_key.py", "r", encoding="utf8")
        MAP_KEY = f.readline()[:]
        f.close()
        if os.path.exists(".git/"):
            with open(".gitignore", "a+", encoding="utf8") as f:
                f.seek(0)
                file = f.readlines()
                if not "checked_key.py" in file:
                    f.write("checked_key.py")
            f.close()

def main() -> None:

    check_key()
    test_map_key.generate_map(MAP_KEY)

    pygame.init()
    files = []
    base_file_name = "frames/file"
    file_number = 15
    index_files(base_file_name, files, file_number)
    index = 0

    screen = pygame.display.set_mode((WIDTH_WINDOW, HEIGHT_WINDOW))
    running = True
    rec_size = screen.get_width()
    example_picture = pygame.image.load("background.png").convert()
    size_width = (screen.get_width() / file_number)
    size_height = 40

    while running:
        size_width = 40
        keys = pygame.key.get_pressed()
        # Rim stands for Readjust_IMage
        rim_vertical   = (screen.get_height() - example_picture.get_height()) / 2
        rim_horizontal = (screen.get_width() - example_picture.get_width()) / 2
        # Have to check if window is closed.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYUP: # active touch when release

                # next frame
                if keys[pygame.K_RIGHT]:
                    if index + 1 < len(files) - 1:
                        index += 1  
                    example_picture = pygame.image.load(files[index]).convert()
                    
                # previous frame
                if keys[pygame.K_LEFT]:
                    if index - 1 >= 0:
                        index -= 1
                    example_picture = pygame.image.load(files[index]).convert()
        screen.blit(example_picture, (0,0 + rim_vertical))


        screen.fill("white")

        # put picture in the right place (if rim_vertical < 0 it puts picture at the center of the window
        if (rim_vertical <= 0 or rim_horizontal <= 0):
            # print("TODO:scale picture ?")
            screen.blit(example_picture, (0 + rim_horizontal, 0 + rim_vertical)) 
        else:
            screen.blit(example_picture, (0 + rim_horizontal,0 + rim_vertical)) 

        # Manage timestamp 
        rec_timestamp = pygame.Rect(0, screen.get_height() - size_height, screen.get_width(), size_height)
        pygame.draw.rect(screen, (125, 127, 126), rec_timestamp, width = 0)

        # Current position
        width_bar = screen.get_width() / (file_number - 1) 
        # We have to round ourselves and to have a right part to get our bar to move correctly
        x = round(index * width_bar)
        right = round((index + 1) * width_bar)

        rec_timestamp_active = pygame.Rect(x, screen.get_height() - size_height, right - x, size_height)
        pygame.draw.rect(screen, (150, 143, 190), rec_timestamp_active, width=0)
        
        pygame.display.flip() # is .update() an equivalent?

        clock.tick(60)

    print("Hello and goodbye from nasa-space-app-jukebok!")

    for i in os.listdir("frames"):
        os.remove("frames/" + i)
    os.rmdir("frames")
    pygame.quit()

main()
