#!/usr/bin/python
#
# wmctrl.py
#
# developed by Benjamin Hutchins and Ryan Stringham
#
# forked and edited by Jakob Lombacher
#
# an attempt to make linux more usable.
#
# MIT License
#
# https://github.com/benhutchins/wmctrl


import sys
import os
import commands
import re
import argparse

# Customizable variables
window_title_height = 0#21
window_border_width = 1
panel_height = 30
leway_percentage = .05

debug = False

## dual monitor setup

xleft = 1920
yleft = 1080
xright = 1920
yright = 1080
zero_xleft = 0
zero_yleft = 0

zero_xright = xleft
zero_yright = 400
halfpoints = [0, xleft/2, xleft, xleft+xright/2]


def getMonitorConfig():
    """ 
    Returns ordered list of Monitor configuration as dict.
    
    The list is order by the x position from left to right.
    At the moment no support for "upper" Monitors
    
    """
    xrandr_output = commands.getoutput('xrandr').split('\n')
    expr = re.compile('\S+ connected (?P<size_x>\d+)x(?P<size_y>\d+)\+'
                      '(?P<pos_x>\d+)\+(?P<pos_y>\d+).*')
    mon = [m.groupdict() for m in [expr.match(l) for l in xrandr_output]
           if m is not  None]

    for m in mon:
        for k in m.keys():
            m[k] = int(m[k])
    mon.sort(key=lambda x:  x['pos_x']  )
    return mon





def initialize():
    """
    Get window and desktop information
    """
    desk_output = commands.getoutput("wmctrl -d").split("\n")
    desk_list = [line.split()[0] for line in desk_output]

    current =  filter(lambda x: x.split()[1] == "*" , desk_output)[0].split()

    desktop = current[0]
    width =  current[8].split("x")[0]
    height =  current[8].split("x")[1]
    orig_x =  current[7].split(",")[0]
    orig_y =  current[7].split(",")[1]

    # this is unreliable, xdpyinfo often does not know what is focused, we use xdotool now
    #window_id = commands.getoutput("xdpyinfo | grep focus | grep -E -o 0x[0-9a-f]+").strip()
    #window_id = hex(int(window_id, 16))

    current = commands.getoutput("xwininfo -id $(xdotool getactivewindow)").split("\n")
    absoluteX = int(current[3].split(':')[1])
    absoluteY = int(current[4].split(':')[1])
    relativeX = int(current[5].split(':')[1])
    relativeY = int(current[6].split(':')[1])
    cW = int(current[7].split(':')[1])
    cH = int(current[8].split(':')[1])

    # Guess the panel height if we can, this has to assume your window is at the top of screen
    #global panel_height
    #if panel_height == 0 and (absoluteX - relativeX) > 0:
    #    panel_height = absoluteX - relativeX

    # this windows list is no longer needed
#    win_output = commands.getoutput("wmctrl -lG").split("\n")
#    win_list = {}
#
#    for line in win_output:
#        parts = line.split()
#        win_id = hex(int(parts[0], 16))
#        win_list[win_id] = {
#            'x': line[1],
#            'y': line[2],
#            'h': line[3],
#            'w': line[4],
#        }

    #determine maximized state
    current = commands.getoutput("xwininfo -wm -id $(xdotool getactivewindow)")
    cMh = current.find('Maximized Horz') >= 0
    cMv = current.find('Maximized Vert') >= 0
    #Korrekturfaktor, warum auch immer
    absoluteX -= 1
    absoluteY -= 22
    return (desktop,width,height, absoluteX, absoluteY, cW, cH, cMh, cMv)


# calculate these
monitors = getMonitorConfig()
(junk, max_width, max_height, cX, cY, cW, cH, cMh, cMv) = initialize()
max_width = int(max_width)
max_height = int(max_height)

def within_leway(w):
    global cW
    global leway_percentage

    leway = w * leway_percentage

    if cW - leway < w and cW + leway > w:
        return True
    else:
        return False


def is_active_window_maximized():
    return False

    
def maximize():
    unmaximize()

    command = "wmctrl -r :ACTIVE: -b add,maximized_vert,maximized_horz"
    os.system(command)

def maximize_vert():
    unmaximize()

    command = "wmctrl -r :ACTIVE: -b add,maximized_vert"
    os.system(command)

def maximize_horz():
    unmaximize()

    command = "wmctrl -r :ACTIVE: -b add,maximized_horz"
    os.system(command)


def unmaximize():
    command = "wmctrl -r :ACTIVE: -b remove,maximized_vert,maximized_horz,hidden,below"
    os.system(command)


def minimize():
    unmaximize()

    #command = "wmctrl -r :ACTIVE: -b add,below"
    #os.system(command)


def move_active(x,y,w,h):
    unmaximize()

    if debug:
        print x, y, w, h

    # Sanity check, make sure bottom of window does not end up hidden
    if (y+h) > max_height:
        h = max_height - y

    if debug:
        print x, y, w, h


  
    command = "wmctrl -r :ACTIVE: -e 0," + str(int(x)) + "," + str(int(y))+ "," + str(int(w)) + "," + str(int(h))
    os.system(command)

    command = "wmctrl -a :ACTIVE: "
    os.system(command)


def left(shift = False):
    for x in reversed(halfpoints):
        if x < cX-10:
            break

    if shift:
        w = max_width/4
        if within_leway(w):
            w = w * 3
    else:
        if x < xleft:
            w = xleft/2
        else:
            w = xright/2


    h = max_height - window_title_height
    move_active(x, panel_height, w - window_border_width, h)
    maximize_vert()

