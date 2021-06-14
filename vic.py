#!/usr/bin/env python

"""vic.py: calculate impedance from S-parameters"""

from sys import stderr, exit as sys_exit
from skrf.io.touchstone import Touchstone
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from csv import writer as csv_writer
from enum import Enum
from matplotlib import pyplot as plt, ticker
from numpy import real as np_real, imag as np_imag, absolute as np_abs, log10 as np_log10


class MeasurementType(Enum):
    s11_shunt = 's11_shunt'
    s21_series = 's21_series'
    s21_shunt_through = 's21_shunt_through'

    def __str__(self):
        return self.value


def s11_shunt_impedance(z0, s11):
    return z0 * ((1 + s11) / (1 - s11))


def s21_series_impedance(z0, s21):
    return z0 * (2 * (1 - s21)) / (s21)


def s21_shunt_through_impedance(z0, s21):
    return (z0 * s21) / (2 * (1 - s21))


if __name__ == '__main__':
    argument_parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    argument_parser.add_argument('--type', '-t', type=MeasurementType, choices=list(MeasurementType),
                                 default=MeasurementType.s11_shunt)
    argument_parser.add_argument('--z0', '-z', type=complex, help='system impedance')
    argument_parser.add_argument('--output', '-o', type=str, help='output file name', default='impedance.csv')
    argument_parser.add_argument('--plot', '-p', action='store_true', help='show impedance plot')
    argument_parser.add_argument('--xkcd', '-x', action='store_true', help='turn on xkcd sketch-style drawing mode')
    argument_parser.add_argument('--refs', '-r', action='store_true',
                                 help='turn on impedance range references (for common mode chokes)')
    argument_parser.add_argument('--abs', '-a', action='store_true', help='plot absolute reactance values')
    argument_parser.add_argument('--bands', '-b', action='store_true', help='turn on HF band ranges')
    argument_parser.add_argument('--title', type=str, help='Plot title')
    argument_parser.add_argument('--width', type=float, help='Plot width (inches)', default=15)
    argument_parser.add_argument('--height', type=float, help='Plot height (inches)', default=10)
    argument_parser.add_argument('--isolation', '-i', action='store_true', help='plot isolation (insertion loss)')
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
        sys_exit(1)
    with open(args.output, 'w') as output_file:
        print(f'Storing impedance data to {args.output}')
        output_writer = csv_writer(output_file)
        for frequency, impedance in zip(frequencies, impedances):
            output_writer.writerow([frequency, impedance])
    if args.plot:
        if args.xkcd:
            plt.xkcd(0.35, 75, 150)
        plt.figure(figsize=(args.width, args.height))
        ax = plt.axes(xlabel='Frequency, Hz', ylabel='Impedance, Ohm', title=args.title or 'Impedance vs Frequency')
        ax.xaxis.grid(linewidth=0.5)
        ax.yaxis.grid(linewidth=0.5)
        ax.xaxis.set_major_formatter(ticker.EngFormatter())
        ax.yaxis.set_major_formatter(ticker.EngFormatter())
        plt.plot(frequencies, np_real(impedances), 'C1', label='R')
        if args.abs:
            plt.plot(frequencies, np_abs(np_imag(impedances)), 'C2', label='|X|')
        else:
            plt.plot(frequencies, np_imag(impedances), 'C2', label='X')
        plt.plot(frequencies, np_abs(impedances), 'C3', label='|Z|')
        if args.refs:
            plt.axhspan(0, 500, color='red', alpha=0.25)
            plt.axhspan(500, 1000, color='orange', alpha=0.25)
            plt.axhspan(1000, 2000, color='yellow', alpha=0.25)
            plt.axhspan(2000, 4000, color='yellowgreen', alpha=0.25)
            plt.axhspan(4000, 8000, color='green', alpha=0.25)
        if args.bands:
            bands = [
                ('160m', 1.81e6, 2e6),
                ('80m', 3.5e06, 3.8e6),
                ('40m', 7e6, 7.2e6),
                ('20m', 14e6, 14.35e6),
                ('15m', 21e6, 21.45e6),
                ('10m', 28e6, 29.7e6),
            ]
            for band_name, freq_min, freq_max in bands:
                plt.axvspan(freq_min, freq_max, color='grey', alpha=0.5)
                y_min, y_max = ax.get_ylim()
                y_center = (y_max - y_min) / 2.0
                plt.text(freq_min, y_center, band_name, rotation=90, va='center', ha='right')
        plt.legend()
        if args.isolation:
            isolation = -20 * np_log10(np_abs((2 * z0) / ((2 * z0) + impedances)))
            ax2 = ax.twinx()
            ax2.set_ylabel('Isolation, dB')
            ax2.set_ylim(0, 50)
            ax2.plot(frequencies, isolation, color='black', label='Isolation')
        plt.show()
