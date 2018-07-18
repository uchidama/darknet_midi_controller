#!/usr/bin/env python

from __future__ import print_function
import argparse
import signal
import sys
import time

import rtmidi
import sysv_ipc

KEY = 81

class DetectedObject():

    def __init__(self):
        self.label_name = ""
        self.left = 0
        self.right = 0
        self.top = 0
        self.bottom = 0


def parse_receive_data(receive_str):
    ret_array = []

    arr = receive_str.split(";")
    
    d = None
    i = 0
    num = 5

    screen_w = int(arr[0])
    screen_h = int(arr[1])

    del arr[:2]

    for a in arr:
        if i%num == 0:
            d = DetectedObject()
            d.label_name = a
        elif i%num == 1:
            d.left = int(a)
        elif i%num == 2:
            d.top = int(a)
        elif i%num == 3:
            d.right = int(a)
        elif i%num == 4:
            d.bottom = int(a)
            ret_array.append(d)
        i += 1


    return (ret_array, screen_w, screen_h )




def signal_handler(signal, frame):
    """Handler for Ctrl-C"""
    sys.exit(0)


def midi_in_callback(value, args):
    data = value[0]
    if args['hex']:
        print('[' + ', '.join('0x%02X' % x for x in data) + ']')
    else:
        print(data)

def midi_send(device_id, data_array):
    outport = rtmidi.MidiOut()
    if not device_id < len(outport.get_ports()):
        raise Exception('Device id out of range')
    outport.open_port(device_id)
    '''
    if args['hex']:
        data = [int(x, 16) for x in args['write']]
    else:
        data = [int(x, 0) for x in args['write']]
    '''
    outport.send_message(data_array)
    del outport


def midi_send_server(args):
    # Write command, send data
    if not args['device']:
        raise Exception('No device specified')
    device_id = int(args['device'])
    outport = rtmidi.MidiOut()
    if not device_id < len(outport.get_ports()):
        raise Exception('Device id out of range')
    outport.open_port(device_id)
    if args['hex']:
        data = [int(x, 16) for x in args['write']]
    else:
        data = [int(x, 0) for x in args['write']]
    outport.send_message(data)
    del outport


if __name__ == '__main__':
    # Setup command line parser
    parser = argparse.ArgumentParser(description='MIDI tool')
    parser.add_argument('-l', '--list', action='store_true',
                        help='List connected devices')
    parser.add_argument('-d', '--device', metavar='ID',
                        help='Select device')
    parser.add_argument('-w', '--write', type=str, nargs='+', metavar='DATA',
                        help='Write data')
    parser.add_argument('-r', '--read', action='store_true',
                        help='Read data')
    parser.add_argument('-x', '--hex', action='store_true',
                        help='Show/interprete data as hex')
    print(parser.parse_args())
    args = vars(parser.parse_args())

    try:

        if args['list']:
            # List command, show all connected devices
            print()
            print('Available ports:')
            print()
            print('\tInput:')
            print('\t', 'ID', 'Name', sep='\t')
            for i, name in enumerate(rtmidi.MidiIn().get_ports()):
                print('\t', i, name, sep='\t')
            print()
            print('\tOutput:')
            print('\t', 'ID', 'Name', sep='\t')
            for i, name in enumerate(rtmidi.MidiOut().get_ports()):
                print('\t', i, name, sep='\t')
            print()

        elif args['write']:
            #midi_send_server(args)
            #midi_send( 0, [0x90, 80, 100])
            #midi_send( 1, [128, 80, 100])
            print("KEY:", KEY)
            mq = sysv_ipc.MessageQueue(KEY)
            print("id:", mq.id)
            print("ready to receive messages.")
            #device_id = int(args['device'])

            while True:
                mtext, mtype = mq.receive(type=1)
                print(mtext.decode("utf-8"))
                ret, screen_w, screen_h = parse_receive_data(mtext.decode("utf-8"))
                print("SCREEN_WIDTH:", screen_w)
                print("SCREEN_HEIGHT:", screen_h)

                MIDI_ID = 1
                CC_NO = 20

                for r in ret:
                    print(r.label_name)
                    center_x = (r.left + r.right)/2
                    center_y = (r.top + r.bottom)/2
                    #center_x = r.left
                    #center_y = r.top

                    if r.label_name == "cell phone":
                        print("cell phone find")
                        print("center_x:", center_x)
                        print("center_y:", center_y)
                        MIDI_NOTE = int(40.0 + round(48.0*(center_x/screen_w)))
                        CC_DATA = int(round(127*(1.0-float(center_y)/float(screen_h))))
                        print("MIDI_NOTE:", MIDI_NOTE)
                        print("CC_DATA:", CC_DATA)

                        midi_send( MIDI_ID, [0x90, MIDI_NOTE, MIDI_NOTE])
                        # CC
                        if CC_DATA >= 0:
                            midi_send( MIDI_ID, [185, CC_NO, CC_DATA])


            # Write command, send data
            '''
            if not args['device']:
                raise Exception('No device specified')
            device_id = int(args['device'])
            outport = rtmidi.MidiOut()
            if not device_id < len(outport.get_ports()):
                raise Exception('Device id out of range')
            outport.open_port(device_id)
            if args['hex']:
                data = [int(x, 16) for x in args['write']]
            else:
                data = [int(x, 0) for x in args['write']]
            outport.send_message(data)
            del outport
            '''

        elif args['read']:
            # Read command, receive data until Ctrl-C is pressed
            signal.signal(signal.SIGINT, signal_handler)
            if not args['device']:
                raise Exception('No device specified')
            device_id = int(args['device'])
            inport = rtmidi.MidiIn()
            if not device_id < len(inport.get_ports()):
                raise Exception('Device id out of range')
            inport.open_port(device_id)
            inport.set_callback(midi_in_callback, args)
            inport.ignore_types(False, False, False)
            while True:
                time.sleep(1)

    except Exception as e:
        print('Error:', e)
