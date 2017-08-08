#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""The main game code"""

import datetime
import math
import os
import random
import time

import pygame

import unofficial_utilities_for_pygame as utils
from __init__ import __author__, __credits__, __version__

PATH = os.path.dirname(os.path.realpath(__file__))


class Airplane(utils.ImprovedSprite):
    """The class for an airplane sprite."""
    NEXT_ID = 0
    def __init__(self, image, x=(0, 0, 0), y=None, altitude=None,
            speed=250, throttle=50, player_id=None, airspace_dim=[700, 700]):
        """Initializes the instance."""
        if y == None and altitude != None: x, y = x
        elif y == None: x, y, altitude = x
        super(Airplane, self).__init__(image, x, y)
        self.pos = list(self.rect.center)
        self.upos = self.pos[:]
        self.upos[0] *= (1000.0/airspace_dim[0])
        self.upos[1] *= (1000.0/airspace_dim[1])
        self.altitude = altitude
        self.heading = 0
        self.vertical_heading = 0
        self.speed = speed # m/s
        self.horizontal_velocity = speed
        self.vertical_velocity = 0
        self.throttle = throttle
        self.acceleration = 0 # m/s^2
        self.roll_level = 0
        self.roll = 0
        self.vertical_roll_level = 0

        self.points = 0
        self.exit_code = 0
        self.health = 100
        if player_id == None: self.id = Airplane.NEXT_ID; Airplane.NEXT_ID += 1
        else: self.id = player_id

    def draw(self, screen, airspace_x, airspace_y=None):
        """Draws the airplane."""
        if airspace_y == None: airspace_x, airspace_y = airspace_x
        image_rotated = pygame.transform.rotate(self.image, -self.heading)
        draw_rect = self.rect.copy()
        draw_rect.x += airspace_x
        draw_rect.y += airspace_y
        screen.blit(image_rotated, draw_rect)

    def update(self, fps=60, airspace_dim=[700, 700]):
        """Updates the plane."""
        # calculate display stretch
        x_str = airspace_dim[0] / 1000.0
        y_str = airspace_dim[1] / 1000.0

        # initialize damage
        damage = 0
        
        # move the plane
        self.roll = self.get_roll(self.roll_level)
        self.heading += (self.roll / fps)
        if self.heading < -180: self.heading += 360
        elif self.heading > 180: self.heading -= 360
        self.vertical_heading = self.get_vert_hd(self.vertical_roll_level)

        # acceleration
        self.acceleration = (self.throttle ** 2 / 250.0
                - self.speed ** 2 / 6250.0)
        self.speed += (self.acceleration / float(fps))
        self.horizontal_speed = self.speed * math.cos(math.radians(
                self.vertical_heading))
        self.vertical_velocity = self.speed * math.sin(math.radians(
                self.vertical_heading))
        
        hspeed = self.horizontal_speed / float(fps) / 100
        vspeed = self.vertical_velocity / float(fps) / 100
        self.pos[0] += math.sin(math.radians(self.heading)) * hspeed * x_str
        self.pos[1] -= math.cos(math.radians(self.heading)) * hspeed * y_str
        self.rect.center = tuple(self.pos)
        self.altitude += vspeed

        # User-freindly coordinates
        # Goes from 0 to +1000 in both dimensions
        self.upos = self.pos[:]
        self.upos[0] *= (1/x_str)
        self.upos[1] *= (1/y_str)

        # overspeed/overthrottle damage
        if self.speed > 500:
            damage += (self.speed - 500) ** 2 / 75000.0 / fps

        # deal damage
        self.health -= damage

    # Function that approximates the 5, 10, 20, 30 roll of Slight Fimulator 1.0
    get_roll = lambda s, r: (35/198.0) * r**3 + (470/99.0) * r
    get_vert_hd = lambda s, r: 10*r


