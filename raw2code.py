import sys
import re

# raw data from USB UIRT is expected
# $ mode2 --driver=uirt2_raw --device=/dev/ttyUSB0
# start: pulse 3350, space 1600
# val 0: pulse  450, space  350
# val 1: pulse  450, space 1150-1200
# pulse threshold: 2000
# space threshold:  800
def raw2conv(lines, debug=False):
    temp = ''
    code = ''
    for i in range(int(len(lines)/2)):
        m = re.match(r'pulse (\d+)', lines[i*2])
        if m:
            pulse = int(m.group(1))
            m = re.match(r'space (\d+)', lines[i*2+1])
            if m:
                space = int(m.group(1))
                if pulse >= 2000: # start
                    pass
                elif space >= 800:
                    temp = '1'+temp
                else:
                    temp = '0'+temp

                if len(temp) == 8:
                    if debug:
                        print('{:02X}'.format(int(temp, 2)), end='')
                    code += '{:02X}'.format(int(temp, 2))
                    temp = ''
    return(code)

def main():
    with open(sys.argv[1], 'r') as f:
        ret = raw2conv(f.readlines())
        print(ret)

if __name__ == '__main__':
    main()
