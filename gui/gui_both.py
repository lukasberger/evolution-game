import os
import sys
import subprocess


filedir = os.path.dirname(os.path.realpath(__file__))
stdin = sys.stdin.read().encode("utf8")

p1 = subprocess.Popen("python3 {}/gui_dealer.py".format(filedir), shell=True, stdin=subprocess.PIPE)
p1.stdin.write(stdin)

p2 = subprocess.Popen("python3 {}/gui_player.py".format(filedir), shell=True, stdin=subprocess.PIPE)
p2.stdin.write(stdin)
