import pygame
from pygame import FULLSCREEN
import random
import copy
import math
import os


#window setup
import ctypes
user32 = ctypes.windll.user32
global scr_width
global scr_height
scr_width = user32.GetSystemMetrics(0)
scr_height = user32.GetSystemMetrics(1)
window = pygame.display.set_mode((scr_width,scr_height),FULLSCREEN)
pygame.display.set_caption("ASH")
pygame.font.init()
from pygame.locals import *
pygame.init()

#Objects
#BOARD ========================================
class Board:
    def __init__(self):
        self.RUN = True
        self.pawns = [[], []]
        self.menuparticles = []
        self.particles = []
        self.buildings = []
        self.buildbuildings = []
        self.resources = []

        #rainstorm
        self.rainstorm = False
        self.raintimer = 0
        self.rainswitch = random.randint(3000,5000)

        #pathgrid
        self.width = 60
        self.height = 40
        self.thickness = 25
        self.coord = [scr_width//2-(self.width*self.thickness//2), scr_height//2-(self.height*self.thickness//2)]
        self.grid = []
        for x in range(self.width):
            self.grid.append([])
            for y in range(self.height):
                coord = []
                coord.append(x*self.thickness + self.coord[0] + self.thickness//2)
                coord.append(y*self.thickness + self.coord[1] + self.thickness//2)
                if x == 0 or x == self.width -1 or y == 0 or y == self.height -1:
                    self.grid[x].append(Node([x,y], coord, True))
                else:
                    self.grid[x].append(Node([x,y], coord, False))

        self.nodes = []
        for x in range(self.width):
            for y in range(self.height):
                self.nodes.append(self.grid[x][y])
                if x == 0 or x == self.width-1 or y == 0 or y == self.height-1:
                    self.nodes[-1].outer = True

        #buildgrid
        self.buildcoord = [self.coord[0] + self.thickness, self.coord[1] + self.thickness]
        self.buildwidth = int(self.width/2)-1
        self.buildheight = int(self.height/2)-1
        self.buildthickness = self.thickness*2
        self.bgridthickness = 2

        #UI
        self.totalresources = [1000,1000,1000]
        self.population = 0
        self.maxpopulation = 5

        #resource panel
        self.resourcepanel = scr_width - 300, scr_height-150, 300, 150
        self.resourcefont = pygame.font.SysFont('', 50)
        self.icons = []
        self.icons.append(pygame.image.load("images\\resources\\icons\\grain.png").convert_alpha())
        self.icons.append(pygame.image.load("images\\resources\\icons\\rain.png").convert_alpha())
        self.icons.append(pygame.image.load("images\\resources\\icons\\wood.png").convert_alpha())
        self.icons.append(pygame.image.load("images\\resources\\icons\\population.png").convert_alpha())

    def Show(self):
        #roofed
        for x in range(self.width):
            for y in range(self.height):
                i = self.grid[x][y]
                if i.roofed:
                    pygame.draw.rect(window, (116,166,166), (i.coord[0]-self.thickness//2, i.coord[1]-self.thickness//2, self.thickness, self.thickness))

        #buildgrid
        if M.buildmode or M.wallmode:
            for i in range(1, self.buildheight):
                pygame.draw.line(window, (221,223,220), (self.buildcoord[0], self.buildcoord[1]+i*self.buildthickness), (self.buildcoord[0] + self.buildwidth* self.buildthickness, self.buildcoord[1]+i*self.buildthickness))

            for i in range(1, self.buildwidth):
                pygame.draw.line(window, (221,223,220), (self.buildcoord[0]+i*self.buildthickness, self.buildcoord[1]), (self.buildcoord[0]+i*self.buildthickness, self.buildcoord[1] + self.buildheight* self.buildthickness))

        if M.wallmode:
            W.Show()

    def LogGen(self):
        depositno = 5
        for i in range(0, depositno):
            self.resources.append(Logs(False))
            x = random.randint(0,self.width)
            y = random.randint(0,self.height)
            self.resources[-1].Drop([x,y])

    def RainStorm(self):
        self.raintimer += 1

        #drizzle
        if self.rainstorm:
            for i in range(0, 25):
                x = random.randint(self.coord[0]-5000, self.coord[0] + self.width * self.thickness)
                y = random.randint(self.coord[1], self.coord[1] + self.height * self.thickness)
                check = Coordfinder([x,y])
                if check != False:
                    z = B.grid[check[0]][check[1]]
                    if not (z.roofed or z.blocked):
                        B.particles.append(Drizzle([x, y], (40,73,87), False))

            #droplet
            if self.raintimer % 50 == 0:
                x = random.randint(2, self.width-3)
                y = random.randint(2, self.height-3)

                #roof check
                z = B.grid[x][y]
                if not z.roofed:
                    coord = CoordConverter([x, y], True)
                    if (not z.blocked) and random.randint(0,5) == 0:
                        B.particles.append(BadDroplet(coord))
                    else:
                        B.particles.append(Droplet(coord))

        #stop rain
        if self.raintimer == self.rainswitch:
            self.raintimer = 0
            if self.rainstorm:
                self.rainstorm = False
                self.rainswitch = random.randint(6000,9000)
            else:
                self.rainstorm = True
                self.rainswitch = random.randint(1000,2000)

    def ResourcePanel(self):
        pygame.draw.rect(window, (40,62,63), self.resourcepanel)
        X = self.resourcepanel[0]+20
        Y = self.resourcepanel[1]+10

        #resources
        for i in range(0,3):
            Text = self.resourcefont.render(str(self.totalresources[i]), False, (247,216,148))
            window.blit(Text, (X+35, Y))
            window.blit(self.icons[i], (X, Y))
            Y += 30

        #pop
        Text = self.resourcefont.render(str(self.population)+"/"+str(self.maxpopulation), False, (247,216,148))
        window.blit(Text, (X+35, Y))
        window.blit(self.icons[-1], (X, Y))
    
#CONTROLS ========================================
class Mouse:
    def __init__(self):
        #coord
        self.coord = [0,0]

        #pan
        self.drag = False

        #bottom bar
        self.barheight = 150
        self.bargap = 120

    def Pan(self):
        diff = []
        for i in  range(0,2):
            diff.append(self.coord[i] - self.drag[i])
        
        for x in range(0,2):
            B.coord[x] += diff[x]
            B.buildcoord[x] += diff[x]
            for i in B.nodes:
                i.coord[x] += diff[x]
            for i in B.resources:
                i.coord[x] += diff[x]
            for i in B.buildings:
                i.coord[x] += diff[x]
            for z in B.pawns:
                for i in z:
                    i.coord[x] += diff[x]
            for i in B.particles:
                i.coord[x] += diff[x]
                if i.sig == "droplet":
                    i.des[x] += diff[x]
                elif i.sig == "drizzle":
                    i.last[x] += diff[x]
                    if x == 1:
                        i.dest += diff[x]
            for i in W.verticies:
                i.coord[x] += diff[x]
            
        self.drag = copy.deepcopy(self.coord)

class GameMonitor(Mouse):
    def __init__(self):
        super().__init__()
        #coordinator
        self.wallmode = False
        self.buildmode = False
        self.coord[0], self.coord[1] = pygame.mouse.get_pos()


        #gameplay
        self.selectbox = False
        self.shift = False
        self.selected = False

        #bottom option bar
        self.options = []
        self.bar = 0, scr_height-150, self.bargap * len(self.options), self.barheight
        self.highlight = -1

        #overview box
        self.Obox = (scr_width-250, scr_height-500, 250, 500)

        #fonts
        self.TitleFont = pygame.font.SysFont('', 70)
        self.SubFont = pygame.font.SysFont('', 40)
        self.TextFont = pygame.font.SysFont('', 30)
        
    def Input(self):
        if self.drag != False:
            self.Pan()

        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            #mouse
            if event.type == pygame.MOUSEMOTION:
                self.coord[0], self.coord[1] = pygame.mouse.get_pos()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.mouse.get_pressed()[0]:
                    self.LClickDOWN()
                elif pygame.mouse.get_pressed()[1]:
                    self.drag = copy.deepcopy(self.coord)
                elif pygame.mouse.get_pressed()[2]:
                    self.RClickDOWN()
            if event.type == pygame.MOUSEBUTTONUP:
                if self.selectbox != False:
                    self.LClickUP()
                if self.drag != False:
                    self.drag = False
            
            #keys
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()#dev tools#####################
                if keys[pygame.K_9]:######################
                    B.LogGen()######################
                if keys[pygame.K_8]:######################
                    if B.rainstorm:######################
                        B.rainstorm = False######################
                    else:######################
                        B.rainstorm = True######################
                        B.raintimer = 0######################
                if keys[pygame.K_RSHIFT] or keys[pygame.K_LSHIFT]:
                    self.shift = True
                if keys[pygame.K_f]:
                    self.wallmode = True
                if keys[pygame.K_b]:
                    self.buildmode = True
                if keys[pygame.K_ESCAPE]:
                    PauseScreen()

            if event.type == pygame.KEYUP:
                self.shift = False

    def LClickDOWN(self):
        #command
        if self.highlight == -1:
            if not self.shift:
                if self.selected != False:
                    for i in self.selected:
                        i.selected = False
                    self.selected = False

            self.selectbox = copy.deepcopy(self.coord)
        else:
            action = self.op[self.highlight]
            if action[:5] == "Train":
                self.selected[0].Task()
            elif action == "Demolish":
                self.selected[0].Demolish()
    
    def RClickDOWN(self):
        if self.selected != False:
            harvest = False
            for x in B.resources:
                if x.coord[0] < self.coord[0] < x.coord[0]+x.width and x.coord[1] < self.coord[1] < x.coord[1]+x.height:
                    harvest = x
                    break

            for i in self.selected:
                if i.pawn:
                    if i.sig == "worker":
                        if harvest != False:
                            i.HarvestCommand(harvest)
                        else:
                            if i.resourcepoint != False:
                                i.resourcepoint.workers.remove(i)
                                i.resourcepoint = False
                            
                            i.harvesting = False
                            i.Task(self.coord)
                    else:
                        i.Task(self.coord)

    def LClickUP(self):
        x = self.coord[0] - self.selectbox[0]
        y = self.coord[1] - self.selectbox[1]
        notbox = math.sqrt(x**2 + y**2)
        if notbox > 10:
            #sets correct bound
            bounds = [[0,0],[0,0]]
            for i in range(0,2):
                if self.coord[i] < self.selectbox[i]:
                    bounds[i][0] = self.coord[i]
                    bounds[i][1] = self.selectbox[i]
                else:
                    bounds[i][1] = self.coord[i]
                    bounds[i][0] = self.selectbox[i]

            #scans pawns
            for x in B.pawns:
                for i in x:
                    inside = True
                    for x in range(0,2):
                        if bounds[x][0] > i.coord[x] or  i.coord[x] > bounds[x][1]:
                            inside = False
                            break
                    if inside:
                        self.Select(i)
        
        else:
            #selects pawns without select box
            pawnselected = False
            for x in B.pawns:
                for i in x:
                    if i.coord[0]+i.radius > self.coord[0] >i.coord[0]-i.radius and i.coord[1]+i.radius > self.coord[1] > i.coord[1] - i.radius:
                        x = i.coord[0] - self.coord[0]
                        y = i.coord[1] - self.coord[1]
                        hypotenuse = math.sqrt(x**2 + y**2)
                        if hypotenuse < i.radius:
                            self.Select(i)
                            pawnselected = True

            if not pawnselected:
                for i in B.buildings:
                    if i.coord[0]+i.width > self.coord[0] > i.coord[0] and i.coord[1]+i.height > self.coord[1] > i.coord[1]:
                        self.Select(i)
                for i in B.resources:
                    if i.coord[0]+i.width > self.coord[0] > i.coord[0] and i.coord[1]+i.height > self.coord[1] > i.coord[1]:
                        self.Select(i)


        self.selectbox = False
    
    def Select(self, i):
        if self.selected == False:
            self.selected = [i]
        else:
            self.selected.append(i)

        i.selected = True

    def BottomBar(self):
        self.op = []
        self.highlight = -1
        if self.selected != False:
            if self.selected[0].overview == "building":
                
                #options
                self.op = self.selected[0].options
                if len(self.op) > 0:
                    self.bar = 0, scr_height-150, self.bargap * len(self.op), 150

                pygame.draw.rect(window, (40,62,63), self.bar)

                #highlights
                for i in range(0, len(self.op)):
                    X = self.bar[0] + self.bargap * i
                    Y = self.bar[1]
                    if (X < self.coord[0] < X + self.bargap) and (Y < self.coord[1] < scr_height):
                        #highlight
                        self.highlight = i
                        pygame.draw.rect(window, (60,82,83), (X, Y, self.bargap, self.bar[3]))

                    #Text
                    if self.op[i] != False:
                        OpFont = pygame.font.SysFont('', 50)
                        Text = OpFont.render(str(self.op[i]), False, (247,216,148))
                        window.blit(Text, (X+10, Y+30))

        #select box
        if self.selectbox != False:
            topright = [self.coord[0], self.selectbox[1]]
            bottomleft = [self.selectbox[0], self.coord[1]]
            pygame.draw.polygon(window, (211,171,81), (self.selectbox, topright, self.coord, bottomleft), 3)

    def OverviewBox(self):
        if self.selected != False:
            i = self.selected[0]
            pygame.draw.rect(window, (116,116,116), self.Obox)
            x = 0

            #title
            text = self.TitleFont.render(i.sig, False, (255,255,255))
            window.blit(text, (self.Obox[0]+10, self.Obox[1]+10))
            x += 1

            if i.overview == "pawn":
                #Health
                text = self.SubFont.render("HLT: "+str(i.health), False, (21,35,45))
                window.blit(text, (self.Obox[0]+10, self.Obox[1]+x*60))
                x += 1

                #Strength
                text = self.SubFont.render("STR: "+str(i.strength), False, (21,35,45))
                window.blit(text, (self.Obox[0]+10, self.Obox[1]+x*60))
                x += 1

                #Status
                status = self.SubFont.render("STA: "+i.status, False, (21,35,45))


                if i.sig == "worker":
                    #holding
                    text = self.SubFont.render("HLD: "+str(i.holding), False, (21,35,45))
                    window.blit(text, (self.Obox[0]+10, self.Obox[1]+x*60))
                    x += 1

                window.blit(status, (self.Obox[0]+10, self.Obox[1]+x*60))

            elif i.overview == "building":
                #Health
                text = self.SubFont.render("HLT: "+str(i.health), False, (21,35,45))
                window.blit(text, (self.Obox[0]+10, self.Obox[1]+x*60))
                x += 1

                #Training Status
                if i.trainable:
                    if i.trainingdelay > 0:
                        progress = str(round((i.trainingdelay/i.maxtrainingdelay)* 100)) + "%"
                        if i.queue > 0:
                            multi = " x"+str(i.queue+1)+" "
                        else:
                            multi = ""
                        status = self.SubFont.render("STA: training"+multi+": "+ progress, False, (21,35,45))
                    else:
                        status = self.SubFont.render("STA: idle", False, (21,35,45))
                    

                    window.blit(status, (self.Obox[0]+10, self.Obox[1]+x*60))

            elif i.overview == "resource":
                #Resource pool
                text = self.SubFont.render("LFT: "+str(i.resourcepool), False, (21,35,45))
                window.blit(text, (self.Obox[0]+10, self.Obox[1]+x*60))
                x += 1

class BuildMonitor(Mouse):
    def __init__(self):
        super().__init__()
        self.coord = M.coord
        #building
        self.selected = False

        self.items = [Center(False), House(False), Stockpile(False), Barracks(False), Palace(False), Grain(False)]
        for i in self.items:
            i.coord[0] = self.items.index(i)*self.bargap - i.width //2 + self.bargap//2
            i.coord[1] = scr_height-150 - i.height //2 + self.barheight//2
            B.buildbuildings.append(i)          

    def Input(self):
        if self.drag != False:
            self.Pan()

        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            #mouse
            if event.type == pygame.MOUSEMOTION:
                self.coord[0], self.coord[1] = pygame.mouse.get_pos()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.mouse.get_pressed()[0]:
                    self.LClickDOWN()
                elif pygame.mouse.get_pressed()[1]:
                    self.drag = copy.deepcopy(self.coord)
            if event.type == pygame.MOUSEBUTTONUP:  
                if self.drag != False:
                    self.drag = False
                else:
                    self.LClickUP()

            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_b]:
                    M.buildmode = False
                if keys[pygame.K_ESCAPE]:
                    PauseScreen()
    
    def LClickDOWN(self):
        #command
        if self.highlight != -1:
            #build
            items = [Center(True), House(True), Stockpile(True), Barracks(True), Palace(True), Grain(True)]
            self.selected = items[self.highlight]
            B.buildbuildings.append(self.selected)

    def LClickUP(self):
        if self.selected != False:
            #list management
            if self.selected.sig == "grain":
                B.resources.append(self.selected)
            else:
                B.buildings.append(self.selected)
            B.buildbuildings.remove(self.selected)

            pycoord = Coordfinder(self.coord)
            self.selected.Drop(pycoord)

            #reset
            self.selected = False

    def Showcase(self):
        #options ========        
        self.bar = 0, scr_height-150, self.bargap * len(self.items), 150

        pygame.draw.rect(window, (40,62,63), self.bar)
        #highlights
        self.highlight = -1
        for i in range(0, len(self.items)):
            X = self.bar[0] + self.bargap * i
            Y = self.bar[1]
            if (X < self.coord[0] < X + self.bargap) and (Y < self.coord[1] < scr_height):
                #highlight
                self.highlight = i
                pygame.draw.rect(window, (60,82,83), (X, Y, self.bargap, self.bar[3]))
        
        #items
        for i in B.buildbuildings:
            i.Show()

class WallMonitor(Mouse):
    def __init__(self):
        super().__init__()
        self.coord = M.coord
        self.verticies = []
        self.walls = []

        #placement
        self.highlight = False
        self.start = False
        self.hold = False
        self.cost = [5,5,5]

        #board
        self.width = B.buildwidth
        self.height = B.buildheight
        for x in range(0, self.width+1):
            for y in range(0, self.height+1):
                self.verticies.append(Vertex([x, y]))
    
    def BorderGen(self):
        corners = [False, False, False, False]
        for i in self.verticies:
            if i.pycoord[0] == 0:
                if i.pycoord[1] == 0:
                    corners[0] = i #top left
                elif i.pycoord[1] == self.height:
                    corners[3] = i #bottom left
            elif i.pycoord[0] == self.width:
                if i.pycoord[1] == 0:
                    corners[1] = i #top right
                elif i.pycoord[1] == self.height:
                    corners[2] = i #bottom right

        for i in range(0,4):
            if i == 4:
                self.walls.append(Wall(corners[i], corners[0]))
            else:
                self.walls.append(Wall(corners[i], corners[i-1]))

        #block off
        for i in self.walls:
            i.unchangeable = True

    def Input(self):
        if self.drag != False:
            self.Pan()

        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            #mouse
            if event.type == pygame.MOUSEMOTION:
                self.coord[0], self.coord[1] = pygame.mouse.get_pos()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.mouse.get_pressed()[0]:
                    self.LClickDOWN()
                elif pygame.mouse.get_pressed()[1]:
                    self.drag = copy.deepcopy(self.coord)
                elif pygame.mouse.get_pressed()[2]:
                    self.RClickDOWN()
            if event.type == pygame.MOUSEBUTTONUP:  
                if self.drag != False:
                    self.drag = False
                else:
                    self.LClickUP()

            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_f]:
                    self.ModeTransition()
                if keys[pygame.K_ESCAPE]:
                    PauseScreen()
                if keys[pygame.K_g]:
                    self.GateWork()

    def LClickDOWN(self):
        #highlight
        if self.highlight != False:
            self.hold = True
            self.start = self.highlight
            self.highlight = False

    def LClickUP(self):
        if self.start != False:
            if self.highlight != False:
                #45 degree check
                p = self.highlight.pycoord
                q = self.start.pycoord
                if p != q:
                    x = p[0] - q[0]
                    y = p[1] - q[1]
                    if x == 0 or y == 0:
                        #direction
                        nudge = [0,0]
                        if x > 0:
                            nudge[0] = 1
                        elif x < 0:
                            nudge[0] = -1
                        elif y > 0:
                            nudge[1] = 1
                        elif y < 0:
                            nudge[1] = -1

                        #search
                        found = False
                        current = self.start
                        while not found:
                            for i in self.verticies:
                                if i.pycoord[0] == current.pycoord[0]+nudge[0] and i.pycoord[1] == current.pycoord[1]+nudge[1]:
                                    result = self.CostCheck()
                                    if result:
                                        result = self.DuplicateCheck(i, current)
                                        if result:
                                            self.walls.append(Wall(i, current))
                                            current = i
                                            if i == self.highlight:
                                                found = True
                                                break
                                        else:
                                            self.Reset()
                                            return
                                    else:
                                        self.Reset()
                                        return
        self.Reset()

    def Reset(self):
        #reset
        self.hold = False
        self.highlight = False
        self.start = False

    def RClickDOWN(self):
        for i in self.walls:
            result = i.rect.collidepoint((self.coord[0], self.coord[1]))
            if result:
                if not i.unchangeable:
                    i.Remove()
                    for i in range(0,3):
                        B.totalresources[i] += self.cost[i]

    def Show(self):
        self.highlight = False

        if self.hold:
            pygame.draw.line(window, (221,223,220), (self.start.coord[0], self.start.coord[1]), (self.coord[0], self.coord[1]),5)

    def GateWork(self):
        for i in self.walls:
            if not i.unchangeable:
                result = i.rect.collidepoint((self.coord[0], self.coord[1]))
                if result:
                    i.GateTransition()

    def DuplicateCheck(self, x, z):
        for i in self.walls:
            if x in i.verticies and z in i.verticies:
                for i in range(0,3):
                    B.totalresources[i] += self.cost[i]
                return False

        return True

    def CostCheck(self):
        fine = True
        for i in range(0,3):
            if B.totalresources[i] - self.cost[i] < 0:
                fine = False

        if fine:
            for i in range(0,3):
                B.totalresources[i] -= self.cost[i]
            return True
        else:
            return False

    def ModeTransition(self):
        M.wallmode = False

        #pathfinding
        for x in B.pawns:
            for i in x:
                if i.status != "idle" and i.status != "harvesting":
                    if i.status == "commuting":
                        i.HarvestCommand(i.resourcepoint)
                    elif i.status == "hauling":
                        i.FindDepositsite()
                    else:
                        i.Task(i.path[-1])

        #roofing
        #reset grid
        for x in range(B.width):
            for y in range(B.height):
                B.grid[x][y].roofed = False

        for i in self.walls:
            i.RoofProvoke()

#GRID ========================================
class Node:
    def __init__(self, pycoord, coord, outer):
        self.pycoord = pycoord
        self.coord = coord
        self.Fcost = False
        self.gcost = 0

        #states
        if outer:
            self.blocked = True
        else:
            self.blocked = False
        self.builton = False

        #resource collection
        self.depositable = False

        #wall
        self.roofed = False
        self.outer = False
        self.exhausted = False
    
    def CostFinder(self, node, end):
        #g cost
        x = self.coord[0] - node.coord[0]
        y = self.coord[1] - node.coord[1] 

        self.gcost = math.sqrt(x**2 + y**2) + node.gcost

        #h cost
        x = self.coord[0] - end.coord[0]
        y = self.coord[1] - end.coord[1] 

        hcost = math.sqrt(x**2 + y**2)
        result = hcost + self.gcost

        if self.Fcost != False:
            if self.Fcost < result:
                self.Fcost = result
                self.parent = node
        else:
            self.Fcost = result
            self.parent = node

    def RoofWork(self):
        self.exhausted = True
        self.roofed = True
        middle = Centralise(self.coord)
        #find neighbours
        neighbours = []
        ticker = [[-1,-1],[0,-1],[1,-1],[1,0],[1,1],[0,1],[-1,1],[-1,0]]
        x, y = self.pycoord
        for i in ticker:
            node = B.grid[x+i[0]][y+i[1]]
            if not node.blocked and not node.exhausted:
                #barricade
                result = self.IntersectCheck(node, middle)
                if result:
                    neighbours.append(node)
            
            else:
                #unwind
                result = self.IntersectCheck(node, middle)
                if result:
                    if node.outer:
                        self.roofed = False
                        return True

        if len(neighbours) == 0:
            return False
        else:
            for i in neighbours:
                hitouter = i.RoofWork()
                if hitouter:
                    self.roofed = False
                    return True

    def IntersectCheck(self, node, middle):
        intersects = False
        rect = FindRect(middle, Centralise(node.coord))
        for z in W.walls:
            if rect.colliderect(z.rect) and not z.unchangeable:
                intersects = True
                break

        if not intersects:
            return True

class Vertex:
    def __init__(self, pycoord):
        self.pycoord = pycoord
        self.coord = [B.buildcoord[0] + B.buildthickness * self.pycoord[0], B.buildcoord[1] + B.buildthickness * self.pycoord[1]]
        self.radius = 8

        #gameplay
        self.connections = []

    def Show(self):
        if M.wallmode:
            #mouseover
            mouseover = False

            if W.highlight == False:#optimization
                x = W.coord[0] - self.coord[0]
                y = W.coord[1] - self.coord[1]
                hypotenuse = math.sqrt(x**2 + y**2)
                if hypotenuse < self.radius:
                    mouseover = True
                    W.highlight = self

            if len(self.connections) > 0:
                #circle
                if mouseover:
                    colour = (0,225,0)
                else:
                    colour = (73,73,73)
                
                pygame.draw.circle(window, colour, (int(self.coord[0]), int(self.coord[1])), self.radius, 0)
            
            else:
                if mouseover:
                    colour = (0,225,0)
                else:
                    colour = (221,223,220)

                pygame.draw.circle(window, colour, (int(self.coord[0]), int(self.coord[1])), self.radius, 0)


        else:
            if len(self.connections) > 0:
                #circle
                colour = (73,73,73)
                #no dot
                through = False
                for i in self.connections:
                    for x in self.connections:
                        p = copy.deepcopy(i.line)
                        q = copy.deepcopy(x.line)
                        if p != q:
                            p.remove(self.coord)
                            q.remove(self.coord)
                            if p[0][0] == q[0][0] or p[0][1] == q[0][1]:
                                through = True
                                break
                    if through:
                        break


                if not through:
                    pygame.draw.circle(window, colour, (int(self.coord[0]), int(self.coord[1])), self.radius-2, 0)

class Wall:
    def __init__(self, start, end):
        self.verticies = [start, end]
        self.maxhealth = 10

        #show
        self.line = [self.verticies[0].coord, self.verticies[1].coord]
        self.colour = (73,73,73)

        #top left + roofing
        if self.line[0][0] == self.line[1][0]:
            state = "verti"
            if self.line[0][1] < self.line[1][1]:
                topleft = self.line[0]
            else:
                topleft = self.line[1]
        else:
            state = "hori"
            if self.line[0][0] < self.line[1][0]:
                topleft = self.line[0]
            else:
                topleft = self.line[1]

        
        roofing = [copy.deepcopy(topleft), copy.deepcopy(topleft)]
        if state == "hori":
            for i in range(2):
                roofing[i][0] += 10
            roofing[0][1] += 10
            roofing[1][1] -= 10
        else:
            for i in range(2):
                roofing[i][1] += 10
            roofing[0][0] += 10
            roofing[1][0] -= 10
        
        self.roofing = [False, False]
        for i in range(2):
            pycoord = Coordfinder(roofing[i])
            if pycoord == False:
                pass
            elif B.grid[pycoord[0]][pycoord[1]].outer:
                pass
            else:
                self.roofing[i] = pycoord
            

        #connections
        for i in self.verticies:
            i.connections.append(self)

        #states
        self.gate = False
        self.unchangeable = False

        #rect
        self.rect = pygame.draw.line(window, self.colour, self.line[0], self.line[1], 5)

    def Show(self):
        self.rect = pygame.draw.line(window, self.colour, self.line[0], self.line[1], 5)

    def GateTransition(self):
        if self.gate:
            self.gate = False
        else:
            self.gate = True

        #colour
        if self.gate:
            self.colour = (50,50,50)
        else:
            self.colour = (73,73,73)

        #health
        if self.gate:
            self.maxhealth = 5
        else:
            self.maxhealth = 10

    def Remove(self):
        for i in self.verticies:
            i.connections.remove(self)
        W.walls.remove(self)

    def RoofProvoke(self):
        for i in self.roofing:
            if i != False:
                #reset grid
                for x in range(B.width):
                    for y in range(B.height):
                        B.grid[x][y].exhausted = False

                B.grid[i[0]][i[1]].RoofWork()


#PAWNS ========================================
class Pawn:
    def __init__(self, pycoord):
        #details
        self.coord = CoordConverter(pycoord, True)
        self.deg = 0
        self.move = False
        self.vel = 1
        self.radius = 10
        self.pawn = True
        self.colour = (40,73,87)
        self.maxhealth = copy.deepcopy(self.health)

        #team
        if self.team == 0:
            self.colour = (24,80,96)
        else:
            self.colour = (118,26,26)

        #pathing
        self.pycoord = pycoord
        self.path = []

        #image
        if self.image != False:
            self.width = self.image.get_width()
            self.height = self.image.get_height()

        #overview
        self.combat = False
        self.status = "idle"
        self.overview = "pawn"

    def Show(self):
        #health show
        temp = [0,0,0]
        for i in self.colour:
            temp[self.colour.index(i)] = i * (self.health/self.maxhealth) 

        colour = (temp[0], temp[1], temp[2])


        pygame.draw.circle(window, colour, (int(self.coord[0]), int(self.coord[1])), self.radius, 0)
        if self.image != False:
            window.blit(self.image, (self.coord[0]-self.width//2, self.coord[1]-self.height//2))


        if self.selected:
            pygame.draw.circle(window, (181,230,29), (int(self.coord[0]), int(self.coord[1])), self.radius+1, 5)

            #draw pathing line
            if len(self.path) > 0:
                pygame.draw.lines(window, self.colour, False, ([self.coord] + self.path))

        if self.combat:
            if self.melee:
                if self.attackline != False:
                    if self.reload > self.maxreload - 50:
                        pygame.draw.line(window, self.colour, self.coord, self.attackline, 5)

    def Move(self):
        self.pycoord = Coordfinder(self.coord)
        if self.move:
            self.Jostle()
            if self.distance > 0:
                #trig
                rad = math.radians(self.deg)
                trig = []
                trig.append(self.vel * math.sin(rad))
                trig.append(self.vel * math.cos(rad))
                #bob
                bob = math.sin(self.distance/4)
                self.coord[1] += bob

                for i in range(0,2):
                    #displace
                    self.coord[i] += trig[i]

                #move
                self.distance -= self.vel
            else:
                #delete path
                if len(self.path) > 0:
                    self.path.pop(0)
                if len(self.path) > 0:
                    self.Orientation(self.path[0])
                else:
                    if self.sig == "worker":
                        self.Deposit()

                    #resource collection
                    if self.status == "commuting":
                        self.harvesting = True
                        self.status = "harvesting"
                    elif self.status == "hauling":
                        self.FindWorksite(self.resourcepoint)
                    else:
                        self.move = False
                        self.status = "idle"
        else:
            self.Jostle()
        
         
        if self.combat:
            if self.reload > 0:
                self.reload -= 1
            else:
                self.CombatScan()

    def Task(self, coord):
        pycoord = Coordfinder(coord)
        if pycoord != False:
            if not pycoord == Coordfinder(self.coord):
                if not B.grid[pycoord[0]][pycoord[1]].blocked:
                    #pathfind
                    impossible, path = self.PathFinder(pycoord)
                    if not impossible:
                        if not M.shift:
                            self.path = []
                        self.path += path
                        self.Orientation(self.path[0])

                        if self.status != "commuting" or self.status != "hauling":
                            self.status = "moving"
                        self.move = True
                    else:
                        self.move = False
                        self.path = []
                        if self.sig == "worker":
                            self.harvesting = False
                            self.harvesting = False
                            self.resourcepoint = False
                        self.status = "idle"
                    return impossible

    def PathFinder(self, destination):
        #A* pathfinding
        if M.shift and len(self.path) > 0:
            self.pycoord = Coordfinder(self.path[-1])
        else:
            self.pycoord = Coordfinder(self.coord)
        start = B.grid[self.pycoord[0]][self.pycoord[1]]
        end = B.grid[destination[0]][destination[1]]
        Open = [start] #nodes yet to be evaluated
        Closed = [] #nodes already evaluated

        #reset Fcost
        for x in range(B.width):
            for y in range(B.height):
                B.grid[x][y].Fcost = False
                B.grid[x][y].parent = False

        start.Fcost = 0
        found = False
        impossible = False
        ticker = [[-1,-1],[0,-1],[1,-1],[1,0],[1,1],[0,1],[-1,1],[-1,0]]
        while not found and not impossible:
            #find min
            Min = 9999999
            smallest = 0
            for i in Open:
                if i.Fcost < Min:
                    smallest = i
                    Min = i.Fcost
            current = smallest
            
            if len(Open) == 0:
                impossible = True
                break

            Open.remove(current)
            Closed.append(current)

            #found query
            if current == end:
                found = True
                break

            #find neighbours
            x,y = current.pycoord
            neighbours = []
            for i in ticker:
                node = B.grid[x+i[0]][y+i[1]]
                if not node.blocked:

                    #barricade
                    intersects = False
                    rect = FindRect(current.coord, node.coord)
                    for z in W.walls:
                        if rect.colliderect(z.rect):
                            if self.team == 1 or z.gate == False:
                                intersects = True
                                break

                    if not intersects:
                        neighbours.append(node)

            #examine neighbours
            for i in neighbours:
                if not (i in Closed or i.blocked):
                    i.CostFinder(current, end)
                    if not (i in Open):
                        Open.append(i)

        #conclusion
        if not impossible:
            path = []
            if current == start:
                found = True
                path.append(current.coord)
            else:
                found = False
            
            while not found:
                path.append(current.coord)
                current = current.parent

                if current == start:
                    found = True
                    
            path.reverse()
        else:
            path = False

        return impossible, path

    def Orientation(self, point):
        #hypotenuse
        x = point[0] - self.coord[0] #if x positive point is to the right
        y = point[1] - self.coord[1] #if y positive point is below

        hypotenuse = math.sqrt(x**2 + y**2)

        #deg
        self.distance = hypotenuse
        self.deg = 0
        trig = math.degrees(math.asin(x/hypotenuse))

        if x == 0 or y == 0:
            if y < 0:
                self.deg = 180
            if x > 0:
                self.deg = 90
            elif x < 0:
                self.deg = -90

        else:
            if y > 0:
                self.deg +=  trig
            elif y < 0:
                self.deg = 180 - trig

    def Jostle(self):
        #jostling pawns
        for x in B.pawns:
            for i in x:
                if i != self:
                    self.NudgeDisplacement(i.coord)

        rect = pygame.Rect(self.coord, (self.radius, self.radius))
        for i in B.buildings:
            self.StaticJostle(rect, i)
        for i in B.resources:
            self.StaticJostle(rect, i)
                       
    def StaticJostle(self, rect, i):
        if i.obstruct:
            if rect.colliderect(i.rect):
                center = [i.coord[0] + B.thickness/2*i.dim[0], i.coord[1] + B.thickness/2*i.dim[1]]
                self.FirmDisplacement(center)

    def FirmDisplacement(self, a):
        x = a[0] - self.coord[0] #if x positive point is to the right
        y = a[1] - self.coord[1] #if y positive point is below
        hypotenuse = math.sqrt(x**2 + y**2)

        if hypotenuse == 0:
            disp = [random.randint(-1,1),random.randint(-1,1)]
        else:
            deg = 0
            trig = math.degrees(math.asin(x/hypotenuse))

            if x == 0 or y == 0:
                if y < 0:
                    deg = 180
                if x > 0:
                    deg = 90
                elif x < 0:
                    deg = -90

            else:
                if y > 0:
                    deg +=  trig
                elif y < 0:
                    deg = 180 - trig

            #displacement
            disp = [0,0]
            disp[0] = math.sin(math.radians(deg)) * 1.5
            disp[1] = math.cos(math.radians(deg)) * 1.5

        for i in range(0,2):
            self.coord[i] -= disp[i]

    def NudgeDisplacement(self, a):
        x = a[0] - self.coord[0] #if x positive point is to the right
        y = a[1] - self.coord[1] #if y positive point is below
        hypotenuse = math.sqrt(x**2 + y**2)

        if hypotenuse < self.radius*1.5:
            if hypotenuse == 0:
                disp = [random.randint(-1,1),random.randint(-1,1)]
            else:
                deg = 0
                trig = math.degrees(math.asin(x/hypotenuse))

                if x == 0 or y == 0:
                    if y < 0:
                        deg = 180
                    if x > 0:
                        deg = 90
                    elif x < 0:
                        deg = -90

                else:
                    if y > 0:
                        deg +=  trig
                    elif y < 0:
                        deg = 180 - trig

                #displacement
                disp = [0,0]
                disp[0] = math.sin(math.radians(deg)) * 0.5
                disp[1] = math.cos(math.radians(deg)) * 0.5

            reverse = [0,0]
            for i in range(0,2):
                self.coord[i] -= disp[i]
                reverse[i] = disp[i]

            self.BarrierCheck(reverse)
                
    def BarrierCheck(self, reverse):
        rect = pygame.Rect(self.coord, (self.radius, self.radius))

        #barriercheck        
        for i in W.walls:
            if rect.colliderect(i.rect):
                for i in range(0,2):
                    self.coord[i] += reverse[i]
                break

    def Dead(self):
        for i in range(0,5):
            B.particles.append(Particle(self.coord, self.colour, random.uniform(3, 5)))
        B.pawns[self.team].remove(self)

        if self.team == 0:
            B.population -= 1

        if self.selected:
            if M.selected != False:
                if len(M.selected) == 1:
                    M.selected = False
                else:
                    M.selected.remove(self)

class Unit(Pawn):
    def __init__(self, pycoord, team):
        self.selected = False
        self.cost = [1,1,1]
        self.team = team

        super().__init__(pycoord)

class Ranged:
    def __init__(self):
        #combat
        self.combat = True
        self.melee = False
        self.attackline = False
        self.reload = 0
        self.maxreload = 150

        if self.team == 0:
            self.otherteam = 1
        else:
            self.otherteam = 0

        #ranged
        self.accuracysway = 15
        self.range = 6

    def CombatScan(self):
        #frame is the area surrounding a unit and 
        #goes clockwise starting in the top left
        #query are the units grid coordinates
        #ticker is the cycles through the clockwise motion
        ticker = self.TickerDepth(self.range)

        neighbours = []
        for i in ticker:
            pycoord = [self.pycoord[0]+i[0], self.pycoord[1]+i[1]]
            for p in B.pawns[self.otherteam]:
                if p.pycoord == pycoord:
                    neighbours.append(p)

        if len(neighbours) > 0:
            i = random.choice(neighbours)
            dest = [i.coord[0]+random.randint(-self.accuracysway, self.accuracysway), i.coord[1]+random.randint(-self.accuracysway, self.accuracysway)]
            B.particles.append(Arrow(self.coord, dest, self))
            self.reload = self.maxreload

    def TickerDepth(self, depth):
        #frame is the area surrounding a unit and 
        #goes clockwise starting in the top left
        #query are the units grid coordinates
        #ticker is the cycles throught the clockwise motion
        ticker = []
        for a in range(-depth, depth+1):
            for b in range(-depth, depth+1):
                ticker.append([a])
                ticker[len(ticker)-1].append(b)

        ticker.remove([0,0])

        return ticker

class Melee:
    def __init__(self):
        self.combat = True
        self.attackline = False
        self.reload = 0
        self.maxreload = 250
        self.melee = True

        if self.team == 0:
            self.otherteam = 1
        else:
            self.otherteam = 0

    def CombatScan(self):
        #frame is the area surrounding a unit and 
        #goes clockwise starting in the top left
        #query are the units grid coordinates
        #ticker is the cycles through the clockwise motion
        ticker = [[-1,-1],[0,-1],[1,-1],[1,0],[0,0],[1,1],[0,1],[-1,1],[-1,0]] 
        #barricade
        removals = []
        for i in ticker:
            node = CoordConverter([self.pycoord[0]+i[0], self.pycoord[1]+i[1]], True)
            rect = FindRect(self.coord, node)
            for z in W.walls:
                if rect.colliderect(z.rect):
                    removals.append(i)
                    break
        for i in removals:
            ticker.remove(i)

        neighbours = []
        for i in ticker:
            pycoord = [self.pycoord[0]+i[0], self.pycoord[1]+i[1]]
            for p in B.pawns[self.otherteam]:
                if p.pycoord == pycoord:
                    neighbours.append(p)

        if len(neighbours) > 0:
            i = random.choice(neighbours)
            i.health -= self.strength
            self.attackline = i.coord
            if i.health <= 0:
                i.Dead()
            self.reload = self.maxreload
        else:
            self.attackline = False

#==player
class Officer(Unit, Melee):
    def __init__(self, pycoord):
        self.image = pygame.image.load("images\\units\\officer.png").convert_alpha()
        self.sig = "officer"

        #gameplay
        self.health = 6
        self.strength = 3

        Unit.__init__(self, pycoord, 0)
        Melee.__init__(self)

class Archer(Unit, Ranged):
    def __init__(self, pycoord):
        self.image = pygame.image.load("images\\units\\archer.png").convert_alpha()
        self.sig = "archer"

        #gameplay
        self.health = 3
        self.strength = 1

        Unit.__init__(self, pycoord, 0)
        Ranged.__init__(self)

class Warrior(Unit, Melee):
    def __init__(self, pycoord):
        self.image = pygame.image.load("images\\units\\warrior.png").convert_alpha()
        self.sig = "warrior"

        #gameplay
        self.health = 9
        self.strength = 5

        Unit.__init__(self, pycoord, 0)
        Melee.__init__(self)
        self.radius = 13

class Levy(Unit, Melee):
    def __init__(self, pycoord):
        self.image = pygame.image.load("images\\units\\levy.png").convert_alpha()
        self.sig = "levy"

        #gameplay
        self.health = 6
        self.strength = 1

        Unit.__init__(self, pycoord, 0)
        Melee.__init__(self)

class Worker(Unit):
    def __init__(self, pycoord):
        self.image = False
        self.sig = "worker"

        #gameplay
        self.health = 3
        self.strength = 1

        #resource collection
        self.maxharvestdelay = 250
        self.harvestdelay = 0
        self.harvesting = False
        self.resourcepoint = False
        self.holding = [0,0,0]

        Unit.__init__(self, pycoord, 0)

    def HarvestCommand(self, resourcepoint):
        #connecting
        enclosed = self.FindWorksite(resourcepoint)

        if not enclosed:
            resourcepoint.workers.append(self)
            self.resourcepoint = resourcepoint      

    def FindMore(self):
        self.harvesting = False
        trek = []
        rpoint = []
        for i in B.resources:
            if i.type == self.resourcepoint.type:
                #hypotenuse
                x = self.coord[0] - i.coord[0]
                y = self.coord[1] - i.coord[1]
                trek.append(math.sqrt(x**2 + y**2))
                rpoint.append(i)

        if len(rpoint) > 0:
            index = trek.index(min(trek))
            self.resourcepoint = rpoint[index]
        else:
            self.resourcepoint = False
        
        if self.resourcepoint != False:
            self.resourcepoint.workers.append(self)
            if self.status == "harvesting" or self.status == "commuting":
                self.FindWorksite(self.resourcepoint)
            elif self.status == "hauling":
                self.FindDepositsite()
        else:
            self.move = False
        
        if len(self.path) == 0:
            self.path.append(copy.deepcopy(self.coord))
        
    def FindWorksite(self, resourcepoint):
        trek = []
        nodes = []
        resourcepoint.GatherScan()
        for i in resourcepoint.gathertiles:
            if not i.blocked:
                ignore = False
                if not resourcepoint.obstruct:
                    if abs(i.pycoord[0] - resourcepoint.pycoord[0]) <= 1 and abs(i.pycoord[1] - resourcepoint.pycoord[1]) <= 1:
                        ignore = True

                if not ignore:
                    #hypotenuse
                    x = self.coord[0] - i.coord[0]
                    y = self.coord[1] - i.coord[1]
                    trek.append(math.sqrt(x**2 + y**2))
                    nodes.append(i)

        if len(nodes) > 0:
            index = trek.index(min(trek))
            optimal = nodes[index]
            coord = Centralise(optimal.coord)
            impossible = self.Task(coord)
            if not impossible:
                self.status = "commuting"
            return False
        else:
            return True

    def FindDepositsite(self):
        trek = []
        nodes = []
        for i in B.nodes:
            if i.depositable:
                #hypotenuse
                x = self.coord[0] - i.coord[0]
                y = self.coord[1] - i.coord[1]
                trek.append(math.sqrt(x**2 + y**2))
                nodes.append(i)

        index = trek.index(min(trek))
        optimal = nodes[index]
        coord = Centralise(optimal.coord)
        impossible = self.Task(coord)
        if not impossible:
            self.status = "hauling"
        return impossible

    def Harvest(self):
        if not self.harvestdelay > 0:
            if sum(self.holding) < 10:
                i = self.resourcepoint.type
                self.resourcepoint.resourcepool -= 1
                self.holding[i] += 1
                #effects
                for i in range(0,10):
                    B.particles.append(Particle(self.coord, (94,57,38), random.uniform(1, 3)))

                self.harvestdelay = copy.deepcopy(self.maxharvestdelay)
        
                if not self.resourcepoint.resourcepool > 0:
                    self.resourcepoint.Barren()
            else:
                self.harvesting = False
                impossible = self.FindDepositsite()

                if not impossible:
                    self.harvestdelay = copy.deepcopy(self.maxharvestdelay)

                    if not self.resourcepoint.resourcepool > 0:
                        self.resourcepoint.Barren()
        else:
            #delay
            self.harvestdelay -= 1

    def Deposit(self):
        self.pycoord = Coordfinder(self.coord)
        if B.grid[self.pycoord[0]][self.pycoord[1]].depositable:
            for i in range(0,3):
                B.totalresources[i] += round(self.holding[i])

            self.holding = [0,0,0]

#==enemy
class Peon(Unit, Melee):
    def __init__(self, pycoord):
        self.image = False
        self.sig = "peon"

        #gameplay
        self.health = 3
        self.strength = 1

        Unit.__init__(self, pycoord,  1)
        Melee.__init__(self)

#STATIC ========================================
class Static:
    def __init__(self, held):
        self.selected = False
        self.pawn = False
        
        #image
        self.width = self.image.get_width()
        self.height = self.image.get_height()

        #coord
        self.held = held
        self.coord = [0,0]
        self.pycoord = [False, False]

        #jostle
        self.rect = False

    def Show(self):
        if self.held:
            self.coord[0], self.coord[1] = E.coord[0]-self.width/2, E.coord[1]-self.height/2

        window.blit(self.image, self.coord)

        self.rect = pygame.Rect(self.coord[0], self.coord[1], self.width, self.height)
        if self.selected:
            pygame.draw.rect(window, (153,217,234), self.rect, 3)

    def FrameScan(self):
        #frame is the area surrounding a unit and 
        #goes clockwise starting in the top left
        #query are the units grid coordinates
        #ticker is the cycles through the clockwise motion
        ticker = []
        for a in range(-1, self.dim[0]+1):
            for b in range(-1, self.dim[1]+1):
                ticker.append([a])
                ticker[-1].append(b)

        ticker.remove([0,0])

        #makes the frame the same length as the ticker

        X, Y = self.pycoord
        frame = []
        for x in ticker:
            i = B.grid[X+x[0]][Y+x[1]]
            if not i.blocked:
                #barricade
                intersects = False
                pycoord = copy.deepcopy(self.pycoord)

                for z in range(0,2):
                    if self.dim[z] < 1:
                        if x[z] <= 0:
                            pycoord[z] = self.pycoord[z]
                        elif x[z] > 0:
                            pycoord[z] = self.pycoord[z]+x[z]
                            if x[z] != self.dim[0]:
                                pycoord -= 1

                center = CoordConverter(pycoord, True)

                rect = FindRect(center, i.coord)
                for z in W.walls:
                    if rect.colliderect(z.rect):
                        intersects = True
                        break

                if not intersects:
                    frame.append([X+x[0], Y+x[1]])

        return frame

#BUILDINGS===
class Building(Static):
    def __init__(self, held):
        #options
        self.options = ["Demolish"]
        self.trainable = False

        #gameplay
        self.dropsite = False
        self.health = 20
        self.cost = [10,10,10]

        #overview
        self.overview = "building"

        super().__init__(held)
    
    def Demolish(self):
        B.buildings.remove(self)
        if M.selected != False:
            if len(M.selected) > 1:
                M.selected.remove(self)
            else:
                M.selected = False

        #remove blocked
        for x in range(self.dim[0]):
            for y in range(self.dim[1]):
                i = B.grid[self.pycoord[0]+x][self.pycoord[1]+y]
                if self.obstruct:
                    i.blocked = False
                i.builton = False
                if self.dropsite:
                    i.depositable = False

        #pop
        if self.sig == "house":
            B.maxpopulation -= self.popadd

    def Drop(self, pycoord):
        self.held = False
        if pycoord == False:
            remove = True
        else:
            #allign
            for i in range(0,2):
                if pycoord[i] %2 == 0:
                    pycoord[i] -= 1

            self.coord = CoordConverter(pycoord, False)
            self.pycoord = pycoord

            #check obstruction
            remove = False
            for x in range(self.dim[0]):
                for y in range(self.dim[1]):
                    i = B.grid[self.pycoord[0]+x][self.pycoord[1]+y]
                    if i.blocked or i.builton:
                        remove = True
                        break
                if remove:
                    break

            #cost check
            for i in range(0,3):
                if B.totalresources[i] - self.cost[i] < 0:
                    remove = True
                

        #if it violates the checks
        if remove:
            B.buildings.remove(self)
        else:
            #set blocked
            for x in range(self.dim[0]):
                for y in range(self.dim[1]):
                    i = B.grid[self.pycoord[0]+x][self.pycoord[1]+y]
                    if self.obstruct:
                        i.blocked = True
                    i.builton = True
                    if self.dropsite:
                        i.depositable = True
                        

            #exceptions
            if self.sig == "house":
                B.maxpopulation += self.popadd

            #cost
            for i in range(0,3):
                B.totalresources[i] -= self.cost[i]

class Trainable:
    def __init__(self, unit):
        self.unit = unit
        self.trainable = True
        self.options.append("Train "+self.unit)

        #training
        self.queue = 0
        self.maxtrainingdelay = 50 
        self.trainingdelay = 0
        self.training = False

    def Train(self):
        if self.trainingdelay > 0:
            self.trainingdelay -= 1
        else:
            #frame scan
            frame = self.FrameScan()

            if len(frame) > 0:
                pycoord = random.choice(frame)

                if self.unit == "worker":
                    unit = Worker(pycoord)
                elif self.unit == "levy":
                    unit = Levy(pycoord)
                elif self.unit == "officer":
                    unit = Officer(pycoord)
                elif self.unit == "archer":
                    unit = Archer(pycoord)

                B.pawns[0].append(unit)
                
                #queue
                self.InitiateTraining()

    def InitiateTraining(self):
        if self.queue == 0:
            self.training = False
        else:
            self.training = True
            self.queue -= 1
            self.trainingdelay = self.maxtrainingdelay

    def Task(self):
        if self.unit == "worker":
            temp = Worker([0,0])
        elif self.unit == "levy":
            temp = Levy([0,0])
        elif self.unit == "officer":
            temp = Officer([0,0])
        elif self.unit == "archer":
            temp = Archer([0,0])

        #cost
        remove = False
        for i in range(0,3):
            B.totalresources[i] -= temp.cost[i]

        #cost check
        for i in range(0,3):
            if B.totalresources[i] < 0:
                remove = True

        #pop
        B.population += 1
        #pop check
        if B.population > B.maxpopulation:
            remove = True

        #reverse
        if remove:
            for i in range(0,3):
                B.totalresources[i] += temp.cost[i]
            B.population -= 1
        else:
            self.queue += 1
            if not self.training:
                self.InitiateTraining()

#==
class House(Building):
    def __init__(self, held):
        self.sig = "house"
        self.image = pygame.image.load("images\\buildings\\house.png").convert_alpha()
        
        self.dim = [1 * B.bgridthickness,1 * B.bgridthickness]
        self.obstruct = True
        
        Building.__init__(self, held)
        self.popadd = 10

class Stockpile(Building):
    def __init__(self, held):
        self.sig = "stockpile"
        self.image = pygame.image.load("images\\buildings\\stockpile.png").convert_alpha()

        #details
        self.dim = [1 * B.bgridthickness,1 * B.bgridthickness]
        self.obstruct = False

        Building.__init__(self, held)
        self.dropsite = True

class Center(Building, Trainable):
    def __init__(self, held):
        self.sig = "center"
        self.image = pygame.image.load("images\\buildings\\center.png").convert_alpha()

        #details
        self.dim = [2 * B.bgridthickness,2 * B.bgridthickness]
        self.obstruct = False

        Building.__init__(self, held)
        Trainable.__init__(self, "worker")
        self.dropsite = True

class Barracks(Building, Trainable):
    def __init__(self, held):
        self.sig = "barracks"
        self.image = pygame.image.load("images\\buildings\\barracks.png").convert_alpha()

        #details
        self.dim = [2 * B.bgridthickness,2 * B.bgridthickness]
        self.obstruct = True

        Building.__init__(self, held)
        Trainable.__init__(self, "archer")

class Palace(Building, Trainable):
    def __init__(self, held):
        self.sig = "palace"
        self.image = pygame.image.load("images\\buildings\\palace.png").convert_alpha()

        #details
        self.dim = [2 * B.bgridthickness,2 * B.bgridthickness]
        self.obstruct = True

        Building.__init__(self, held)
        Trainable.__init__(self, "officer")


#RESOURCES===
class Resource(Static):
    def __init__(self, held):
        self.workers = []
        self.gathertiles = []

        self.dim = [1 * B.bgridthickness,1 * B.bgridthickness]

        #overview
        self.overview = "resource"

        super().__init__(held)

    def Barren(self):
        self.Remove()

        if M.selected != False:
            if self in M.selected:
                if len(M.selected) == 1:
                    M.selected = False
                else:
                    M.selected.remove(self)

        for i in self.workers:
            i.FindMore()

    def Drop(self, pycoord):
        self.held = False
        if pycoord == False:
            remove = True
        else:
            #allign
            for i in range(0,2):
                if pycoord[i] %2 == 0:
                    pycoord[i] -= 1

            self.coord = CoordConverter(pycoord, False)
            self.pycoord = pycoord

            #check obstruction
            remove = False
            for x in range(self.dim[0]):
                for y in range(self.dim[1]):
                    i = B.grid[self.pycoord[0]+x][self.pycoord[1]+y]
                    if i.blocked or i.builton:
                        remove = True
                        break
                if remove:
                    break

            #cost check
            if self.sig == "grain":
                for i in range(0,3):
                    if B.totalresources[i] - self.cost[i] < 0:
                        remove = True
                

        #if it violates the checks
        if remove:
            B.resources.remove(self)
        else:
            #set blocked
            for x in range(self.dim[0]):
                for y in range(self.dim[1]):
                    i = B.grid[self.pycoord[0]+x][self.pycoord[1]+y]
                    if self.obstruct:
                        i.blocked = True
                    i.builton = True

            #exceptions
            if self.sig == "logs":
                self.WoodGen()

            #cost
            if self.sig == "grain":
                for i in range(0,3):
                    B.totalresources[i] -= self.cost[i]
    
    def GatherScan(self):
        self.gathertiles = []
        frame = self.FrameScan()
        for i in frame:
            x = B.grid[i[0]][i[1]]
            self.gathertiles.append(x)

    def Remove(self):
        B.resources.remove(self)

        for x in range(self.dim[0]):
            for y in range(self.dim[1]):
                i = B.grid[self.pycoord[0]+x][self.pycoord[1]+y]
                if self.obstruct:
                    i.blocked = False
                i.builton = False

#==
class Grain(Resource):
    def __init__(self, held):
        self.image = pygame.image.load("images\\resources\\grain.png").convert_alpha()
        self.sig = "grain"
        self.obstruct = False

        #harvesting
        self.type = 0
        self.workercapacity = 1
        self.resourcepool = 150
        super().__init__(held)
        self.cost = [10,10,10]

class Rain(Resource):
    def __init__(self, held):
        self.image = pygame.image.load("images\\resources\\rain.png").convert_alpha()
        self.sig = "rain"
        self.obstruct = False

        #harvesting
        self.type = 1
        self.workercapacity = 5
        self.resourcepool = random.randint(50,250)
        super().__init__(held)

class Logs(Resource):
    def __init__(self , held):
        self.image = pygame.image.load("images\\resources\\wood.png").convert_alpha()
        self.sig = "logs"
        self.obstruct = True

        #harvesting
        self.type = 2
        self.workercapacity = 5
        self.resourcepool = 100
        super().__init__(held)

    def WoodGen(self):
        if random.randint(1,5) > 2:
            recno = random.randint(1,8)
            ticker = [[-1,-1],[0,-1],[1,-1],[1,0],[1,1],[0,1],[-1,1],[-1,0]] 

            for i in range(0, recno):
                log = random.choice(ticker)
                ticker.remove(log)

                x = self.pycoord[0] + log[0]
                y = self.pycoord[1] + log[1]

                B.resources.append(Logs(False))
                B.resources[-1].Drop([x, y])


#EFFECTS ========================================
class Particle:
    def __init__(self, coord, colour, vel):
        self.coord = copy.deepcopy(coord)
        self.deg = random.randint(-90, 90)+180
        self.vel = vel
        self.colour = colour
        self.sig = "particle"

    def Show(self):
        rad = math.radians(self.deg)
        opp = self.vel * math.sin(rad)
        adj = self.vel * math.cos(rad)

        self.coord[0] += opp
        self.coord[1] += adj

        pygame.draw.circle(window, self.colour, (int(self.coord[0]), int(self.coord[1])), 4*int(self.vel), 0)

        #entropy
        if self.sig == "particle":
            if random.choice([True, False, False, False]):
                if self.deg < 180:
                    self.deg += random.randint(-10,0)
                else:
                    self.deg += random.randint(0,10)


        self.vel -= .1
        if self.vel <= 0:
            B.particles.remove(self)     

class Drizzle:
    def __init__(self, coord, colour, menu):
        self.sig = "drizzle"
        if B.coord[1] < 0:
            self.coord = [coord[0]-100, B.coord[1]]
        else:
            self.coord = [coord[0]-100, 0]
        
        self.last = copy.deepcopy(self.coord)
        self.deg = 10
        num =  random.randint(0,15)
        self.vel = num + 10
        self.dest = coord[1]
        self.colour = colour
        self.menu = menu

    def Show(self):
        rad = math.radians(self.deg)
        opp = self.vel * math.sin(rad)
        adj = self.vel * math.cos(rad)

        self.coord[0] += opp
        self.coord[1] += adj

        pygame.draw.line(window, self.colour, (self.last), (self.coord), 1)

        #entropy
        self.last = copy.deepcopy(self.coord)
        if self.last[1] > self.dest:
            if self.menu:
                for i in range(0,5):
                    B.menuparticles.append(Splash(self.coord, self.colour, True))
                B.menuparticles.remove(self)  
            else:
                for i in range(0,5):
                    B.particles.append(Splash(self.coord, self.colour, False))
                B.particles.remove(self)  


class Splash:
    def __init__(self, coord, colour, menu):
        self.coord = copy.deepcopy(coord)
        self.deg = random.randint(-90, 90)+180
        self.vel = random.uniform(1, 3)
        self.colour = colour
        self.sig = "splash"
        self.menu = menu

    def Show(self):
        rad = math.radians(self.deg)
        opp = self.vel * math.sin(rad)
        adj = self.vel * math.cos(rad)

        self.coord[0] += opp
        self.coord[1] += adj

        pygame.draw.circle(window, self.colour, (int(self.coord[0]), int(self.coord[1])), int(self.vel), 0)

        #entropy
        if random.choice([True, False]):
            if self.deg < 180:
                self.deg += random.randint(-10,0)
            else:
                self.deg += random.randint(0,10)
        self.vel -= .1
        if self.vel <= 0:
            if self.menu:
                B.menuparticles.remove(self)  
            else:
                B.particles.remove(self)  

class Droplet:
    def __init__(self, destination):
        self.sig = "droplet"
        self.colour = (40,73,87)
        if B.coord[1] < 0:
            self.coord = [destination[0], B.coord[1]]
        else:
            self.coord = [destination[0], 0]
        self.des = destination
        self.vel = 5
        self.bad = False

    def Show(self):
        pygame.draw.circle(window, self.colour, (int(self.coord[0]), int(self.coord[1])), 23, 0)
        self.coord[1] += self.vel
        self.vel += 0.25

        B.particles.append(Trail(self.coord, self.colour))

        if self.coord[1] >= self.des[1]:
            B.particles.remove(self)
            #effects
            for i in range(0,15):
                B.particles.append(Particle(self.coord, self.colour, random.uniform(3, 5)))
            #rain
            if self.bad:
                self.Spawn()
            else:
                self.Destroy()
                if random.randint(0,5) == 0:
                    B.resources.append(Rain(False))
                    B.resources[-1].Drop(Coordfinder(self.des))

    def Destroy(self):
        ticker = [[-1,-1],[0,-1],[1,-1],[0,0],[1,0],[1,1],[0,1],[-1,1],[-1,0]]
        d = Coordfinder(self.des)
        for i in ticker:
            p = [d[0] + i[0],d[1] + i[1]]
            z = B.grid[p[0]][p[1]]
            if z.builton:
                self.BuildingSearch(p)
            
            for u in B.pawns[0]:
                if u.pycoord == p:
                    u.Dead()

    def BuildingSearch(self, p):
        for b in B.buildings:
            for x in range(0,b.dim[0]):
                for y in range(0,b.dim[1]):
                    if p[0] == b.pycoord[0] + x and p[1] == b.pycoord[1] + y:
                        b.Demolish()
                        return

class BadDroplet(Droplet):
    def __init__(self, destination):
        Droplet.__init__(self, destination)
        self.bad = True
        self.colour = (118,26,26)

    def Spawn(self):
        pycoord = Coordfinder(self.coord)
        if pycoord != False:
            for i in range(0,3):
                B.pawns[1].append(Peon(pycoord))

class Trail(Particle):
    def __init__(self, coord, colour):
        super().__init__(coord, colour, random.randint(3, 5))
        self.deg = random.randint(-30, 30)+180
        self.sig = "trail"

class Arrow:
    def __init__(self, start, dest, archer):
        self.coord = copy.deepcopy(start)
        self.vel = 10
        self.archer = archer
        self.sig = "arrow"

        #hypotenuse
        x = dest[0] - start[0] #if x positive point is to the right
        y = dest[1] - start[1] #if y positive point is below

        hypotenuse = math.sqrt(x**2 + y**2)

        #deg
        self.distance = hypotenuse
        self.deg = 0
        trig = math.degrees(math.asin(x/hypotenuse))

        if x == 0 or y == 0:
            if y < 0:
                self.deg = 180
            if x > 0:
                self.deg = 90
            elif x < 0:
                self.deg = -90

        else:
            if y > 0:
                self.deg +=  trig
            elif y < 0:
                self.deg = 180 - trig

        #image
        self.image = pygame.transform.rotate(pygame.image.load("images\\units\\archer.png").convert_alpha(), self.deg)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def Show(self):
        rad = math.radians(self.deg)
        opp = self.vel * math.sin(rad)
        adj = self.vel * math.cos(rad)

        self.coord[0] += opp
        self.coord[1] += adj
        self.distance -= self.vel

        window.blit(self.image, (self.coord[0]-self.width/2, self.coord[1]-self.height/2))
        
        if self.distance < 0:
            B.particles.remove(self)
            self.Hit()

    def Hit(self):
        for z in B.pawns:
            for i in z:
                if i.coord[0]+i.radius > self.coord[0] >i.coord[0]-i.radius and i.coord[1]+i.radius > self.coord[1] > i.coord[1] - i.radius:
                    x = i.coord[0] - self.coord[0]
                    y = i.coord[1] - self.coord[1]
                    hypotenuse = math.sqrt(x**2 + y**2)
                    if hypotenuse < i.radius:
                        i.health -= self.archer.strength
                        if i.health < 0:
                            i.Dead()
                        return
                        
#functions
def Coordfinder(coord):
    #finds coords on board
    xFound = False
    yFound = False
    X = 0
    Y = 0
    for x in range(0, B.width):
        if (xFound == False) and (coord[0] >= (B.coord[0] + B.thickness*x)) and (coord[0] <= (B.coord[0] + B.thickness*(x+1))):
            X = x
            xFound = True
        for y in range(0, B.height):
            if (yFound == False) and (coord[1] >= B.coord[1] + B.thickness*y) and (coord[1] <= B.coord[1] + B.thickness*(y+1)):
                Y = y
                yFound = True

    if xFound and yFound:
        pycoord = [X, Y]
        return pycoord
    else:
        return False

def CoordConverter(pycoord, center):
    coord = []
    if center:
        for i in range(0,2):
            coord.append(pycoord[i]*B.thickness + B.coord[i] + B.thickness//2)
    else:
        for i in range(0,2):
            coord.append(pycoord[i]*B.thickness + B.coord[i])

    return coord 

def Centralise(coord):
    pycoord = Coordfinder(coord)
    result = CoordConverter(pycoord, True)
    return result

def FindRect(a, b):
    x = [a[0], b[0]]
    y = [a[1], b[1]]

    rect = pygame.Rect(min(x), min(y), abs(a[0]-b[0]), abs(a[1]-b[1]))

    return rect

def PauseScreen():
    #title
    TitleFont = pygame.font.SysFont('', 150)
    Title = TitleFont.render('PAUSED', False, (255,255,255))

    B.menuparticles = []
    loop = True
    while loop:
        pygame.time.delay(10)
        window.fill((21,35,45))

        for i in range(0,3):
            coord = [random.randint(0, scr_width), random.randint(scr_height//2, scr_height - scr_height//3)]
            B.menuparticles.append(Drizzle(coord, (214,245,246), True))

        for i in B.menuparticles:
            i.Show()
        
        #title
        window.blit(Title,(scr_width/2-200,scr_height/2))
        
        for event in pygame.event.get():
            #mouse
            if event.type == pygame.MOUSEMOTION:
                M.coord[0], M.coord[1] = pygame.mouse.get_pos()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.mouse.get_pressed()[0]:
                    #exit
                    if M.coord[0] > scr_width-50 and M.coord[0] < scr_width and M.coord[1] < scr_height and M.coord[1] > scr_height-50:
                        loop = False
                        B.RUN = False
            #keys
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_ESCAPE]:
                    loop = False

            
                        
        pygame.display.update()

def TitleScreen():
    TitleFont = pygame.font.SysFont('', 300)
    SubFont = pygame.font.SysFont('', 20)

    Title = TitleFont.render('ASH', False, (255,255,255))
    Sub = SubFont.render('PRESS ENTER TO START', False, (255,255,255))

    B.menuparticles = []
    loop = True
    while loop:
        pygame.time.delay(10)
        window.fill((21,35,45))

        for i in range(0,3):
            coord = [random.randint(0, scr_width), random.randint(scr_height//2, scr_height - scr_height//4)]
            B.menuparticles.append(Drizzle(coord,(214,245,246), True))

        for i in B.menuparticles:
            i.Show()
        
        #title
        window.blit(Title,(scr_width/2-220,scr_height/2-100))

        #subtitle
        window.blit(Sub,(scr_width/2-90,scr_height/2+110))
        
        for event in pygame.event.get():
            #mouse
            if event.type == pygame.MOUSEMOTION:
                M.coord[0], M.coord[1] = pygame.mouse.get_pos()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.mouse.get_pressed()[0]:
                    #exit
                    if M.coord[0] > scr_width-50 and M.coord[0] < scr_width and M.coord[1] < scr_height and M.coord[1] > scr_height-50:
                        loop = False
                        B.RUN = False

            #keys
            if event.type == pygame.KEYDOWN:
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_RETURN]:
                        loop = False
                        
        pygame.display.update()


if __name__ == '__main__':
    B = Board()

    #monitors
    M = GameMonitor()
    W = WallMonitor()
    E = BuildMonitor()

    B.LogGen()
    W.BorderGen()

    TitleScreen()
    while B.RUN:
        pygame.time.delay(1)
        window.fill((21,35,45))
        #input
        if M.wallmode:
            W.Input()          
        else:
            B.RainStorm()
            if M.buildmode:
                E.Input()
            else:
                M.Input()
            for x in B.pawns:
                for i in x:
                    if i.sig == "worker":
                        if i.harvesting:
                            i.Harvest()
                        else:
                            i.Move()
                    else:
                        i.Move()
            for i in B.buildings:
                if i.trainable:
                    if i.training:
                        i.Train()

        #show
        B.Show()
        for i in B.resources:
            i.Show()
        for i in B.buildings:
            i.Show()
        for x in B.pawns:
            for i in x:
                i.Show()
        for i in W.walls:
            i.Show()
        for i in W.verticies:
            i.Show()
        if not M.wallmode:
            for i in B.particles:
                i.Show()

        #UI
        if M.buildmode:
            E.Showcase()
        else:
            M.BottomBar()
            M.OverviewBox()
        B.ResourcePanel()
        
        pygame.display.update()