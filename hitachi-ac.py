import sys
# reference
# https://perhof.wordpress.com/2015/03/29/reverse-engineering-hitachi-air-conditioner-infrared-remote-commands/
# start: pulse: 3200 us, pause: 1700 us
# val 0: Pulse:  450 us, pause:  400 us
# val 1: Pulse:  450 us, pause: 1180 us
# total 37 bytes, paires of byte and inverted one

# mode: 0:stop 3:cool, 5:dehumidify
# temp: 1:auto 16-32 (10-32 for dehumidify)
# fanspeed: 1-4, 5:auto (2:bifu)
def genparams(mode, temp=28, fanspeed=1, humidity=0):
    # RAS-22FNX samples
    #                                           op1  op2  temp off/on timer         famo onof
    # start-dehum-28-bifu    01100040BFFF00CC33 946B 718E 708F 00FF00FF00FF00FF00FF 25DA D12E 00FF00FF
    # stop-dehum-28-bifu     01100040BFFF00CC33 926D 13EC 708F 00FF00FF00FF00FF00FF 23DC C13E 00FF00FF
    # start-cool-28-bifu     01100040BFFF00CC33 926D 13EC 708F 00FF00FF00FF00FF00FF 23DC D12E 00FF00FF
    # stop-cool-28-bifu      01100040BFFF00CC33 926D 13EC 708F 00FF00FF00FF00FF00FF 23DC C13E 00FF00FF
    # sleep-1h-dehum-28-bifu 01100040BFFF00CC33 926D 31CE 708F 3CC300FF00FF00FF40BF 25DA D12E 00FF00FF
    # sleep-2h-dehum-28-bifu 01100040BFFF00CC33 926D 31CE 708F 788700FF00FF00FF40BF 25DA D12E 00FF00FF
    # sleep-3h-dehum-28-bifu 01100040BFFF00CC33 926D 31CE 708F B44B00FF00FF00FF40BF 25DA D12E 00FF00FF
    # sleep-7h-dehum-28-bifu 01100040BFFF00CC33 926D 31CE 708F A45B01FE00FF00FF40BF 25DA D12E 00FF00FF
    # sleep-0h-dehum-28-bifu 01100040BFFF00CC33 926D 31CE 708F 00FF00FF00FF00FF00FF 25DA D12E 00FF00FF
    # cancel-dehum-28-bifu   01100040BFFF00CC33 926D 24DB 708F 00FF00FF00FF00FF00FF 25DA D12E 00FF00FF
    # autodir-dehum-28-bifu  01100040BFFF00CC33 926D 817E 708F 00FF00FF00FF00FF00FF 25DA D12E 00FF00FF
    # temp-27-dehum-28-bifu  01100040BFFF00CC33 926D 43BC 6C93 00FF00FF00FF00FF00FF 25DA D12E 00FF00FF
    # temp-29-dehum-28-bifu  01100040BFFF00CC33 926D 44BB 748B 00FF00FF00FF00FF00FF 25DA D12E 00FF00FF
    # fanspd-dehum-28-bifu   01100040BFFF00CC33 926D 42BD 708F 00FF00FF00FF00FF00FF 25DA D12E 00FF00FF
    # chg1cool-dehum-28-bifu 01100040BFFF00CC33 926D 41BE 708F 00FF00FF00FF00FF00FF 23DC D12E 00FF00FF
    # chg2flow-cool-28-bifu  01100040BFFF00CC33 926D 41BE 708F 00FF00FF00FF00FF00FF 21DE D12E 00FF00FF
    # chg3auto-flow-xx-bifu  01100040BFFF00CC33 926D 41BE 04FB 00FF00FF00FF00FF00FF 57A8 D12E 00FF00FF
    # chg4heat-auto-23-auto  01100040BFFF00CC33 926D 41BE 5CA3 00FF00FF00FF00FF00FF 56A9 D12E 00FF00FF
    # chg5dehum-heat-23-auto 01100040BFFF00CC33 926D 41BE 708F 00FF00FF00FF00FF00FF 25DA D12E 00FF00FF
    #
    # op1:  94 dehumidify
    # op1:  92 others
    # op2:  13 cool/stop
    # op2:  24 cancel
    # op2:  31 sleep
    # op2:  41 change mode
    # op2:  42 fan speed
    # op2:  43 temp down
    # op2:  44 temp up
    # op2:  71 dehumidity
    # op2:  81 auto fandir
    # offtm:lo hi
    # ontm: lo hi
    # timer:10 00001000 off?
    # timer:20 00000100 on?
    # timer:40 00000010 sleep
    # mode: x5 1010xxxx 1:airflow,3:cool,5:dehum,6:heat,7:auto
    # fan:  2x xxxx0100 1:silent,2:low/bifu,3:med,4:hi,5(auto)
    # on:   D1 10001011
    # off:  C1 10000011
    #
    # 1-5
    params = '01100040BF'
    # 6-7
    params += 'FF00'
    # 8-9
    params += 'CC33'
    # 10-11
    if mode == 5: # dehumidify
        params += '946B'
    else: # others
        params += '926D'
    # 12-13: operation
    if mode == 0 or mode == 3: # stop/cool
        params += '13EC'
    elif mode == 5: # dehumidify
        params += '718E'
    else:
        print('unknown mode')
        params += '----'
    # 14-15: temperature (1:auto)
    params += '{:02X}{:02X}'.format(temp<<2, (temp<<2)^0xff)
    # 16-17
    params += '00FF'
    # 18-25: timers, which differs from sleep timer?
    offmin = 0 # 11 bits
    offact = 0 # 1 bit
    onmin  = 0 # 11 bits
    onact  = 0 # 1 bit
    params += '{:02X}{:02X}'.format((offmin&0x0f)<<4, ((offmin&0x0f)<<4)^0xff)
    params += '{:02X}{:02X}'.format(offmin>>4, (offmin>>4)^0xff)
    params += '{:02X}{:02X}'.format(onmin&0xff, (onmin&0xff)^0xff)
    params += '{:02X}{:02X}'.format((onact<<5)+(offact<<4)+(onmin>>8), ((onact<<5)+(offact<<4)+(onmin>>8))^0xff)
    # 26-27: fanspeed: 1-4,5(auto)
    # mode: 3(cool),4(drycool),5(dehumidify),6(heat),7(auto),9(autodehumidify),10(quicklaundry),12(condensation ctrl)
    mode2 = 3 if mode == 0 else mode
    params += '{:02X}{:02X}'.format((fanspeed<<4)+mode2, ((fanspeed<<4)+mode2)^0xff)
    # 28-29: on/off
    onoff = 0 if mode == 0 else 1
    # params += '{:02X}{:02X}'.format(0xe0+(onoff<<4)+1, (0xe0+(onoff<<4)+1)^0xff)
    params += '{:02X}{:02X}'.format(0xc0+(onoff<<4)+1, (0xc0+(onoff<<4)+1)^0xff)
    # 30-31: powerfulop: 2 bits
    powerfulop = 0
    params += '{:02X}{:02X}'.format(powerfulop<<4, (powerfulop<<4)^0xff)
    # 32-33
    params += '00FF'
    # 34-35
    # params += '00FF'
    # 36-37: humidity: 3(40%)-9(70%)
    # params += '{:02X}{:02X}'.format((humidity<<4)+0x0f, ((humidity<<4)+0x0f)^0xff)

    return(params)

def regressiontest():
    testcases = [
        {'mode':0, 'temp':28, 'fan':1, 'code':'01100040BFFF00CC33926D13EC708F00FF00FF00FF00FF00FF13ECC13E00FF00FF'},
        {'mode':3, 'temp':28, 'fan':1, 'code':'01100040BFFF00CC33926D13EC708F00FF00FF00FF00FF00FF13ECD12E00FF00FF'},
        {'mode':5, 'temp':28, 'fan':1, 'code':'01100040BFFF00CC33946B718E708F00FF00FF00FF00FF00FF15EAD12E00FF00FF'}
        ]
    for testcase in testcases:
        ret = genparams(testcase['mode'], testcase['temp'], testcase['fan'])
        expected = testcase['code']
        if ret != expected:
            print('test error:')
            print(testcase)
            print(expected)
            print(ret)

def main():
    regressiontest()
    ret = genparams(5)
    bto_ir_cmd_hitachiac = '0BCC00' # hitachi ac
    print(bto_ir_cmd_hitachiac + ret)

if __name__ == '__main__':
    main()
