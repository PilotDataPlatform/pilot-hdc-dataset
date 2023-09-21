# Dataset Service

[![Python](https://img.shields.io/badge/python-3.9-brightgreen.svg)](https://www.python.org/)

Dataset management service for the Pilot Platform.

## Getting Started

### Prerequisites

This project is using:
1. [Poetry](https://python-poetry.org/docs/#installation) to handle the dependencies.

2. [Redis](https://redis.io/) to handle cache.

3. [postgresql](https://www.postgresql.org/) as database.


1. Install [Docker](https://www.docker.com/get-started/).
2. Start container with project application.

       docker compose up

3. Visit http://127.0.0.1:5064/v1/api-doc for API documentation.

### Installation & Quick Start

1. Clone the project.

       git clone git@github.com:PilotDataPlatform/dataset.git

2. Install dependencies.

       poetry install

4. Add environment variables into `.env`. taking in consideration `.env.schema`


5. Start project dependencies:

        docker-compose up -d redis
        docker-compose up -d postgres


6. Run any initial scripts, migrations or database seeders.

       poetry run alembic upgrade head

7. Run application.

       poetry run python -m dataset


8. Install [Docker](https://www.docker.com/get-started/).


### Startup using Docker

This project can also be started using [Docker](https://www.docker.com/get-started/).

1. To build and start the service within the Docker container run.

       docker compose up

2. Migrations should run automatically on previous step. They can also be manually triggered:

       docker compose run --rm alembic upgrade head

## Contribution

You can contribute the project in following ways:

* Report a bug
* Suggest a feature
* Open a pull request for fixing issues or adding functionality. Please consider
  using [pre-commit](https://pre-commit.com) in this case.
* For general guidelines how to contribute to the project, please take a look at the [contribution guides](CONTRIBUTING.md)

## Acknowledgements
The development of the HealthDataCloud open source software was supported by the EBRAINS research infrastructure, funded from the European Union's Horizon 2020 Framework Programme for Research and Innovation under the Specific Grant Agreement No. 945539 (Human Brain Project SGA3) and H2020 Research and Innovation Action Grant Interactive Computing E-Infrastructure for the Human Brain Project ICEI 800858.
