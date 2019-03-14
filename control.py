import RPi.GPIO as GPIO
import time
import pickle
from Passcodes import PermanentPasscode, OneTimePasscode, TemporaryPasscode, RepeatPasscode

class Controller:

    def __init__(self):
        self.passcodeLength = 4
        self.passcodes = []
        #self.passcodes.append(PermanentPasscode('1234'))
        #self.passcodes.append(OneTimePasscode('5678'))
        #self.passcodes.append(TemporaryPasscode('1357', time.time(), time.time()+60))
        #self.passcodes.append(RepeatPasscode('2468', 0, (12+7)*3600+36*60, [False, False, False, True, False, False, True]))
        self.readPasscodes()
        
    def readPasscodes(self):
        file = open("Passcode-data.dat", "rb")
        self.passcodes = pickle.load(file)
        file.close()

    def writePasscodes(self):
        file = open("Passcode-data.dat", "wb")
        pickle.dump(self.passcodes, file)
        file.close()

    def addPasscode(self, passcode):
        self.passcodes.append(passcode)
        self.writePasscodes()

    def removePasscode(self, passcode):
        self.passcodes.remove(passcode)
        self.writePasscodes()

    def changePasscode(self, oldPasscode, newPasscode):
        self.removePasscode(oldPasscode)
        self.addPasscode(newPasscode)
        self.writePasscodes()

    def updatePasscodes(self, newPasscodes):
        self.passcodes = newPasscodes
        self.writePasscodes()

    def clearPasscodes(self):
        self.passcodes = []
        self.writePasscodes()

    def lock(self):
        servoPIN = 23
        GPIO.setup(servoPIN, GPIO.OUT)

        p = GPIO.PWM(servoPIN, 50)   # GPIO 23 for PWM with 50Hz
        p.start(7.5)    # Initialization
        time.sleep(0.5)

        # 90 degrees
        p.ChangeDutyCycle(2.5)
        print(2.5)
        time.sleep(2)

        p.stop()

    def unlock(self):
        servoPIN = 23
        GPIO.setup(servoPIN, GPIO.OUT)

        p = GPIO.PWM(servoPIN, 50)   # GPIO 23 for PWM with 50Hz
        p.start(2.5)    # Initialization
        time.sleep(0.5)

        # 0 degrees
        p.ChangeDutyCycle(7.5)
        print(7.5)
        time.sleep(2)

        p.stop()

    def waitForPasscode(self):
        GPIO.setmode(GPIO.BCM)

        MATRIX = [
            [1,2,3,"A"],
            [4,5,6,"B"],
            [7,8,9,"C"],
            ["*",0,"#","D"]
        ]

        ROW = [26,19,13,6] # BCM numbering
        COL = [22,27,17,4] # BCM numbering

        for j in range(4):
            GPIO.setup(COL[j], GPIO.OUT)
            GPIO.output(COL[j], 1)

        for i in range(4):
            GPIO.setup(ROW[i], GPIO.IN, pull_up_down = GPIO.PUD_UP)

        try:
            attempt = ''
            while(True):
                for j in range(4):
                    GPIO.output(COL[j], 0)

                    for i in range(4):
                        if GPIO.input(ROW[i]) == 0:
                            print(MATRIX[i][j])
                            while(GPIO.input(ROW[i]) == 0):
                                pass
                            num = str(MATRIX[i][j])
                            attempt += num
                            if num == '*':
                                self.lock()
                                attempt = ''
                            if num == '#' or num == 'A' or num == 'B' or num == 'C' or num == 'D':
                                attempt = ''
                            if len(attempt) == self.passcodeLength:
                                if self.isValid(attempt):
                                    print("Unlock")
                                    self.unlock()
                                attempt = ''
                            time.sleep(0.3)

                    GPIO.output(COL[j], 1)
        except KeyboardInterrupt:
            print("Cleaning")
            GPIO.cleanup()

    def isValid(self, attempt):
        for passcode in self.passcodes:
            if passcode.isActive(time.time()):
                if attempt == passcode.getPasscode():
                    passcode.use()
                    return True
        return False
        
Controller().waitForPasscode()

