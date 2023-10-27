'''Hello there! I call this game Shoot The Rings (honestly for lack of a better name :)). It is a 2d game developed in Python with the Kivy library.

Click on the "?" icon button on the game's screen when you start the game to understand how its controls.

All you have to do are move, rotate, shoot and survive for as long as possible!

If I do continue working on this game, I plan to add a few more things like gamepad controls support. I think I should also change the jet to something else - maybe a car, or a tank?

Have some fun while playing.

Please send your honest and helpful feedbacks to francisali692@gmail.com.
'''

import os

#Seems like SDL2 is the best audio provider for this game as of now
os.environ['KIVY_AUDIO'] = 'sdl2'

#Redirect error messages to a file called ".logs.txt"
#import sys
# sys.stderr = open('./.logs.txt', 'w')

import math
import random
from itertools import cycle

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label

from kivy.vector import Vector
from kivy.graphics import Rectangle, Ellipse, Rotate, PushMatrix, PopMatrix, Color, Line
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import NumericProperty, BooleanProperty
from kivy.core.audio import SoundLoader


Window.size = [900, 600]

'''Set the background color of the window to some sort BLUE-GREY. 
You can tweak the values as you please.'''
#GREY = 26/255, 32/255, 38/255, 1
Window.clearcolor = 0.15, 80/255, 110/255, 1

Window.borderless = True
app = None

#Just converting the sines and cosines to accept arguments in degrees instead of radians.
sin = lambda x: math.sin(math.radians(x))
cos = lambda x: math.cos(math.radians(x))

soundfile = lambda f: os.path.join('sounds', f)

shooting_sound = SoundLoader.load(soundfile("blaster-2-81267.mp3"))
powerdown_sound = SoundLoader.load(soundfile("power-down-7103.mp3"))
hit_sound = SoundLoader.load(soundfile("mixkit-arcade-mechanical-bling-210.wav"))

#how fast the game's state is updated
UPDATE_TIME = 1/60 #In seconds

class Jet(Widget):
	KEY_HELD_DOWN = False #Boolean that keeps travck of whether a key is still held down or otherwise.
	speed_factor = 40
	pos_set_clock = None

	def __init__(self, **kws):
		super().__init__(**kws)
		self.size_hint = None, None
		with self.canvas.before:
			PushMatrix()
			self.rotation = Rotate(0, 0, 0, 1)
			Color(1, 1, 1, 1)
			self.sprite = Rectangle(source=os.path.join('res', 'plane_1.png'), pos=self.pos)
			PopMatrix()
			self.sprite.size = Vector(self.sprite.texture.size)/5.0
			self.sprite.pos = self.pos
			self.size = self.sprite.size
			#Set the center of rotation to the center of the widget’s bounding box.
			self.rotation.origin = self.center
		#self.bind(pos=self._move_sprite)
	
	def on_pos(self, inst, pos):
		'''This is a special method that creates an event listener and is called whenever there is a change in the `pos` property.'''
		self.sprite.pos = pos
		self.rotation.origin = self.center
	
	def on_center(self, inst, center):
		self.sprite.pos = self.pos
		self.rotation.origin = self.center
		
	def update_pos(self, direction):
		f = 10

		#Do nothing if the game hasn't started yet or is paused.
		if not app.STARTED or app.IS_PAUSED: return False
		if direction == "up":
			if self.top+f <= Window.height-120:
				self.y += f
		if direction == "down":
			if self.y-f >= 0:
				self.y += -f
		if direction == "left":
			if self.x-f >= 0:
				self.x += -f
		if direction == "right":
			if self.right+f <= Window.width:
				self.x += f

	def move(self, direction='up'):
		self.rotation.origin = self.center
		#Cancel any previous movement if any.
		try: self.move_timer.cancel()
		except: pass
		self.move_timer = Clock.schedule_interval(lambda dt: self.update_pos(direction), 1/60)
	
	def update_angle(self, factor):
		if not app.IS_PAUSED and app.STARTED:
			if self.KEY_HELD_DOWN:
				temp = self.rotation.angle
				self.rotation.angle *= 0
				self.rotation.angle = temp+factor
				return True
			return False #stops the clock scheduler
		return False

	def rotate(self, factor):
		if self.KEY_HELD_DOWN: return
		self.KEY_HELD_DOWN = True
		if not app.IS_PAUSED and app.STARTED:
			Clock.schedule_interval(lambda dt:self.update_angle(factor), 1/60)

	def shoot(self):
		if app.IS_PAUSED or not app.STARTED: return
		bullet = Bullet(self)
		bullet.set_direction(self.rotation.angle)
		
		'''I have to stop the previous sound before playing it again as the previous one may not have had the chance to have played completely'''
		shooting_sound.stop()
		shooting_sound.play()
		bullet.release()

