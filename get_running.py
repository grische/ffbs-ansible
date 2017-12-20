#!/usr/bin/env python3

from subprocess import check_output

def get_vagrant_output(cmd):
    result = []
    output = check_output('vagrant {} --machine-readable'.format(cmd).split())
    for line in output.decode().splitlines():
        line = line.replace(r'\r', '\r')
        line = line.replace(r'\n', '\n')
        line = [x.replace('%!(VAGRANT_COMMA)', ',') for x in line.split(',')]
        if len(line) == 4: # ignore overlong lines
            result.append(line)
    return result

def get_running():
    running = []
    for (_, target, type, data) in get_vagrant_output('status'):
        if type == 'state' and data == 'running':
            running.append(target)
    return running

if __name__ == "__main__":
    print(' '.join(get_running()))
