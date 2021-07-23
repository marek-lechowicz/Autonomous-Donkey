#!/usr/bin/python
# -*- coding: utf-8 -*-
from enum import Enum
from typing import Optional, Union

import motors
import sensors
import math

class ProgramState(Enum):
    START = 1
    RUNNING = 2

class SensorPosition(Enum):
    FRONT = 0
    FRONT_LEFT = 1
    LEFT = 3
    FRONT_RIGHT = 2
    RIGHT = 4

class Rotation(Enum):
    RIGHT = -90
    LEFT = 90
    TURN_BACK = 180

class Donkey:
    def __init__(self):
        #Motors
        self.left_motor = motors.MotorWithEncoder(DIR_pin=22, PWM_pin=17, ENC_pin=4)
        self.right_motor = motors.MotorWithEncoder(DIR_pin=23, PWM_pin=18, ENC_pin=26)

        #Sensors
        self.transducer = sensors.Transducer(device=0)

        #Path
        self.trace = list()
        self.angles = list()

        self.deviation = 0

    def learn_path(self):
        user_input = self.read_commands(ProgramState.START)
        self.preprocessing(user_input)

    def traverse_path(self, speed=50):

        while len(self.trace) > 0 or len(self.angles) > 0:
            flag_different_course_correction = False

            while self.transducer.get_distance(channel=SensorPosition.FRONT) > 30: #FIXME: CZY 30 cm na pewno?
                self.run(speed)
                if self.trace[0] < self.left_motor.distance:
                    self.trace.pop(0)
                    self.rotate(self.angles[0])
                    self.angles.pop(0)

            self.trace[0] -= self.left_motor.distance
            # zbędne, bo w while jest rotate
            # self.left_motor.reset_measurement()
            while not (self.transducer.get_distance(channel=SensorPosition.FRONT) > 30):
                self.stop()
                self.rotate(Rotation.LEFT)

                while self.transducer.get_distance(channel=SensorPosition.RIGHT) < 30:
                    self.run(speed)
                    self.deviation = self.left_motor.distance

                self.rotate(Rotation.RIGHT)

                while self.transducer.get_distance(channel=SensorPosition.RIGHT) < 30:
                    self.run(speed)

                    # obsluzenie sytuacji gdy przeszkoda stoi na 'zakrecie'
                    if self.trace[0] < self.left_motor.distance:
                        self.trace.pop(0)
                        if self.angles[0] == Rotation.LEFT:
                            self.trace[0] -= self.deviation
                        elif self.angles[0] == Rotation.RIGHT:
                            self.trace[0] += self.deviation
                        self.rotate(self.angles[0])
                        self.angles.pop(0)
                        flag_different_course_correction = True

            if not flag_different_course_correction:
                self.rotate(Rotation.RIGHT)
                while self.deviation > self.left_motor.distance:
                    self.run(speed)
                self.rotate(Rotation.LEFT)
                self.deviation = 0

    def rotate(self, angle: Union[Rotation, int] = 90, speed=20):
        #TODO: na razie bierzemy średnicę jakąś losową, trzeba zmierzyć

        d = 261
        rotate_distance = math.pi * d * angle / 360.0

        if angle > 0:
            left_motor_direction = 'B'
            right_motor_direction = 'F'
        else:
            left_motor_direction = 'F'
            right_motor_direction = 'B'

        self.left_motor.reset_measurement()

        while rotate_distance > self.left_motor.distance:
            self.left_motor.run(speed, left_motor_direction)
            self.right_motor.run(speed, right_motor_direction)

        self.left_motor.reset_measurement()

    def run(self, speed, direction='F'):
        self.left_motor.run(speed, direction)
        self.right_motor.run(speed, direction)

    def stop(self):
        self.left_motor.stop()
        self.right_motor.stop()

    def read_commands(self, program_state=ProgramState.RUNNING):
        if program_state == ProgramState.START:
            introduction = "This program will allow you to control the Donkey. \n" \
                           "You can command robot to move forward by typing the distance, you want the robot to travel. \n" \
                           "If You wish to change the direction type: \n" \
                           "R - to turn right \n" \
                           "L - to turn left \n" \
                           "T - to turn back \n" \
                           "F - to finish giving the commands \n\n"

            print(introduction)

        user_input = list()
        while True:
            command = input(">")
            if command == 'F':
                break

            # translacja na wartość kąta obrotu i odległość
            # robiona głównie dla ułatwienia późniejszego preprocessingu
            if command == 'R':
                command = '-90'
            elif command == 'L':
                command = '90'
            elif command == 'T':
                command = '180'
            else:
                command = int(command)

            user_input.append(command)

        return user_input

    def preprocessing(self, user_input):
        for i in range(len(user_input)):
            if type(user_input[i]) is int:
                if type(user_input[i]) == type(user_input[i - 1]) and i != 0:
                    self.trace[-1] += user_input[i]
                else:
                    self.trace.append(user_input[i])
            else:
                if type(user_input[i]) == type(user_input[i - 1]) and i != 0:
                    self.angles[-1] += int(user_input[i])
                else:
                    self.angles.append(int(user_input[i]))