class GameObject(Widget):
	def remove(self):
		self.upd_scheduler.cancel()
		Window.remove_widget(self)
		
class Bullet(GameObject):
	def __init__(self, jet:Jet, size=[8, 8], **kws):
		super().__init__(size=size, size_hint=[None,None], **kws)
		self.center = jet.center
		self.jet = jet
		with self.canvas:
			#We are simply using a red circle as the bullet
			Color(.1, .84, .1, 1)
			self.ellipse = Ellipse(size=self.size, pos=self.pos)
		
	def set_direction(self, angle):
		'''Sets the orientation/direction of the bullet based on the orientation of the jet'''
		#Set how much the bullet's position changes in both x and y directions in a particular amount of time
		angle += 90 #Just calibrating things right (pun intended. Hopefully it was a good one).
		self.velocity = 20 * Vector(cos(angle), sin(angle))
	
	def release(self):
		'''Adds a bullet to the window and releases it'''
		Window.add_widget(self)
		#Play a shooting sound here
		def update_pos(dt):
			if not app.IS_PAUSED:
				self.center = list(Vector(self.center) + self.velocity)
				self.ellipse.pos = Vector(self.center) - Vector(self.size)/2
				#Remove from the window once the bullet leaves the visible screen to improve performance
				if self.x < 0 or self.x > Window.width:
					if self.y < 0 or self.y > Window.height:
						self.remove()
		self.upd_scheduler = Clock.schedule_interval(update_pos, UPDATE_TIME)

class Ring(GameObject):
	def __init__(self, jet:Jet, **kws):
		super().__init__(**kws)
		self.jet = jet
		self.size = 20, 20
		self.size_hint = [None, None]
		with self.canvas.before:
			Color(1,
				random.random(),
				random.random(),
				1)
			#self.ellipse = Ellipse(size=self.size, pos=self.pos)
			self.ellipse = Line(circle=[*self.center, self.size[0]/2], width=1.5)
			
	def launch(self, angle, speed=1):
		'''Method to launch a ring in a given direction specified in degrees from an arbitrary ref point.'''
		#`velocity`: A velocity of 1 means 1 pixel/second in whatever direction it is headed.
		self.velocity = speed*Vector(cos(angle), sin(angle))
		self.is_still_colliding = False
		def update_pos(dt):
			if not app.IS_PAUSED and app.STARTED:
				self.center = list(Vector(self.center) + self.velocity)
				#self.ellipse.pos = Vector(self.center) - Vector(self.size)/2
				self.ellipse.circle = [*self.center, self.size[0]/2]
				if self.collide_widget(self.jet) and not self.is_still_colliding:
					app.HEALTH_PERCENTAGE -= 5
					self.is_still_colliding = True
					if app.HEALTH_PERCENTAGE <= 0:
						app.STARTED = False
						Window.remove_widget(self.jet)
						'''Do a gameover here'''
						powerdown_sound.play()
						try: self.jet.rotation_clock.cancel()
						except: pass
					#Play a hit sound here
					hit_sound.stop()
					hit_sound.play()
				if not self.collide_widget(self.jet):
					self.is_still_colliding = False
				#Effecting reflection about an axis caused by bouncing off a wall
				if self.top > Window.height-120 or self.y < 0:
					self.velocity.y *= -1 
				if self.right > Window.width or self.x < 0:
					self.velocity.x *= -1 
				bullets = filter(lambda w: isinstance(w, Bullet), Window.children)
				for bullet in bullets:
					if self.collide_widget(bullet):
						#self.canvas.before.remove(self.ellipse)
						self.remove()
			               
		self.upd_scheduler = Clock.schedule_interval(update_pos, 1/50)
		