class Objective(utils.ImprovedSprite):
    """The class for an objective sprite."""
    NEXT_ID = 0
    def __init__(self, image, x=(0, 0, 0), y=None, altitude=None, obj_id=None,
            airspace_dim=[700, 700]):
        """Initializes the instance."""
        if y == None and altitude != None: x, y = x
        elif y == None: x, y, altitude = x
        super(Objective, self).__init__(image, x, y)
        self.altitude = altitude

        if obj_id == None: self.id = Objective.NEXT_ID; Objective.NEXT_ID += 1
        else: self.id = obj_id

        self.upos = list(self.rect.center[:])
        self.upos[0] -= airspace_dim[0] / 2
        self.upos[0] *= (2000.0/airspace_dim[0])
        self.upos[1] -= airspace_dim[1] / 2
        self.upos[1] *= (2000.0/airspace_dim[1])

    def draw(self, screen, airspace_x, airspace_y=None):
        """Draws the objective."""
        if airspace_y == None: airspace_x, airspace_y = airspace_x
        draw_rect = self.rect.copy()
        draw_rect.x += airspace_x
        draw_rect.y += airspace_y
        screen.blit(self.image, draw_rect)

    def update(self, airspace_dim=[700, 700]):
        """Updates the objective."""
        self.upos = list(self.rect.center[:])
        self.upos[0] *= (1000.0/airspace_dim[0])
        self.upos[1] *= (1000.0/airspace_dim[1])


class Airspace(pygame.rect.Rect):
    """The class for an airspace."""
    def __init__(self, x=(0, 0, 0, 0), y=None, w=None, h=None):
        """Initializes the instance."""
        if y == None: x, y, w, h = x # Input: 1 list
        elif w == None and h == None: (x, y), (w, h) = x, y # Input: 2 lists
        super(Airspace, self).__init__(x, y, w, h)
        self.panel = pygame.rect.Rect(x-(w/140), y-(h/140), w*71/70, h*71/70)
        self.planes = pygame.sprite.Group()
        self.objectives = pygame.sprite.Group()

    def draw(self, screen, image, color, panel_color):
        """Draws the airspace and everything inside it."""
        pygame.draw.rect(screen, panel_color, self.panel)
        pygame.draw.rect(screen, color, self)
        screen.blit(image, (self.topleft))
        for plane in self.planes: plane.draw(screen, self.x, self.y)
        for obj in self.objectives: obj.draw(screen, self.x, self.y)

    def update(self, fps, *args, **kw):
        """Updates the airspace."""
        self.planes.update(fps, self.size, *args)
        self.objectives.update(self.size, *args)

        for plane in self.planes:
            collisions = pygame.sprite.spritecollide(plane,
                    self.objectives, True, self.collided)
            for collision in collisions:
                plane.points += 1
                self.generate_objective(collision)

    def add_plane(self, plane):
        """Adds a plane to the airspace.

        Creates a new airplane if an image is supplied."""
        if type(plane) != Airplane:
            plane = Airplane(plane, self.width/2, self.height/2, 1800,
                    airspace_dim=self.size)
        self.planes.add(plane)

    def generate_objective(self, prev_objective):
        """Generates an objective."""
        objective = Objective(prev_objective.image, airspace_dim=self.size)
        # no collide, correct coords
        objective_correct = [False, False]
        while objective_correct != [True, True]:
            objective_correct = [False, False]
            # generate objective
            objective.rect.centerx = random.randint(0, self.width)
            objective.rect.centery = random.randint(0, self.height)
            objective.altitude = (prev_objective.altitude
                    + random.randint(-150, 150))
            if objective.altitude > 6000: objective.altitude = 8000
            elif objective.altitude < 1000: objective.altitude = 1000
            # test for collision
            if not pygame.sprite.spritecollide(objective, self.planes,
                    False, self.collided):
                objective_correct[0] = True
            if self.in_bounds(objective):
                objective_correct[1] = True
        self.objectives.add(objective)

    def generate_initial_objective(self, image):
        """Generates an objective."""
        objective = Objective(image, airspace_dim=self.size)
        # no collide, correct coords
        objective_correct = [False, False]
        while objective_correct != [True, True]:
            objective_correct = [False, False]
            # generate objective
            objective.rect.centerx = random.randint(0, self.width)
            objective.rect.centery = random.randint(0, self.height)
            objective.altitude = random.randint(2000, 2500)
            # test for collision
            if not pygame.sprite.spritecollide(objective, self.planes,
                    False, self.collided):
                objective_correct[0] = True
            if self.in_bounds(objective):
                objective_correct[1] = True
        self.objectives.add(objective)

    def collided(self, airplane, objective, altitude_tolerance=100):
        """Tests if a airplane collides with an objective."""
        return (airplane.rect.colliderect(objective.rect)
                and abs(objective.altitude - airplane.altitude)
                <= altitude_tolerance)

    def in_bounds(self, sprite, use_zeroed_coords=True):
        """Tests if an object is in bounds.

        If use_zeroed_coords is True, it will assume the airspace's
            topleft is (0, 0)."""
        if isinstance(sprite, pygame.sprite.Sprite):
            rect = sprite.rect
        else: rect = sprite
        if use_zeroed_coords:
            return (rect.left >= 0 and rect.top >= 0
                    and rect.right <= self.width
                    and rect.bottom <= self.height)
        else:
            return (rect.left >= self.left and rect.top >= self.top
                    and rect.right <= self.right
                    and rect.bottom <= self.bottom)


