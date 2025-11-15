import pygame, time, pathlib
import numpy as np

resource_dir = pathlib.Path(__file__).parent.resolve() / "resources"
SCREENSIZE = (800, 600)

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode(SCREENSIZE)
pygame.display.set_caption("Anti-air Onslaught")
clock = pygame.time.Clock()

# Load image resources
def loadImage(filename, scale, rotate=None):
    img = pygame.image.load(resource_dir / filename)
    img = pygame.transform.scale(img, scale)
    if rotate:
        img = pygame.transform.rotate(img, rotate)
    return img

planeImage = [loadImage("plane1.png", (65, 65)), loadImage("plane2.png", (65, 65))]
bomberImage = loadImage("bomber.png", (65, 65))
missileImage = loadImage("missile1.png", (60, 60))
carImage = loadImage("car.png", (60, 60))
bombImage = loadImage("bomb.png", (65, 65), -45)

# Load audio resources
pygame.mixer.music.load(resource_dir / "music1.ogg")
pygame.mixer.music.set_volume(0.8)
pygame.mixer.music.play(-1)
crashEffect = pygame.mixer.Sound(resource_dir / "crash.wav")
crashEffect.set_volume(0.35)
bombingEffect = pygame.mixer.Sound(resource_dir / "bombing.wav")
bombingEffect.set_volume(0.1)

# Game setting and initialization
currentScore = 0
planeNumber = 10
ground_rect = pygame.rect.Rect(0, 500, 800, 600)
carPosition = [400, 450]
missileLeft = 15
font = pygame.font.SysFont("Calibri Bold", 50)
startTime = time.time()
refresh_cycle = 1
last_refresh_time = time.time()
last_bombing_time = time.time()
bombing_interval = 10 * np.exp(-0.02*currentScore) + 5


class normalPlane(pygame.sprite.Sprite):
    def __init__(self, ):
        super().__init__()
        self.x = -20
        self.y = np.random.choice(np.arange(1, 6) * 60)
        self.speed = 0.1 * currentScore + 3
        self.speed += np.random.randint(-2, 3)
        if currentScore > 10:
            self.speed *= ((currentScore//10) * 0.3 + 1)
            self.speed = min(self.speed, 11)
        self.image = planeImage[np.random.choice((0, 1))]
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def kill(self, passive=False):
        global currentScore
        if not passive:
            if self.speed <= 7:
                currentScore += 1
            elif self.speed <= 10:
                currentScore += 2
            else:
                currentScore += 3
        return super().kill()
    
    def update(self):
        self.rect.x += self.speed
        self.x += self.speed
        if self.rect.x > SCREENSIZE[0]:
            self.kill(passive=True)

class missile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.image = missileImage
        self.rect = self.image.get_rect(center=(self.x, self.y))
        super().__init__()
    
    def update(self):
        self.rect.y -= 5 if currentScore <= 40 else 7
        if self.rect.y < -50:
            self.kill()

class bomber(pygame.sprite.Sprite):
    def __init__(self):
        self.speed = 5
        self.x = -self.speed * 5
        self.y = 50
        self.image = bomberImage
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        self.dropPosition = self.randomPosition()
        super().__init__()
    
    def randomPosition(self):
        result = []
        while len(result) < 5:
            new = np.random.randint(0, SCREENSIZE[0]//self.speed) * self.speed
            ok = True
            for other in result:
                if abs(new - other) < 30:
                    ok = False
                    break
            if ok:
                result.append(new)
        return result
    
    def update(self):
        self.rect.x += self.speed
        if self.rect.x in self.dropPosition:
            self.throw(self.rect.x)
        if self.rect.x > SCREENSIZE[0]:
            self.kill()
    
    def throw(self, x):
        bombs.add(bomb(x))

    def kill(self):
        global currentScore
        currentScore += 3
        return super().kill()

class bomb(pygame.sprite.Sprite):
    def __init__(self, x):
        self.x = x
        self.y = 50
        self.speed = 6
        self.image = bombImage
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
        super().__init__()
    
    def update(self):
        global game_over
        self.rect.y += self.speed
        if abs(self.rect.y - carPosition[1]) <= 50 and self.rect.x - 20 <= carPosition[0] <= self.rect.x + 50:
            game_over = True
        if self.rect.y > 455:
            bombingEffect.play(maxtime=1500, fade_ms=500)
            self.kill()
        
# Use pygame Sprite for collision detection
planes = pygame.sprite.Group()
missiles = pygame.sprite.Group()
bombers = pygame.sprite.GroupSingle()
bombs = pygame.sprite.Group()

game_over = done = False

while not game_over:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_over = done = True
        elif event.type == pygame.KEYDOWN and (event.key == pygame.K_SPACE or event.key == pygame.MOUSEBUTTONDOWN) and missileLeft:
            missiles.add(missile(*carPosition))
            missileLeft -= 1
    
    if missileLeft == 0 and len(missiles) == 0:
        game_over = True
    
    # Move the car
    keys = pygame.key.get_pressed()
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        carPosition[0] -= 6
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        carPosition[0] += 6
    carPosition[0] = max(0, min(carPosition[0], SCREENSIZE[0] - 50))

    # A new round of planes
    if time.time() - last_refresh_time > refresh_cycle:
        number_of_new_planes = np.random.choice((1, 2, 3), p=(0.2, 0.5, 0.3))
        for each in range(number_of_new_planes):
            planes.add(normalPlane())
        refresh_cycle = np.random.choice((1, 2, 3))
        last_refresh_time = time.time()

    planes_shot = pygame.sprite.groupcollide(planes, missiles, dokilla=True, dokillb=True)
    if planes_shot:
        crashEffect.play(maxtime=1000, fade_ms=400)
    missileLeft += len(planes_shot) * np.random.choice((1, 2, 3), p=(0.25, 0.7, 0.05))
    
    # A new round of bombing
    if time.time() - last_bombing_time > bombing_interval:
        last_bombing_time = time.time()
        bombing_interval = 10 * np.exp(-0.02 * currentScore) + 5
        bombers.add(bomber())

    # Refresh
    screen.fill((0, 0, 0))
    pygame.draw.rect(screen, (107, 107, 107), ground_rect)
    pygame.display.set_caption(f"Anti-air Onslaught - Time: {int(time.time() - startTime)}s")
    planes.update()
    missiles.update()
    bombers.update()
    bombs.update()
    planes.draw(screen)
    missiles.draw(screen)
    bombers.draw(screen)
    bombs.draw(screen)
    screen.blit(carImage, carPosition)
    availability_text = font.render(f"Available: {missileLeft}", True, (255, 0, 0))
    score_text = font.render(f"Score: {currentScore}", True, (0, 255, 0))
    screen.blits([(availability_text, (100, 550)), (score_text, (350, 550))])
    pygame.display.flip()
    clock.tick(60)

# Game Over
pygame.time.wait(1000)
pygame.mixer.music.load(resource_dir / 'music2.mp3')
pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(1)
font = pygame.font.SysFont('Impact', 90)
text = font.render('GAME OVER', True, "#fff538")
pygame.display.set_caption('Anti-air Onslaught - Game over')
while (not done) and game_over:
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            done=True
    screen.fill((255, 0, 0))
    screen.blit(text, (200, 240))
    pygame.display.flip()
    clock.tick(0)

pygame.quit()