class GameLayout(FloatLayout): pass

#Load the kivy file here. Though I can load my kivy file implicitly by just naming it to "maingame.kv", I prefer to load it myself.
Builder.load_file('main.kv')

class KeyBindings:
	@staticmethod
	def process_key_down(*args):
		keycode, scancode, text, modifiers = args[-4:]
		jet = app.jet
		keycode_mappings = {
			273: 'up',
			274: 'down',
			275: 'right',
			276: 'left',
			32: 'spacebar',
			97: 'A',
			100: 'D',
			120: 'X',
			13: 'Enter'
		}
		F = jet.speed_factor
		function_mappings = {
			'up': (lambda: jet.move('up')),
			'down': (lambda: jet.move('down')),
			'right': (lambda: jet.move('right')),
			'left': (lambda: jet.move('left')),
			'spacebar': (lambda: app.pause_play()),
			'A': (lambda: jet.rotate(+5)),
			'D': (lambda: jet.rotate(-5)),
			'X': (jet.shoot),
			'Enter': (jet.shoot)
		}
		callback = function_mappings.get(
			keycode_mappings.get(keycode)
			)
		#print("callback: ",callback)
		if callback: callback() #Calls a function to move the jet based on the keys pressed

	@classmethod
	def process_key_up(*args):
		*k, keycode, scancode = args[-4:]
		if keycode in range(273, 277):
			app.jet.move_timer.cancel()
		if keycode in [97, 100]:
			app.jet.KEY_HELD_DOWN = False

	@classmethod
	def initialize(cls):
		Window.bind(on_key_down= cls.process_key_down)
		Window.bind(on_key_up= cls.process_key_up)

class MainGame(App):
	TIME_COUNT = NumericProperty(0) 
	HEALTH_PERCENTAGE = NumericProperty(100) #Starts off having a health of 100%
	STARTED = BooleanProperty(False)
	IS_PAUSED = BooleanProperty(False)
	def build(self):
		self.root = GameLayout()
		self.jet = Jet()
		self.jet.center = Window.center
		self.root.add_widget(self.jet)
		Clock.schedule_interval(self.increment_gametime_count, 1/10)
		return self.root
		
	def pause_play(self):
		if self.STARTED:
			self.IS_PAUSED ^= 1

	def increment_gametime_count(self, dt):
		if not self.IS_PAUSED and self.STARTED:
			self.TIME_COUNT += 1/10
		#return str(self.TIME_COUNT)

	def start_game(self):
		import random
		self.jet.center = Window.center
		self.jet.rotation.angle = 0
		rings_left = list(filter(lambda c: isinstance(c, Ring), 
			Window.children))
		#Clear all rings remaining and start afresh.
		for ring in rings_left:
			ring.canvas.before.remove(ring.ellipse)
			ring.remove()
		#Reset the counter
		self.TIME_COUNT = 0
		def spew_ring(dt):
			if not app.IS_PAUSED and app.STARTED:
				obst = Ring(self.jet)
				Window.add_widget(obst)
				obst.launch(random.choice(range(10, 80, 10)), speed=9.0)
		Clock.schedule_interval(spew_ring, 2)
	
	def on_start(self):
		global app
		app = self
		KeyBindings.initialize()
		self.start_game()


game = MainGame()
game.run()