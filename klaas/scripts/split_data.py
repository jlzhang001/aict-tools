import click
import numpy as np
import logging

from fact.io import read_data
import warnings


@click.command()
@click.argument('input_path', type=click.Path(exists=True, file_okay=True))
@click.argument('output_basename')
@click.option(
    '--fraction', '-f', multiple=True, type=float,
    help='Fraction of events to use for this part'
)
@click.option('--name', '-n', multiple=True, help='name for one dataset')
@click.option('-i', '--inkey', help='HDF5 key for pandas or h5py hdf5 of the input file')
@click.option('--key', '-k', help='Name for the hdf5 group in the output', default='data')
@click.option(
    '--fmt', type=click.Choice(['csv', 'hdf5']), default='hdf5',
    help='The output format',
)
@click.option('-v', '--verbose', help='Verbose log output', type=bool)
def main(input_path, output_basename, fraction, name, inkey, key, fmt, verbose):
    '''
    Split dataset in INPUT_PATH into multiple parts for given fractions and names
    Outputs pandas hdf5 or csv files to OUTPUT_BASENAME_NAME.FORMAT

    Example call: klaas_split_data input.hdf5 output_base -n test -f 0.5 -n train -f 0.5
    '''
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    log = logging.getLogger()
    log.debug("input_path: {}".format(input_path))

    data = read_data(input_path, key=inkey)

    assert len(fraction) == len(name), 'You must give a name for each fraction'

    if sum(fraction) != 1:
        warnings.warn('Fractions do not sum up to 1')

    n_total = len(data)
    log.info('Found a total of {} events'.format(n_total))

    num_events = [int(round(n_total * f)) for f in fraction]

    if sum(num_events) > n_total:
        num_events[-1] -= sum(num_events) - n_total

    for n, part_name in zip(num_events, name):
        print(part_name, ': ', n, sep='')

        all_idx = np.arange(len(data))
        selected = np.random.choice(all_idx, size=n, replace=False)

        log.info(len(selected))

        if fmt == 'hdf5':
            data.iloc[selected].to_hdf(
                output_basename + '_' + part_name + '.hdf5',
                key=key
            )
        elif fmt == 'csv':
            data.iloc[selected].to_csv(output_basename + '_' + part_name + '.csv')

        data = data.iloc[list(set(all_idx) - set(selected))]