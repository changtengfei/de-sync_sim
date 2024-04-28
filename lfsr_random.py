'''
This module implement the lfsr_random class
'''

import random

class lfsr_random(object):

    POLYNOMIAL_16B      = 0xb400
    POLYNOMIAL_32B      = 0xd0000001
    NAME                = 'lfsr_random'
    TIME_UNIT           = 0.0000305 # unit is 30.5us
    
    def __init__(self, shift_reg):
    
        self.shift_reg = shift_reg
        
    def getRandomNumber_16bits(self):
    
        '''
        return a value between 0 0xffffs
        '''
        
        random_value = 0
        for i in range(16):
            random_value    |= (self.shift_reg & 0x01)<<i
            self.shift_reg   = (self.shift_reg>>1)^(-(self.shift_reg & 1) & self.POLYNOMIAL_16B)
            
        return random_value
        
    def getRandomNumber_32bits(self):
    
        '''
        return a value between 0 0xffffffffs
        '''
        
        random_value = 0
        for i in range(32):
            random_value    |= (self.shift_reg & 0x01)<<i
            self.shift_reg   = (self.shift_reg>>1)^(-(self.shift_reg & 1) & self.POLYNOMIAL_32B)
            
        return random_value
        
    def getRandomSeconds(self):
    
        '''
        return a time
        '''
        
        random_value = self.getRandomNumber_16bits()

        random_value = random.randint(0, 65535)
            
        return random_value * self.TIME_UNIT

if __name__ == '__main__':
        
    lr_90 = lfsr_random(90)
    lr_64 = lfsr_random(64)
    
    for i in range(20):
        print(lr_90.getRandomSeconds(), lr_64.getRandomSeconds())
    
    