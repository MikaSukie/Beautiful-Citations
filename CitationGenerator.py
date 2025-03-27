import pygame
import pygame.scrap
import numpy as np
import requests
import re
from bs4 import BeautifulSoup
import datetime
import random

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("B-Citation Generator")

pygame.scrap.init()
pygame.scrap.set_mode(pygame.SCRAP_CLIPBOARD)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PASTEL_PINK = (255, 204, 255)
BUTTON_COLOR = (240, 180, 255)
FLUID_BASE = (255, 150, 200)

grid_size = 100
viscosity = 0.93
mouse_influence = 0.7

fluid_current = np.full((grid_size, grid_size), 0.05)
fluid_prev = np.zeros((grid_size, grid_size))

pygame.font.init()
font = pygame.font.Font(None, 30)
small_font = pygame.font.Font(None, 24)

input_box = pygame.Rect(WIDTH // 2 - 200, 50, 400, 32)
paste_button = pygame.Rect(input_box.right + 10, 50, 100, 32)
citation_box = pygame.Rect(WIDTH // 2 - 250, 250, 500, 100)
generate_button = pygame.Rect(WIDTH // 2 - 50, 100, 120, 32)
copy_button = pygame.Rect(WIDTH // 2 - 50, 370, 100, 32)
clear_button = pygame.Rect(WIDTH // 2 - 50, 420, 100, 32)

input_text = ""
citation_text = ""
style = "MLA"
mouse_down = False

class Bubble:
    def __init__(self):
        self.x = random.randint(50, WIDTH - 50)
        self.y = HEIGHT + random.randint(10, 100)
        self.radius = random.randint(5, 15)
        self.speed = random.uniform(1, 2)

    def update(self):
        self.y -= self.speed
        if self.y < -self.radius:
            self.y = HEIGHT + random.randint(10, 100)
            self.x = random.randint(50, WIDTH - 50)

    def draw(self):
        alpha_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(alpha_surface, (255, 255, 255, 120), (self.radius, self.radius), self.radius)
        screen.blit(alpha_surface, (self.x - self.radius, self.y - self.radius))

bubbles = [Bubble() for _ in range(10)]

def get_article_info(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.content
    except requests.exceptions.RequestException:
        return 'Invalid URL', 'Unknown', 'Unknown'

    soup = BeautifulSoup(html_content, 'html.parser')
    title = soup.select_one('title').text.strip() if soup.select_one('title') else 'Unknown'
    author = soup.select_one('meta[name="author"]')
    author = author['content'].strip() if author else 'Unknown'
    date_published = soup.select_one('meta[name="datePublished"]')
    date_published = date_published['content'].strip() if date_published else 'Unknown'

    return title, author, date_published

def generate_citation(url, style):
    title, author, date_published = get_article_info(url)
    domain_match = re.search(r'(?:https?:\/\/)?(?:www\.)?([a-zA-Z0-9-]+)\.[a-zA-Z]{2,}(?:\/|$)', url)
    domain = domain_match.group(1) if domain_match else 'Unknown'

    date_accessed = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")

    if style == 'APA':
        year = date_published[:4] if date_published != 'Unknown' else 'n.d.'
        citation = f'{author}. ({year}). {title}. {domain.capitalize()}. Retrieved from {url}'
    elif style == 'MLA':
        citation = f'{author}. "{title}." {domain.capitalize()}, {date_published}, {url}. Accessed {date_accessed}.'
    elif style == 'Chicago':
        citation = f'{author}. "{title}." {domain.capitalize()}. {date_published}. {url}.'
    else:
        citation = "Invalid citation style."

    return citation

def update_fluid():
    global fluid_current, fluid_prev

    new_fluid = (
        (fluid_prev[:-2, 1:-1] + fluid_prev[2:, 1:-1] +
         fluid_prev[1:-1, :-2] + fluid_prev[1:-1, 2:]) / 2
        - fluid_current[1:-1, 1:-1]
    )

    fluid_current[1:-1, 1:-1] = new_fluid * viscosity

    fluid_prev, fluid_current = fluid_current, fluid_prev

def draw_fluid():
    for x in range(grid_size):
        for y in range(grid_size):
            value = max(50, min(int(180 + fluid_current[x, y] * 150), 255))
            color = (255, value, value)
            rect = pygame.Rect(x * (WIDTH // grid_size), y * (HEIGHT // grid_size),
                               WIDTH // grid_size, HEIGHT // grid_size)
            pygame.draw.rect(screen, color, rect, border_radius=5)

def draw_button(rect, text):
    pygame.draw.rect(screen, BUTTON_COLOR, rect, border_radius=10)
    screen.blit(font.render(text, True, BLACK), (rect.x + 15, rect.y + 5))

running = True
active_input = False
last_mouse_pos = None

while running:
    screen.fill(PASTEL_PINK)
    draw_fluid()

    for bubble in bubbles:
        bubble.update()
        bubble.draw()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEMOTION:
            mx, my = pygame.mouse.get_pos()

            gx, gy = int(mx / (WIDTH / grid_size)), int(my / (HEIGHT / grid_size))

            if 0 < gx < grid_size - 1 and 0 < gy < grid_size - 1:
                fluid_current[gx, gy] += mouse_influence

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_down = True
            mx, my = pygame.mouse.get_pos()

            gx, gy = int(mx / (WIDTH / grid_size)), int(my / (HEIGHT / grid_size))
            if 0 < gx < grid_size - 1 and 0 < gy < grid_size - 1:
                fluid_current[gx, gy] = 1

            if input_box.collidepoint(event.pos):
                active_input = True
            else:
                active_input = False

            if paste_button.collidepoint(event.pos):
                pasted_text = pygame.scrap.get(pygame.SCRAP_TEXT)
                if pasted_text:
                    try:
                        input_text = pasted_text.decode("utf-8").replace("\x00", "").strip()
                    except UnicodeDecodeError:
                        input_text = ""

            if generate_button.collidepoint(event.pos) and input_text:
                citation_text = generate_citation(input_text, style)

            if copy_button.collidepoint(event.pos) and citation_text:
                pygame.scrap.put(pygame.SCRAP_TEXT, citation_text.encode('utf-8'))

            if clear_button.collidepoint(event.pos):
                input_text = ""
                citation_text = ""

        if event.type == pygame.MOUSEBUTTONUP:
            mouse_down = False

        if event.type == pygame.KEYDOWN:
            if active_input:
                if event.key == pygame.K_RETURN:
                    citation_text = generate_citation(input_text, style)
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode

    update_fluid()

    pygame.draw.rect(screen, WHITE, input_box, 2, border_radius=10)
    pygame.draw.rect(screen, WHITE, citation_box, 2, border_radius=10)

    screen.blit(font.render("Enter Website URL:", True, WHITE), (input_box.x, input_box.y - 25))
    screen.blit(font.render(input_text, True, WHITE), (input_box.x + 5, input_box.y + 5))

    draw_button(paste_button, "Paste")
    draw_button(generate_button, "Generate")
    draw_button(copy_button, "Copy")
    draw_button(clear_button, "Clear")

    screen.blit(font.render("Citation:", True, WHITE), (citation_box.x, citation_box.y - 25))
    screen.blit(small_font.render(citation_text, True, WHITE), (citation_box.x + 5, citation_box.y + 5))

    pygame.display.flip()
    pygame.time.delay(16)

pygame.quit()