class GameWindow(utils.Game):
    """The main window for the game."""
    GAME_STAGES = {}
    GAME_LOOPS = {}
    DEFAULT_SIZE = (1280, 960)
    def __init__(self, size=DEFAULT_SIZE):
        """Initializes the instance. Does not start the game."""
        super(GameWindow, self).__init__(
                resources_path="%s/resources.zip" % PATH,
                title="Slight Fimulator v%s" % __version__,
                icontitle="Slight Fimulator",
                size=size, bg=utils.Game.BG_PRESETS['bg-color'])
        self.prev_size = self.size

    # -------------------------------------------------------------------------
    # STARTUP CODE
    # -------------------------------------------------------------------------

    def startup(self):
        """A function that is run once on startup."""
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.mixer.init()
        #self.screen = pygame.display.set_mode(self.size, pygame.RESIZABLE)

        self.images['logo'] = pygame.transform.scale(self.images['logo'],
                (521, 178))
        self.set_image_sizes()

        self.setup_variables()

    def setup_variables(self):
        """Sets up the variables."""
        self.airspace = Airspace(self.size[0]*7/16, self.size[1]/24,
                self.size[0]*35/64, self.size[1]*35/48)
        self.airspace.add_plane(self.images['navmarker'])
        self.planes = self.airspace.planes # Another name for the same object
        self.objectives = self.airspace.objectives
        self.airspace.generate_initial_objective(
                self.images['objectivemarker'])

        self.stage = 0
        self.status = 'status'
        self.exit_code = 0

        self.output_log = True
        self.previous_time = time.time()
        self.time = time.time()
        self.tick = 0

        self.event_log = pygame.USEREVENT
        pygame.time.set_timer(self.event_log, 5000)

    def set_image_sizes(self):
        """Sets up the images."""
        for image_name in self.images:
            x, y = self.images[image_name].get_rect().size
            x *= (self.size[0] / float(self.DEFAULT_SIZE[0]))
            y *= (self.size[1] / float(self.DEFAULT_SIZE[1]))
            x = int(x); y = int(y)
            self.images[image_name] = pygame.transform.scale(
                    self.images[image_name], (x, y))

    def prepare_log(self):
        """Prepares the log."""
        self.log_filepath = "%s/logs/%s" % (PATH, datetime.datetime.now())
        self.log_file = open(self.log_filepath, 'wt')
        output = []
        output.append("TIME\t\t")
        for plane_id in range(len(self.planes)):
            output.append("PLN-%i\t\t\t\t\t\t\t\t\t\t\t\t\t\t" % plane_id)
        for objective_id in range(len(self.objectives)):
            output.append("OBJ-%i\t\t\t" % objective_id)
        output.append("\nTICK:\tDUR:\t")
        for plane_id in range(len(self.planes)):
            output.append(
"X:\tY:\tALT:\tSPD:\tACCEL:\tVSPD:\tTHRTL:\t\
HDG:\tVHDG:\tCR:\tROLL:\tVCR:\tPTS:\tDMG:\t")
        for objective_id in range(len(self.objectives)):
            output.append("X:\tY:\tALT:\t")
        self.log_file.write(''.join(output))
        if self.output_log:
            print('======RESTART LOG======')
            print(''.join(output))
        self.log_file.close()

    # -------------------------------------------------------------------------
    # FUNCTIONS
    # -------------------------------------------------------------------------

    def update_screen_size(self, new_size):
        """Updates the screen size."""
        self.prev_size = self.size
        new_size = list(new_size)
        if self.size[0] == self.prev_size[0]:
            new_size[0] = self.size[0] * (self.size[1] / self.prev_size[1])
        if self.size[1] == self.prev_size[1]:
            new_size[1] = self.size[1] * (self.size[0] / self.prev_size[0])
        self.screen = pygame.display.set_mode(new_size, pygame.RESIZABLE)
        self.size = new_size
        self.scale_images()

    def scale_images(self):
        """Sets up the images."""
        for image_name in self.images:
            x, y = self.images[image_name].get_rect().size
            x *= (self.size[0] / float(self.prev_size[0]))
            y *= (self.size[1] / float(self.prev_size[1]))
            x = int(x); y = int(y)
            self.images[image_name] = pygame.transform.scale(
                    self.images[image_name], (x, y))

    def draw(self):
        """Draws the info box and airspace."""
        for plane in self.planes:
            if plane.id == 0: break
        # get closest objective
        closest_dist = float('inf')
        for obj in self.objectives:
            dist = ((plane.rect.x - obj.rect.x) ** 2
                    + (plane.rect.y - obj.rect.y) ** 2) ** 0.5
            if dist < closest_dist:
                closest_dist = dist
                closest_objective = obj
            
        # attitude tape
        attitude_tape = pygame.transform.rotate(self.images['attitudetape'],
                plane.roll)
        attitude_tape_rect = attitude_tape.get_rect()
        attitude_tape_rect.center = (self.size[0]*7/32,
                self.size[1]*9/24)
        offset_y = self.size[1]*3/160*plane.vertical_roll_level
        offset_x = math.tan(math.radians(plane.roll)) * offset_y
        attitude_tape_rect.x += offset_x
        attitude_tape_rect.y += offset_y
        self.screen.blit(attitude_tape, attitude_tape_rect)
        # surrounding panel
        pygame.draw.rect(self.screen, self.colors['panel'],
                (self.size[0]*5/256, self.size[1]*5/48,
                self.size[0]*25/64, self.size[1]*7/48))
        pygame.draw.rect(self.screen, self.colors['panel'],
                (self.size[0]*5/256, self.size[1]*5/48,
                self.size[0]*15/128, self.size[1]*25/48))
        pygame.draw.rect(self.screen, self.colors['panel'],
                (self.size[0]*75/256, self.size[1]*5/48,
                self.size[0]*15/128, self.size[1]*25/48))
        pygame.draw.rect(self.screen, self.colors['panel'],
                (self.size[0]*5/256, self.size[1]/2,
                self.size[0]*25/64, self.size[1]*7/48))
        self.screen.blit(self.images['attitudecrosshair'],
                (self.size[0]*35/256, self.size[1]*9/24))

        self.airspace.draw(self.screen, self.images['navcircle'],
                self.colors['black'], self.colors['panel'])
        
        # NAV text
        self.draw_text("PLANE LOCATION:",
                self.size[0]*29/64, self.size[1]/16,
                color_id='white', mode='topleft')
        self.draw_text("X: %.2f KM" % (plane.upos[0] / 10.0),
                self.size[0]*29/64, self.size[1]/12,
                color_id='white', mode='topleft')
        self.draw_text("Y: %.2f KM" % (plane.upos[1] / 10.0),
                self.size[0]*29/64, self.size[1]*5/48,
                color_id='white', mode='topleft')
        self.draw_text("ALT: %i M" % plane.altitude,
                self.size[0]*29/64, self.size[1]/8,
                color_id='white', mode='topleft')
        self.draw_text("HEADING: %.1f" % plane.heading,
                self.size[0]*91/128, self.size[1]/16,
                color_id='white', mode='midtop')
        self.draw_text("ANGLE: %.1f" % plane.vertical_heading,
                self.size[0]*91/128, self.size[1]/12,
                color_id='white', mode='midtop')
        self.draw_text("SCORE: %i" % plane.points,
                self.size[0]*91/128, self.size[1]*5/48,
                color_id='white', mode='midtop')
        self.draw_text("OBJECTIVE LOCATION:",
                self.size[0]*31/32, self.size[1]/16,
                color_id='white', mode='topright')
        self.draw_text("X: %.2f KM" % (closest_objective.upos[0] / 10.0),
                self.size[0]*31/32, self.size[1]/12,
                color_id='white', mode='topright')
        self.draw_text("Y: %.2f KM" % (closest_objective.upos[1] / 10.0),
                self.size[0]*31/32, self.size[1]*5/48,
                color_id='white', mode='topright')
        self.draw_text("ALT: %i M" % closest_objective.altitude,
                self.size[0]*31/32, self.size[1]/8,
                color_id='white', mode='topright')

        # panel text
        self.draw_text("THROTTLE",
                self.size[0]*3/128, self.size[1]/4,
                color_id='white', mode='topleft')
        self.draw_text("%.1f%%" % plane.throttle,
                self.size[0]*3/128, self.size[1]*13/48,
                color_id='white', mode='topleft')
        self.draw_text("SPEED",
                self.size[0]*5/16, self.size[1]/4,
                color_id='white', mode='topleft')
        self.draw_text("%.1f KM/H" % (plane.speed * 3.6),
                self.size[0]*5/16, self.size[1]*13/48,
                color_id='white', mode='topleft')
        self.draw_text("HORIZ. SPD",
                self.size[0]*5/16, self.size[1]*17/48,
                color_id='white', mode='topleft')
        self.draw_text("%.1f KM/H" % (plane.horizontal_speed * 3.6),
                self.size[0]*5/16, self.size[1]*3/8,
                color_id='white', mode='topleft')
        self.draw_text("VERT. SPD",
                self.size[0]*5/16, self.size[1]*11/24,
                color_id='white', mode='topleft')
        self.draw_text("%.1f KM/H" % (plane.vertical_velocity * 3.6),
                self.size[0]*5/16, self.size[1]*23/48,
                color_id='white', mode='topleft')
        self.draw_text("DAMAGE:", 30, 425,
                color_id='white', mode='topleft')
        self.draw_text("%.1f%%" % (100 - plane.health), 30, 450,
                color_id='white', mode='topleft')

        # throttle bar
        pygame.draw.rect(self.screen, self.colors['red'], (150, 355, 20, 125))
        pygame.draw.rect(self.screen, self.colors['white'],
                (150, 380, 20, 100))
        pygame.draw.rect(self.screen, self.colors['green'],
                (150, 480-plane.throttle, 20, plane.throttle))

    def control_plane(self):
        """Allows you to control the plane."""
        for plane in self.planes:
            if plane.id == 0: break
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            plane.roll_level -= (1.0 / self.fps)
            if plane.roll_level < -4: plane.roll_level = -4
        elif keys[pygame.K_RIGHT]:
            plane.roll_level += (1.0 / self.fps)
            if plane.roll_level > 4: plane.roll_level = 4
        if keys[pygame.K_UP]:
            plane.vertical_roll_level -= (1.0 / self.fps)
            if plane.vertical_roll_level < -4: plane.vertical_roll_level = -4
        elif keys[pygame.K_DOWN]:
            plane.vertical_roll_level += (1.0 / self.fps)
            if plane.vertical_roll_level > 4: plane.vertical_roll_level = 4
        if keys[pygame.K_F2]:
            plane.throttle -= (4.0 / self.fps)
            if plane.throttle < 0: plane.throttle = 0
        elif keys[pygame.K_F4]:
            plane.throttle += (4.0 / self.fps)
            if plane.throttle > 125: plane.throttle = 125

        for event in self.events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1: plane.throttle = 0
                elif event.key == pygame.K_F3: plane.throttle = 50
                elif event.key == pygame.K_F5: plane.throttle = 100

    def log(self):
        """Writes in the log.

        The log logs every 5 seconds.  It records:
         - The game tick that the log is recording at
         - How many milliseconds long that tick was
         - The coordinates, heading and score of all planes
         - The coordinates of all objectives
        """
        self.log_file = open(self.log_filepath, 'at')
        output = []
        output.append("%i\t%i\t" % (self.tick,
                (self.time-self.previous_time) * 1000))
        for plane_id in range(len(self.planes)):
            for plane in self.planes:
                if plane.id == plane_id: break
            output.append(
                    "%.1f\t%.1f\t%i\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\
\t%.2f\t%.2f\t%.2f\t%i\t%.1f\t"
                    % (plane.upos[0], plane.upos[1], plane.altitude,
                    plane.speed, plane.acceleration,
                    plane.vertical_velocity, plane.throttle,
                    plane.heading, plane.vertical_heading, plane.roll_level,
                    plane.roll, plane.vertical_roll_level, plane.points,
                    100 - plane.health))
        for objective_id in range(len(self.objectives)):
            for objective in self.objectives:
                if objective.id == objective_id: break
            output.append("%.i\t%i\t%i\t" % (objective.upos[0],
                    objective.upos[1], objective.altitude))
        self.log_file.write(''.join(output))
        self.log_file.write('\n')
        if self.output_log: print(''.join(output))
        self.log_file.close()

    def get_tick_values(self):
        """Prepares the values for the log."""
        self.tick += 1
        self.previous_time = self.time
        self.time = time.time()
        

    # -------------------------------------------------------------------------
    # MAIN LOOP
    # -------------------------------------------------------------------------

    def game_loop(self):
        """One iteration of the main loop.

        (In reality, just runs one of the game loops)"""
        self.GAME_LOOPS[self.stage] (self)
        pygame.display.flip()
        for event in self.events:
            if event.type == pygame.QUIT or self.stage == 'END':
                return True
            elif event.type == pygame.VIDEORESIZE:
                self.update_screen_size(event.size)
            
    def startup_screen(self):
        """Activates the startup screen. Stage=0"""
        pygame.mixer.music.stop()
        pygame.mixer.music.load(self.music_files['chilled-eks'])
        pygame.mixer.music.play(-1)
    def game_loop_startup(self):
        """One iteration of the startup screen loop."""
        self.screen.blit(self.images['logo'], ((self.size[0]
                - self.images['logo'].get_width()) / 2,
                self.size[1]/18.8))
        self.screen.blit(self.images['logotext'], ((self.size[0]
                - self.images['logotext'].get_width()) / 2, self.size[1]/2.4))
        self.screen.blit(self.images['titleprompt'], (self.size[0]*35/64,
                self.size[1]*35/48))
        pygame.display.flip()
        for event in self.events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.stage = 1
                elif event.key == pygame.K_ESCAPE:
                    self._stage = 'END'
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.stage = 1
    GAME_STAGES[0] = startup_screen
    GAME_LOOPS[0] = game_loop_startup

    def main_screen(self):
        """Activates the main screen. Stage=1"""
        pygame.mixer.music.stop()
        pygame.mixer.music.load(self.music_files['chip-respect'])
        pygame.mixer.music.play(-1)
        self.prepare_log()
        self.log()
    def game_loop_main(self):
        """One iteration of the main loop."""
        self.control_plane()
        self.airspace.update(fps=self.fps)
        self.draw()
        pygame.display.flip()
        for event in self.events:
            if event.type == pygame.QUIT:
                self.stage = 2
                self.events.remove(event)
            if event.type == self.event_log:
                self.log()
        self.get_tick_values()
    GAME_STAGES[1] = main_screen
    GAME_LOOPS[1] = game_loop_main

    def end_screen(self):
        """Activates the end screen. Stage=2"""
        pygame.mixer.music.fadeout(10000) # Fades out over 10 seconds
        self.status = "You may now close the program."
    def game_loop_end(self):
        """One iteration of the end screen loop."""
##        screen.blit(exittitle, (25, 0))
##        screen.blit(exittext, (25, 100))
        self.draw_text(self.status, (self.size[0]/37.6, self.size[1]*35/48),
                mode='topleft', color_id="white")

        pygame.display.flip()
    GAME_STAGES[2] = end_screen
    GAME_LOOPS[2] = game_loop_end

    @property
    def stage(self):
        """Allows you to get the stage."""
        return self._stage
    @stage.setter
    def stage(self, new_value):
        """Allows you to set the stage variable to change the stage."""
        try: self.GAME_STAGES[new_value] (self)
        except Exception as e:
            print(e)
            raise ValueError("%s is not a stage." % new_value)
        self._stage = new_value