def right(shift = False):
    for x in halfpoints:
        if x > cX+10:
            break

    if shift:
        w = max_width/4
        x = w * 3

        if within_leway(w):
            w = w * 3
    else:
        if x < xleft:
            w = xleft/2
        else:
            w = xright/2

    h = max_height - window_title_height
    move_active(x, panel_height, w - window_border_width, h)
    maximize_vert()

def get_current_monitor():
    ## determine current monitor
    cMonId = 0
    for i in range(len(monitors)):
        m =monitors[i]
        if cX > m['pos_x']-5 and cX < m['pos_x'] + m['size_x'] and\
           cY > m['pos_y']-5 and cY < m['pos_y'] + m['size_y']:
            cMonId = i
            break;
    m = monitors[cMonId]    
    return cMonId,m

def half(mvright = True):
    """Resize  Window to half, and move it right or left"""

    [cMonId, m] = get_current_monitor()

    if mvright:
        if cX < (m['pos_x'] + m['size_x']/2) or (len(monitors) - 1) == cMonId:
            # move to rigth half
            x = m['pos_x'] + m['size_x']/2
        else:
            m = monitors[cMonId+1]
            x = m['pos_x']
    else:
        if cX >= (m['pos_x'] + m['size_x']/2) or 0 == cMonId:
            # move to left half
            x = m['pos_x']
        else:
            m = monitors[cMonId-1]
            x = m['pos_x'] + m['size_x']/2
        
    y = m['pos_y']
    w = m['size_x']/2
    h = m['size_y'] - window_title_height

    move_active(x, panel_height, w - window_border_width, h)
    maximize_vert()



def up(shift = False):
    if not shift:
        if is_active_window_maximized():
            unmaximize()
        else:
            maximize()

    else:
        w = max_width - window_border_width
        h = max_height/2 - window_title_height - window_border_width
        move_active(0, panel_height, w, h)
 

def down(shift = False):
    if not shift:
        if is_active_window_maximized():
            unmaximize()
        else:
            minimize()

    if shift:
        w = max_width - window_border_width
        h = max_height/2 - window_title_height - window_border_width
        y = max_height/2 + window_title_height + window_border_width
        move_active(0, y, w, h)

def next_monitor():
    """
    Moves Window to next monitor
    """
    [id, m] = get_current_monitor()
    nid = (id+1)%len(monitors)
    nm = monitors[nid]

    xrel = float(cX-m['pos_x'])/m['size_x']
    yrel = float(cY-m['pos_y'])/m['size_y']
    x = xrel * nm['size_x'] + nm['pos_x']
    y = yrel * nm['size_y'] + nm['pos_y']
    w = cW * nm['size_x']/m['size_x']
    h = cH * nm['size_y']/m['size_y']

    move_active(x,y,w,h)

    if cMv:
        maximize_vert()
    if cMh:
        maximize_horz()

#TODO remove
def other_monitor():
    if cX < xleft-5: # on left screen
        xrel = float(cX-zero_xleft)/(xleft)
        yrel = float(cY-zero_yleft)/(yleft)
        x = zero_xright + xrel * xright
        y = zero_yright + yrel * yright
        w = cW * xright/xleft
        h = cH * yright/yleft
        # if next to boarder set on boarder
        if cX-zero_xleft < 5:
            x = zero_xright

    else: #right screen
        xrel = float(cX-zero_xright)/(xright)
        yrel = float(cY-zero_yright)/(yright)
        x = zero_xleft + xrel * xleft
        y = zero_yleft + yrel * yleft
        w = cW * xleft/xright
        h = cH * yleft/yright
        # if next to boarder set on boarder
        if cX-zero_xright < 5:
            x = zero_xleft
            
    move_active(x,y,w,h)

    if cMv:
        maximize_vert()
    if cMh:
        maximize_horz()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='tool to move windows')
    subparsers = parser.add_subparsers()
    sub = subparsers.add_parser('half-left', help='resize window to half to the left')
    sub.set_defaults(func=lambda:half(False))
    sub = subparsers.add_parser('half-right',  help='resize window to half to the right')
    sub.set_defaults(func=lambda:half(True))
    sub = subparsers.add_parser('next', help='moves window to other monitor')
    sub.set_defaults(func=next_monitor)

    
    args = parser.parse_args()
    print args
    args.func()
    exit(0)
    # parser.add_argument('cmd', type=str, nargs=1,
    #                help='command')

    # args = parser.parse_args()
    cmd = sys.argv[1]
    #import ipdb;ipdb.set_trace()
    if cmd == 'left':
        left()

    elif cmd == 'right':
        right()
    
    elif cmd in ('shift-left', 'left-shift'):
        left(True)
    
    elif cmd in ('shift-right', 'right-shift'):
        right(True)
    
    elif cmd in ('top', 'up'):
        up()

    elif cmd in ('shift-up', 'up-shift', 'shift-top', 'top-shift'):
        up(True)

    elif cmd in ('bottom', 'down'):
        down()

    elif cmd in ('shift-down', 'down-shift', 'shift-bottom', 'bottom-shift'):
        down(True)

    elif cmd in ('other'):
        other_monitor()

    elif cmd in ('max'):
        maximize()
    elif cmd in ('unmax'):
        unmaximize()
    elif cmd in ('half-right'):
        half()
    elif cmd in ('half-left'):
        half(False)
    else:
        print "Unknown command passed:", cmd
