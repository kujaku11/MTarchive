# package file
import os
from pathlib import Path

CSV_LIST = ['.\auxiliary.csv',
			'.\battery.csv',
			'.\channel.csv',
			'.\citation.csv',
			'.\copyright.csv',
			'.\datalogger.csv',
			'.\data_quality.csv',
			'.\declination.csv',
			'.\diagnostic.csv',
			'.\electric.csv',
			'.\electrode.csv',
			'.\filter.csv',
			'.\instrument.csv',
			'.\location.csv',
			'.\magnetic.csv',
			'.\metadata_standards.csv',
			'.\person.csv',
			'.\provenance.csv',
			'.\run.csv',
			'.\software.csv',
			'.\station.csv',
			'.\survey.csv',
			'.\timing_system.csv']

CSV_PATH = Path(os.path.dirname(os.path.abspath(__file__)))