#!/usr/bin/env python

"""vic.py: calculate impedance from S-parameters"""

from sys import stderr, exit as sys_exit
from skrf.io.touchstone import Touchstone
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from csv import writer as csv_writer
from enum import Enum

class MeasurementType(Enum):
    s11_shunt         = 's11_shunt'
    s21_series        = 's21_series'
    s21_shunt_through = 's21_shunt_through'

    def __str__(self):
        return self.value

def s11_shunt_impedance(z0, s11):
    return (z0 * (1 + s11)) / (1 - s11)

def s21_series_impedance(z0, s21):
    return (2 * (z0 - s21)) / (s21)

def s21_shunt_through_impedance(z0, s21):
    return (z0 * s21) / (2 * (1 - s21))

if __name__ == '__main__':
    argument_parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    argument_parser.add_argument('--type', '-t', type=MeasurementType, choices=list(MeasurementType), default=MeasurementType.s11_shunt)
    argument_parser.add_argument('--z0', '-z', type=complex, help='system impedance')
    argument_parser.add_argument('--output', '-o', type=str, help='output file name', default='impedace.csv')
    argument_parser.add_argument('filename', type=str, help='touchstone S-parameters file name')
    args = argument_parser.parse_args()
    try:
        touchstone = Touchstone(args.filename)
    except Exception as e:
        print(f'Cannot open S-parameters file: {e}', file=stderr)
        sys_exit(1)
    print(f'Loaded {args.filename}')
    if args.z0 is not None:
        z0 = args.z0
        print('Using command line supplied system impedance')
    else:
        try:
            _, z0 = touchstone.get_gamma_z0()
            print('Using touchstone system impedance')
        except:
            print('Unknown system impedance, use -z', file=stderr)
            sys_exit(1)
    print(f'System impedance (z0): {z0}')
    print(f'Measurement type: {args.type}')
    frequencies, s_arrays = touchstone.get_sparameter_arrays()
    if args.type == MeasurementType.s11_shunt:
        impedances = s11_shunt_impedance(z0, s_arrays[:, 0, 0])
    elif args.type == MeasurementType.s21_series:
        impedances = s21_series_impedance(z0, s_arrays[:, 1, 0])
    elif args.type == MeasurementType.s21_shunt_through:
        impedances = s21_shunt_through_impedance(z0, s_arrays[:, 1, 0])
    else:
        print(f'Unknown measurement type: {args.type}', file=stderr)
    with open(args.output, 'w') as output_file:
        output_writer = csv_writer(output_file)
        for frequency, impedance in zip(frequencies, impedances):
            output_writer.writerow([frequency, impedance])
