import click
from sklearn.externals import joblib
import logging
import h5py
from tqdm import tqdm

from ..apply import predict
from ..feature_generation import feature_generation
from ..features import has_source_dependent_columns
from ..io import append_to_h5py, read_telescope_data_chunked, check_existing_column
from ..configuration import KlaasConfig


@click.command()
@click.argument('configuration_path', type=click.Path(exists=True, dir_okay=False))
@click.argument('data_path', type=click.Path(exists=True, dir_okay=False))
@click.argument('model_path', type=click.Path(exists=True, dir_okay=False))
@click.option('-v', '--verbose', help='Verbose log output', is_flag=True)
@click.option(
    '-N', '--chunksize', type=int,
    help='If given, only process the given number of events at once'
)
@click.option('-y', '--yes', help='Do not prompt for overwrites', is_flag=True)
def main(configuration_path, data_path, model_path, chunksize, yes, verbose):
    '''
    Apply loaded model to data.

    CONFIGURATION_PATH: Path to the config yaml file.
    DATA_PATH: path to the FACT data.
    MODEL_PATH: Path to the pickled model.

    The program adds the following columns to the inputfile:
        <class_name>_prediction: the output of model.predict_proba for the
        class name given in the config file.

    If the class name is not given in the config file, the default value of "gamma"
    will be used.
    '''
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    log = logging.getLogger()

    config = KlaasConfig(configuration_path)

    if has_source_dependent_columns(config.columns_to_read):
        raise click.ClickException(
            'Using source dependent features in the model is not supported'
        )

    check_existing_column(data_path, config, yes)

    log.debug('Loading model')
    model = joblib.load(model_path)
    log.debug('Loaded model')

    df_generator = read_telescope_data_chunked(data_path, config, chunksize, config.columns_to_read)

    log.info('Predicting on data...')
    prediction_column_name = config.class_name + '_prediction'
    for df_data, start, end in tqdm(df_generator):

        if config.feature_generation_config:
            feature_generation(df_data, config.feature_generation_config, inplace=True)

        signal_prediction = predict(df_data, model, config.training_config.training_variables)

        with h5py.File(data_path, 'r+') as f:
            append_to_h5py(f, signal_prediction, config.telescope_events_key, prediction_column_name)




if __name__ == '__main__':
    main()
