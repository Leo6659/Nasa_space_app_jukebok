import numpy as np
import pygame

WIDTH_WINDOW = 1280
HEIGHT_WINDOW  = 720
clock = pygame.time.Clock()

def index_files(base_name:str, tab:[str], n_files:int):
    """
    Every file has the same pattern: `base_name` + `_%d % i`
    We will manually load them.
    """
    for i in range(n_files):
        tmp = base_name + "_%d.jpg" % i
        tab.append(tmp)


def main() -> None:

    pygame.init()
    files = []
    base_file_name = "pictures/file"
    file_number = 4
    index_files(base_file_name, files, file_number)
    index = 0

    screen = pygame.display.set_mode((WIDTH_WINDOW, HEIGHT_WINDOW))
    running = True
    rec_size = screen.get_width() / file_number
    example_picture = pygame.image.load("example.jpg").convert()
    size_width = (screen.get_width() / file_number)
    size_height = 40
    rec_timestamp = pygame.Rect(size_width, screen.get_height() - size_height, size_width, size_height)

    while running:
        size_width = (screen.get_width() / file_number)
        keys = pygame.key.get_pressed()
        rim = (screen.get_height() - example_picture.get_height()) / 2
        # Have to check if window is closed.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYUP:
                if keys[pygame.K_RIGHT]:
                    if index + 1 < len(files) - 1:
                        index += 1  
                    example_picture = pygame.image.load(files[index]).convert()
                    
                if keys[pygame.K_LEFT]:
                    if index - 1 >= 0:
                        index -= 1
                    example_picture = pygame.image.load(files[index]).convert()
        screen.blit(example_picture, (0,0 + rim))

        # get to previous picture

        screen.fill("white")
        screen.blit(example_picture, (0,0 + rim)) 
        pygame.draw.rect(screen, (125, 127, 126), rec_timestamp, width = 0)
        rec_timestamp = pygame.Rect(size_width, screen.get_height() - size_height, size_width, size_height)


        for i in range(file_number):
            rec_timestamp = rec_timestamp.inflate(size_width, 0)

        rec_timestamp_active = pygame.Rect(size_width * index, screen.get_height() - size_height, size_width * (index + 1), size_height)
        pygame.draw.rect(screen, (129, 145, 138), rec_timestamp_active, width=0)
        
        pygame.display.flip() # is .update() an equivalent?

        clock.tick(60)

    print("Hello and Goodbye from nasa-space-app-jukebok!")
    pygame.quit()

main()
print(np.__version__)
