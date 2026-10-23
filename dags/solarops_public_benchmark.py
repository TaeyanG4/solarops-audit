"""Airflow DAGs for the isolated public-data benchmark."""

from solarops_factory import make_public_benchmark

serial = make_public_benchmark(1)
parallel = make_public_benchmark(2)
