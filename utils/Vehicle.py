# -*- coding: utf-8 -*-
from random import randint
import time

class MyVehicle:
    tracks = []
    def __init__(self, i, xi, yi, max_age):
        self.i = i
        self.x = xi
        self.y = yi
        self.tracks = []
        self.done = False
        self.state = '0'
        self.age = 0
        self.max_age = max_age
        self.dir = None
    
    def updateCoords(self, xn, yn):
        self.age = 0
        self.tracks.append([self.x,self.y])
        self.x = xn
        self.y = yn
    
    def setDone(self):
        self.done = True
    
    def timedOut(self):
        return self.done
    
    def going_DOWN(self, mid_start, mid_end):
        if len(self.tracks) >= 2:
            if self.state == '0':
                if self.tracks[-1][0] > mid_start and self.tracks[-2][0] <= mid_start:
                    self.state = '1'
                    return True
            else:
                return False
        else:
            return False

    def age_one(self):
        self.age += 1
        if self.age > self.max_age:
            self.done = True
        return True

class MultiPerson:
    def __init__(self, persons, xi, yi):
        self.vehicles = vehicles
        self.x = xi
        self.y = yi
        self.tracks = []
        self.done = False